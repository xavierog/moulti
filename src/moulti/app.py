import os
import asyncio
import selectors
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterator
from socket import socket as Socket
from time import time_ns, localtime, strftime
from threading import get_ident
from textual import work
from textual.app import App, ComposeResult
from textual.dom import BadIdentifier
from textual.widgets import Footer, Label
from textual.worker import get_current_worker, NoActiveWorker
from .protocol import PRINTABLE_MOULTI_SOCKET, clean_socket
from .protocol import moulti_listen, get_unix_credentials, send_json_message
from .protocol import MoultiConnectionClosedException, MoultiProtocolException, Message, FDs
from .protocol import MoultiTLVReader, data_to_message, getraddr
from .widgets.tui import MoultiWidgets
from .widgets.vertscroll import VertScroll
from .widgets.abstractstep.tui import AbstractStep
from .widgets.step.tui import Step

def timestamp() -> str:
	timestamp_ns = time_ns()
	timestamp_s = timestamp_ns//10**9
	ns = timestamp_ns - timestamp_s * 10**9
	ms = ns // 10**6
	timestr = strftime('%FT%T', localtime(timestamp_s))
	timestr = f'{timestr}.{ms:03d} '
	return timestr

class MoultiMessageException(Exception):
	pass

class Moulti(App):
	"""
	moulti is a Terminal User Interface (TUI) meant to display multiple outputs.
	It is visually similar to https://github.com/dankilman/multiplex but unlike
	it, moulti does not do anything until instructed to.
	"""
	BINDINGS = [
		("c", "toggle_debug", "Toggle console"),
		("d", "toggle_dark", "Toggle dark mode"),
		("x", "expand_all", "Expand all"),
		("o", "collapse_all", "Collapse all"),
		("q", "quit", "Quit Moulti"),
	]

	def __init__(self, command: list[str]|None = None):
		self.init_security()
		self.init_widgets()
		self.init_debug()
		self.init_command = command
		super().__init__()

	def init_security(self) -> None:
		def ids_from_env(env_var_name: str) -> list[int]:
			try:
				return [int(xid) for xid in os.environ.get(env_var_name, '').split(',')]
			except Exception:
				return []

		# By default, allow only the current uid to connect to Moulti:
		self.allowed_uids = [os.getuid()]
		self.allowed_gids = []

		# Make this behaviour configurable through environment variables:
		self.allowed_uids.extend(ids_from_env('MOULTI_ALLOWED_UID'))
		self.allowed_gids.extend(ids_from_env('MOULTI_ALLOWED_GID'))

	def init_widgets(self) -> None:
		self.title_label = Label('Moulti', id='header')
		self.steps_container = VertScroll(id='steps_container')
		self.footer = Footer()

	def init_threads(self) -> None:
		try:
			max_pass = max(1, int(os.environ['MOULTI_PASS_CONCURRENCY']))
		except (KeyError, ValueError):
			max_pass = 20
		default_threads = 2 # network_loop() + exec()
		threads_per_pass = 2 # Each "moulti pass" command spawns 2 threads -- cf handle_pass_command()
		thread_count = default_threads + threads_per_pass * max_pass
		moulti_executor = ThreadPoolExecutor(max_workers=thread_count, thread_name_prefix='moulti')
		asyncio.get_running_loop().set_default_executor(moulti_executor)
		self.logdebug(f'allow up to {thread_count} threads for up to {max_pass} concurrent "moulti pass" commands')

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""
		yield self.title_label
		yield self.steps_container
		yield self.footer
		yield self.debug_step

	def on_ready(self) -> None:
		self.init_threads()
		widget_list = ' '.join(MoultiWidgets.registry().keys())
		self.logdebug(f'known widgets: {widget_list}')
		self.network_loop()

	def network_loop_is_ready(self) -> None:
		if self.init_command is not None:
			self.exec(self.init_command)

	@work(thread=True)
	def exec(self, command: list[str]) -> None:
		import subprocess # pylint: disable=import-outside-toplevel
		try:
			environment = os.environ.copy()
			environment['MOULTI_RUN'] = 'moulti'
			environment['MOULTI_SOCKET_PATH'] = PRINTABLE_MOULTI_SOCKET
			self.logdebug(f'exec: about to run {command}')
			completed = subprocess.run(command, env=environment, stdin=subprocess.DEVNULL, check=False)
			self.logdebug(f'exec: {command} exited with return code {completed.returncode}')
		except Exception as exc:
			self.logdebug(f'exec: error running {command}: {exc}')

	def all_steps(self) -> Iterator[AbstractStep]:
		return self.query('#steps_container AbstractStep').results(AbstractStep)

	def init_debug(self) -> None:
		self.debug_step = Step('__moulti_debug', title='Console', classes='debug', min_height=5, max_height=15)
		self.debug_step.styles.display = 'none'
		self.debug_step.collapsible.collapsed = False

	def logdebug(self, line: str) -> None:
		line = timestamp() + line
		if self._thread_id == get_ident():
			self.debug_step.append(line)
		else:
			try:
				worker = get_current_worker()
			except NoActiveWorker:
				worker = None
			if worker and not worker.is_cancelled:
				self.call_from_thread(self.debug_step.append, line)

	def action_toggle_debug(self) -> None:
		"""Toggle the debug console."""
		if self.debug_step.styles.display == 'none':
			self.debug_step.collapsible.collapsed = False
			self.debug_step.styles.display = 'block'
		else:
			self.debug_step.styles.display = 'none'

	def action_toggle_dark(self) -> None:
		"""Toggle dark mode."""
		self.dark = not self.dark

	def action_expand_all(self) -> None:
		"""Expand all steps."""
		for step in self.all_steps():
			step.collapsible.collapsed = False

	def action_collapse_all(self) -> None:
		"""Collapse all steps."""
		for step in self.all_steps():
			step.collapsible.collapsed = True

	def reply(self, connection: Socket, raddr: str, message: dict[str, Any], **kwargs: Any) -> None:
		try:
			# If the original message bears a message id, use it to send a
			# smaller reply. Otherwise, send the original message back with
			# extra data.
			if msgid := message.get('msgid'):
				message = {'msgid': msgid, **kwargs}
			else:
				message = {**message, **kwargs}
			self.logdebug(f'{raddr}: <= message={message}')
			send_json_message(connection, message)
		except Exception as exc:
			self.logdebug(f'{raddr}: reply: kwargs={kwargs}: {exc}')

	def step_from_message(self, message: Message) -> None | AbstractStep:
		try:
			return self.steps_container.query_one('#step_' + str(message['id']), AbstractStep)
		except Exception:
			return None

	def handle_message(self, connection: Socket, raddr: str, message: Message, file_descriptors: FDs) -> None:
		command = str(message.get('command'))
		# "moulti pass" is a special case that actually means "moulti step pass":
		if command == 'pass':
			command = 'step'
			message['command'], message['action'] = command, message['command']
		# Analyse the message to determine what to call or what error to return:
		finally_reply = True
		call: Any = ()
		error = None
		try:
			command_class = MoultiWidgets.command_to_class(command)
			if command_class is not None:
				step = self.step_from_message(message)
				action = str(message.get('action'))
				# add/update/delete actions are considered common/standard and are thus handled here:
				if action == 'add':
					if step:
						raise MoultiMessageException(f'id {message.get("id")} already in use')
					if 'id' not in message:
						raise MoultiMessageException('missing id')
					call = (self.steps_container.mount, command_class(**message))
				else:
					# All other actions require an existing step:
					if not step:
						raise MoultiMessageException(f'unknown id: {message.get("id")}')
					if action == 'update':
						call = (step.update_properties, message)
					elif action == 'delete':
						if step.prevent_deletion:
							err = 'cannot proceed with deletion as '
							err += f'{step.prevent_deletion} ongoing operations prevent it'
							raise MoultiMessageException(err)
						call = (step.remove,)
					else:
						# For actions other than add/update/delete, the widget class is expected to provide a
						# "cli_action_{action}" method:
						method_name = f'cli_action_{action.replace("-", "_")}'
						method = getattr(step, method_name, False)
						if not callable(method):
							raise MoultiMessageException('unknown action {action}')
						# Provide the method with helper functions that abstract away app/network-specific stuff:
						def reply(**kwargs: Any) -> None:
							self.reply(connection, raddr, message, **kwargs)
						def debug(line: str) -> None:
							self.logdebug(f'{raddr}: {line}')
						helpers = {'reply': reply, 'debug': debug, 'file_descriptors': file_descriptors}
						# The method is expected to return a tuple (callable + arguments):
						call = method(message, helpers)
						# An empty tuple means the method chose to handle everything, reply included:
						if not call:
							finally_reply = False
			elif command == 'set':
				if 'title' in message:
					call = (self.title_label.update, str(message['title']))
			elif command == 'ping':
				call = ()
			else:
				raise MoultiMessageException(f'unknown command {command}')
			# At this stage, the analysis is complete; perform the required action and reply accordingly:
			if call:
				self.call_from_thread(*call)
		except (BadIdentifier, MoultiMessageException) as exc:
			# If we catch an exception, then we systematically assume we should handle the reply:
			finally_reply = True
			error = str(exc)
		finally:
			if finally_reply:
				self.reply(connection, raddr, message, done=error is None, error=error)

	def check_unix_credentials(self, socket: Socket) -> tuple[bool, int, int]:
		_, uid, gid = get_unix_credentials(socket)
		allowed = uid in self.allowed_uids or gid in self.allowed_gids
		return allowed, uid, gid

	@work(thread=True)
	async def network_loop(self) -> None:
		current_worker = get_current_worker()

		def read(tlv_reader: MoultiTLVReader) -> None:
			raddr = tlv_reader.raddr
			try:
				try:
					# Read whatever there is to read; if a complete TLV message is received, calls got_tlv, which calls
					# handle_message, which calls reply().
					tlv_reader.read()
				except (MoultiProtocolException, MoultiConnectionClosedException, ConnectionResetError) as exc:
					server_selector.unregister(tlv_reader.socket)
					tlv_reader.socket.close()
					self.logdebug(f'{raddr}: read: closed connection; cause: {exc}')
					return
			except Exception as exc:
				self.logdebug(f'{raddr}: read: {exc}')

		def got_tlv(socket: Socket, raddr: str, data_type: str, data: bytes, file_descriptors: FDs) -> None:
			if data_type == 'JSON':
				message = data_to_message(data)
				self.logdebug(f'{raddr}: => {message=} {file_descriptors=}')
				self.handle_message(socket, raddr, message, file_descriptors)
			else:
				raise MoultiProtocolException(f'cannot handle {data_type} {len(data)}-byte message')

		def accept(socket: Socket) -> None:
			raddr = None
			try:
				connection, _ = socket.accept()
				raddr = getraddr(connection)
				self.logdebug(f'{raddr}: accept: accepted new connection')
				# Check Unix credentials (uid/gid) if and only if Moulti listens on an abstract socket.
				# Regular sockets are protected by file permissions.
				if server_socket_is_abstract:
					allowed, uid, gid = self.check_unix_credentials(connection)
					if not allowed:
						connection.close()
						self.logdebug(f'{raddr}: accept: closed connection: invalid Unix credentials {uid}:{gid}')
						return
				connection.setblocking(False)
				tlv_reader = MoultiTLVReader(connection, raddr, got_tlv, self.logdebug)
				server_selector.register(connection, selectors.EVENT_READ, tlv_reader)
			except Exception as exc:
				self.logdebug(f'{raddr}: accept: {exc}')

		try:
			server_socket, server_socket_is_abstract = moulti_listen()
		except Exception as exc:
			# A Moulti instance is useless if it cannot listen:
			self.exit(f'Fatal: {exc}')
			return
		socket_type = "abstract socket" if server_socket_is_abstract else "socket"
		self.logdebug(f'listening on {socket_type} {PRINTABLE_MOULTI_SOCKET}')

		try:
			server_selector = selectors.DefaultSelector()
			server_selector.register(server_socket, selectors.EVENT_READ, accept)

			self.network_loop_is_ready()
			while not current_worker.is_cancelled:
				events = server_selector.select(1)
				for key, _ in events:
					if isinstance(key.data, MoultiTLVReader):
						read(key.data)
					elif callable(key.data):
						key.data(key.fileobj)
		except Exception as exc:
			self.logdebug(f'network loop: {exc}')
		finally:
			clean_socket(PRINTABLE_MOULTI_SOCKET)

	DEFAULT_CSS = """
	/* Styles inherited by all widgets: */
	$scrollbar_background: #b2b2b2;
	$scrollbar_inactive_bar: #686868;
	$scrollbar_active_bar: $accent-darken-1;
	Widget {
		/* By default, in dark mode, scrollbars are not rendered clearly; enforce their colours: */
		scrollbar-background: $scrollbar_background;
		scrollbar-background-hover: $scrollbar_background;
		scrollbar-background-active: $scrollbar_background;
		scrollbar-color: $scrollbar_inactive_bar;
		scrollbar-color-active: $scrollbar_active_bar;
		scrollbar-color-hover: $scrollbar_active_bar;
	}

	/* One-line title at the top of the screen: */
	#header {
		text-align: center;
		/* For the title to appear centered, the widget must occupy all available width: */
		width: 100%;
		background: $accent;
		color: auto;
	}

	/* Leave a thin space between steps and their container's vertical scrollbar: */
	#steps_container.vertical_scrollbar_visible > Widget {
		margin-right: 1;
	}
	"""

	# Allow end users to redefine Moulti's look and feel through an optional
	# custom CSS set through an environment variable:
	CSS_PATH = os.environ.get('MOULTI_CUSTOM_CSS')

def main(command: list[str]|None = None) -> None:
	reply = Moulti(command=command).run()
	if reply is not None:
		print(reply)

if __name__ == '__main__':
	main()

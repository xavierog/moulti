import os
import selectors
from typing import Any, cast, Iterator
from socket import socket as Socket
from time import time_ns, localtime, strftime
from queue import Queue
from threading import get_ident
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Label
from textual.worker import get_current_worker, NoActiveWorker
from .protocol import PRINTABLE_MOULTI_SOCKET, clean_socket
from .protocol import moulti_listen, get_unix_credentials, send_json_message, recv_json_message
from .protocol import MoultiConnectionClosedException, MoultiProtocolException, Message, FDs
from .widgets import VertScroll, Step

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

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""
		yield self.title_label
		yield self.steps_container
		yield self.footer
		yield self.debug_step

	def on_ready(self) -> None:
		self.network_loop()
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

	def all_steps(self) -> Iterator[Step]:
		return cast(Iterator[Step], self.query('#steps_container Step').results())

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

	@work(thread=True)
	async def append_from_file_descriptor_to_queue(
		self,
		file_desc: int,
		queue: Queue,
		connection: Socket,
		raddr: str,
		message: Message
	) -> None:
		current_worker = get_current_worker()
		error = None
		try:
			# Read lines from the given file descriptor:
			with os.fdopen(file_desc, encoding='utf-8', errors='surrogateescape') as text_io:
				# Syscall-wise, Python will read(fd, buffer, count) where count = max(8192, read_size) - read_bytes.
				# But it will NOT return anything unless it has reached the hinted read size.
				# Out of the box, Moulti should strive to display lines as soon as possible, hence the default value of
				# 1. It remains possible to specify a larger value, e.g. when one knows there are going to be many
				# lines over a short timespan, e.g. "find / -ls".
				read_size = int(message.get('read_size', 1))
				while data := text_io.read(read_size):
					if current_worker.is_cancelled:
						break
					queue.put_nowait(data)
				queue.put_nowait(None)
		except Exception as exc:
			error = str(exc)
			self.logdebug(f'{raddr}: pass: {error}')
		self.reply(connection, raddr, message, done=error is None, error=error)

	@work(thread=True)
	async def append_from_queue_to_step(self, queue: Queue, step: Step) -> None:
		current_worker = get_current_worker()
		step.prevent_deletion += 1
		try:
			buffer = []
			while True:
				if current_worker.is_cancelled:
					break
				data = queue.get()
				if data is not None:
					# Buffer data to avoid queuing partial lines as, down the
					# line, RichLog.write() only handles complete lines:
					# look for the position of \n from the end of the string :
					eol = data.rfind('\n')
					if eol == -1: # no \n found, buffer the whole string:
						buffer.append(data)
					else:
						before = data[:eol]
						after = data[eol+1:]
						buffer.append(before)
						self.call_from_thread(step.append, ''.join(buffer))
						buffer.clear()
						if after:
							buffer.append(after)
				else:
					# Reached EOF: flush buffer and signal EOF:
					if buffer:
						self.call_from_thread(step.append, ''.join(buffer))
					break
		except Exception as exc:
			self.logdebug(f'append_from_queue_to_step: {exc}')
		finally:
			step.prevent_deletion -= 1

	def step_from_message(self, message: Message) -> None | Step:
		try:
			step = self.steps_container.query_one('#step_' + str(message['id']))
			return cast(Step, step)
		except Exception:
			return None

	def handle_pass_command(self, connection: Socket, raddr: str, message: Message, file_descriptors: FDs) -> None:
		step = self.step_from_message(message)
		if not step:
			self.reply(connection, raddr, message, done=False, error=f'no such step: {message.get("id")}')
			return
		if not file_descriptors:
			self.reply(connection, raddr, message, done=False, error='missing file descriptor for pass operation')
			return
		# Set up a queue between two workers:
		# - one that reads data from the file descriptor and replies to the client;
		# - one that appends lines to the step.
		queue: Queue = Queue()
		self.append_from_queue_to_step(queue, step)
		self.append_from_file_descriptor_to_queue(file_descriptors[0], queue, connection, raddr, message)

	def handle_message(self, connection: Socket, raddr: str, message: Message, file_descriptors: FDs) -> None:
		command = message.get('command')
		# Deal with special cases:
		if command == 'pass':
			self.handle_pass_command(connection, raddr, message, file_descriptors)
			return
		# Analyse the message to determine what to call or what error to return:
		call: Any = ()
		error = None
		try:
			if command == 'step':
				step = self.step_from_message(message)
				action = message.get('action')
				if action == 'add':
					if step:
						raise MoultiMessageException(f'step {message.get("id")} already exists')
					call = (self.steps_container.mount, Step(**message))
				else:
					# All other actions require an existing step:
					if not step:
						raise MoultiMessageException(f'no such step: {message.get("id")}')
					if action == 'append':
						if 'text' not in message:
							raise MoultiMessageException('missing text for append operation')
						call = (step.append, '\n'.join(message['text']))
					elif action == 'clear':
						call = (step.clear,)
					elif action == 'delete':
						if step.prevent_deletion:
							err = 'cannot delete this step as '
							err += f'{step.prevent_deletion} ongoing operations depend upon it'
							raise MoultiMessageException(err)
						call = (step.remove,)
					elif action == 'update':
						call = (step.update_properties, message)
					else:
						raise MoultiMessageException('unknown action {action}')
			elif command == 'set':
				if 'title' in message:
					call = (self.title_label.update, str(message['title']))
			else:
				raise MoultiMessageException('unknown command {command}')
		except MoultiMessageException as mme:
			error = str(mme)
		# At this stage, the analysis is complete; perform the required action and reply accordingly:
		else:
			if call:
				self.call_from_thread(*call)
		finally:
			self.reply(connection, raddr, message, done=error is None, error=error)

	def check_unix_credentials(self, socket: Socket) -> tuple[bool, int, int]:
		_, uid, gid = get_unix_credentials(socket)
		allowed = uid in self.allowed_uids or gid in self.allowed_gids
		return allowed, uid, gid

	@work(thread=True)
	async def network_loop(self) -> None:
		current_worker = get_current_worker()

		def getraddr(socket: Socket) -> str:
			raddr = socket.getpeername()
			if raddr:
				raddr = raddr.decode('utf-8').replace('\0', '@')
			return raddr + ':fd' + str(socket.fileno())

		def read(connection: Socket) -> None:
			raddr = None
			try:
				raddr = getraddr(connection)
				try:
					message, file_descriptors = recv_json_message(connection, max_fds=1)
				except (MoultiConnectionClosedException, ConnectionResetError) as exc:
					server_selector.unregister(connection)
					connection.close()
					self.logdebug(f'{raddr}: read: closed connection; cause: {exc}')
					return
				except MoultiProtocolException as mpe:
					self.logdebug(f'{raddr}: read: {mpe}')
					return
				self.logdebug(f'{raddr}: => message={message} file_descriptors={file_descriptors}')
				self.handle_message(connection, raddr, message, file_descriptors)
			except Exception as exc:
				self.logdebug(f'{raddr}: read: {exc}')


		def accept(socket: Socket) -> None:
			raddr = None
			try:
				connection, _ = socket.accept()
				raddr = getraddr(connection)
				self.logdebug(f'{raddr}: accept: accepted new connection')
				allowed, uid, gid = self.check_unix_credentials(connection)
				if not allowed:
					connection.close()
					self.logdebug(f'{raddr}: accept: closed connection: invalid Unix credentials {uid}:{gid}')
					return
				connection.setblocking(False)
				server_selector.register(connection, selectors.EVENT_READ, read)
			except Exception as exc:
				self.logdebug(f'{raddr}: accept: {exc}')

		try:
			server_socket = moulti_listen()
		except Exception as exc:
			# A Moulti instance is useless if it cannot listen:
			self.exit(f'Fatal: {exc}')
			return

		try:
			server_selector = selectors.DefaultSelector()
			server_selector.register(server_socket, selectors.EVENT_READ, accept)

			while not current_worker.is_cancelled:
				events = server_selector.select(1)
				for key, _ in events:
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

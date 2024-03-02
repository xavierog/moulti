import os
import json
import time
import asyncio
import datetime
import selectors
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterator
from socket import socket as Socket
from time import time_ns, localtime, strftime
from threading import get_ident, Lock
from rich.markup import MarkupError
from textual import work
from textual.app import App, ComposeResult
from textual.dom import BadIdentifier
from textual.widgets import Footer, Label
from textual.worker import get_current_worker, NoActiveWorker
from . import __version__ as MOULTI_VERSION
from .protocol import PRINTABLE_MOULTI_SOCKET, clean_socket, current_instance
from .protocol import moulti_listen, get_unix_credentials, send_json_message
from .protocol import MoultiConnectionClosedException, MoultiProtocolException, Message, FDs
from .protocol import MoultiTLVReader, data_to_message, getraddr
from .widgets.tui import MoultiWidgets
from .widgets.vertscroll import VertScroll
from .widgets.abstractstep.tui import AbstractStep
from .widgets.moulticonsole import MoultiConsole
from .widgets.quitdialog import QuitDialog

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
		("s", "save", "Save"),
		("n", "toggle_console", "Console"),
		("x", "expand_all", "Expand all"),
		("o", "collapse_all", "Collapse all"),
		("d", "toggle_dark", "Dark/Light"),
		("q", "quit", "Quit"),
	]

	def __init__(self, command: list[str]|None = None):
		self.init_security()
		self.init_widgets()
		self.end_user_console = MoultiConsole('moulti_console', classes='hidden')
		self.init_command = command
		self.init_command_running = False
		self.exit_first_policy = ''
		"""What to do when "moulti run" must exit before the process it launched? 'terminate' terminates the process,
		any other value leaves it running in the background."""
		self.save_lock = Lock()
		"""
		Lock that ensures Moulti does not generate multiple exports of the current instance at a time.
		"""
		super().__init__()
		self.dark = os.environ.get('MOULTI_MODE', 'dark') != 'light'

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
		threads_per_pass = 2 # Each "moulti pass" command spawns 2 threads -- cf Step.cli_action_pass()
		thread_count = default_threads + threads_per_pass * max_pass
		moulti_executor = ThreadPoolExecutor(max_workers=thread_count, thread_name_prefix='moulti')
		asyncio.get_running_loop().set_default_executor(moulti_executor)
		self.logconsole(f'allow up to {thread_count} threads for up to {max_pass} concurrent "moulti pass" commands')

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""
		yield self.title_label
		yield self.steps_container
		yield self.footer
		yield self.end_user_console

	def on_ready(self) -> None:
		self.logconsole(f'Moulti v{MOULTI_VERSION}')
		self.init_threads()
		widget_list = ' '.join(MoultiWidgets.registry().keys())
		self.logconsole(f'known widgets: {widget_list}')
		self.network_loop()

	def network_loop_is_ready(self) -> None:
		if self.init_command is not None:
			self.exec(self.init_command)

	@work(thread=True)
	def exec(self, command: list[str]) -> None:
		worker = get_current_worker()
		import subprocess # pylint: disable=import-outside-toplevel
		try:
			self.init_command_running = True
			environment = os.environ.copy()
			environment['MOULTI_RUN'] = 'moulti'
			environment['MOULTI_SOCKET_PATH'] = PRINTABLE_MOULTI_SOCKET
			environment['MOULTI_INSTANCE_PID'] = str(os.getpid())
			self.logconsole(f'exec: about to run {command}')
			# Not using 'with' because that waits for the process to exit; pylint: disable=consider-using-with
			process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL)
			self.logconsole(f'exec: {command} launched with PID {process.pid}')
			returncode = None
			while not worker.is_cancelled:
				returncode = process.poll() # non-blocking wait(), e.g. wait4(process.pid, result_addr, WNOHANG, NULL)
				if returncode is not None:
					self.init_command_running = False
					self.logconsole(f'exec: {command} exited with return code {returncode}')
					break
				time.sleep(0.5)
			if returncode is None:
				self.logconsole(f'exec: {command} is still running (PID {process.pid}) but Moulti is about to exit')
				if self.exit_first_policy == 'terminate':
					process.terminate()
				# else just leave the process running in the background and exit.
		except Exception as exc:
			self.logconsole(f'exec: error running {command}: {exc}')
			self.init_command_running = False

	def all_steps(self) -> Iterator[AbstractStep]:
		return self.query('#steps_container AbstractStep').results(AbstractStep)

	def export_properties(self) -> dict[str, Any]:
		prop = {}
		prop['title'] = str(self.title_label.renderable)
		return prop

	def logconsole(self, line: str) -> None:
		line = timestamp() + line
		if self._thread_id == get_ident():
			self.end_user_console.write(line)
		else:
			try:
				worker = get_current_worker()
			except NoActiveWorker:
				worker = None
			if worker and not worker.is_cancelled:
				self.call_from_thread(self.end_user_console.write, line)

	def action_toggle_console(self) -> None:
		"""Toggle the console."""
		self.end_user_console.toggle_class('hidden')

	def action_expand_all(self) -> None:
		"""Expand all steps."""
		for step in self.all_steps():
			step.collapsible.collapsed = False

	def action_collapse_all(self) -> None:
		"""Collapse all steps."""
		for step in self.all_steps():
			step.collapsible.collapsed = True

	async def action_quit(self) -> None:
		"""Quit Moulti."""
		if self.init_command is not None and self.init_command_running:
			message = 'The command passed to "moulti run" is still running.'
			self.push_screen(QuitDialog(message))
			return
		await super().action_quit()

	def on_quit_dialog_exit_request(self, exit_request: QuitDialog.ExitRequest) -> None:
		"""Exit Moulti, as instructed by the Quit Dialog."""
		self.exit_first_policy = exit_request.exit_first_policy
		self.exit()

	@work(thread=True)
	def action_save(self) -> None:
		"""
		Export everything currently shown by the instance as a bunch of files in a directory.
		"""
		if not self.save_lock.acquire(blocking=False): # pylint: disable=consider-using-with
			self.logconsole('save: this instance is already being saved.')
			summary = 'This instance is already being saved.'
			self.notify(summary, title='One at a time!', severity='warning')
			return
		export_dir_fd = None
		try:
			# Determine where to create the export directory:
			basepath = os.environ.get('MOULTI_SAVE_PATH') or '.'
			# Determine what to name the export directory:
			iso_8601_date = datetime.datetime.now().isoformat().replace(":", "-")
			export_dirname = f'{current_instance()}-{iso_8601_date}'
			export_dirpath = os.path.join(basepath, export_dirname)
			# Create the export directory:
			os.makedirs(export_dirpath)
			# Create an "opener" function that opens files relatively to the export directory:
			export_dir_fd = os.open(export_dirpath, 0)
			def opener(path: str, flags: int) -> int:
				return os.open(path, flags, mode=0o666, dir_fd=export_dir_fd)
			# Proceed with the export itself:
			saved_steps = self.save_steps(opener)
			self.save_properties(opener, ('0'*len(str(saved_steps))) + '-')
			# Notify users:
			summary = f'{saved_steps} steps successfully saved\nDir: {basepath}\nSubdir: {export_dirname}'
			self.notify(summary, title='Saved!')
		except Exception as exc:
			self.logconsole(f'save: failed: {exc}')
			summary = 'An error occurred during saving.\nRefer to the console for more details.'
			self.notify(summary, title='Save failed!', severity='error')
		finally:
			self.save_lock.release()
			if export_dir_fd is not None:
				os.close(export_dir_fd)

	def save_properties(self, opener: Callable[[str,int], int], filename_prefix: str = '') -> None:
		filename = filename_prefix + 'instance.properties.json'
		extra_properties = {'command': 'set'}
		with open(filename, 'w', encoding='utf-8', errors='surrogateescape', opener=opener) as instance_file_desc:
			json.dump({**extra_properties, **self.export_properties()}, instance_file_desc, indent=4)
			instance_file_desc.write('\n')

	def save_steps(self, opener: Callable[[str,int], int]) -> int:
		# Fetch a list of all steps to export them:
		steps = list(self.all_steps())
		# Filenames are numbered from 0 to n; how many characters do we need to write n?
		number_prefix_length = len(str(len(steps)))
		step_index = 0
		for step_index, step in enumerate(steps, start=1):
			command = MoultiWidgets.class_to_command(type(step))
			if command is None:
				continue
			extra_properties = {'command': command, 'action': 'add'}
			filename = f'{step_index:0{number_prefix_length}d}-{step.title_from_id()}'
			step.save(opener, filename, extra_properties)
		return step_index

	def reply(self, connection: Socket, raddr: str, message: dict[str, Any], **kwargs: Any) -> None:
		try:
			# If the original message bears a message id, use it to send a
			# smaller reply. Otherwise, send the original message back with
			# extra data.
			if msgid := message.get('msgid'):
				message = {'msgid': msgid, **kwargs}
			else:
				message = {**message, **kwargs}
			self.logconsole(f'{raddr}: <= message={message}')
			send_json_message(connection, message)
		except Exception as exc:
			self.logconsole(f'{raddr}: reply: kwargs={kwargs}: {exc}')

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
					if not isinstance(step, command_class):
						raise MoultiMessageException(f'{message.get("id")} is not a {command}')
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
							self.logconsole(f'{raddr}: {line}')
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
		except (BadIdentifier, MarkupError, MoultiMessageException) as exc:
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
					self.logconsole(f'{raddr}: read: closed connection; cause: {exc}')
					return
			except Exception as exc:
				self.logconsole(f'{raddr}: read: {exc}')

		def got_tlv(socket: Socket, raddr: str, data_type: str, data: bytes, file_descriptors: FDs) -> None:
			if data_type == 'JSON':
				message = data_to_message(data)
				self.logconsole(f'{raddr}: => {message=} {file_descriptors=}')
				self.handle_message(socket, raddr, message, file_descriptors)
			else:
				raise MoultiProtocolException(f'cannot handle {data_type} {len(data)}-byte message')

		def accept(socket: Socket) -> None:
			raddr = None
			try:
				connection, _ = socket.accept()
				raddr = getraddr(connection)
				self.logconsole(f'{raddr}: accept: accepted new connection')
				# Check Unix credentials (uid/gid) if and only if Moulti listens on an abstract socket.
				# Regular sockets are protected by file permissions.
				if server_socket_is_abstract:
					allowed, uid, gid = self.check_unix_credentials(connection)
					if not allowed:
						connection.close()
						self.logconsole(f'{raddr}: accept: closed connection: invalid Unix credentials {uid}:{gid}')
						return
				connection.setblocking(False)
				tlv_reader = MoultiTLVReader(connection, raddr, got_tlv, self.logconsole)
				server_selector.register(connection, selectors.EVENT_READ, tlv_reader)
			except Exception as exc:
				self.logconsole(f'{raddr}: accept: {exc}')

		try:
			server_socket, server_socket_is_abstract = moulti_listen()
		except Exception as exc:
			# A Moulti instance is useless if it cannot listen:
			self.exit(f'Fatal: {exc}')
			return
		socket_type = "abstract socket" if server_socket_is_abstract else "socket"
		self.logconsole(f'listening on {socket_type} {PRINTABLE_MOULTI_SOCKET}')

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
			self.logconsole(f'network loop: {exc}')
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

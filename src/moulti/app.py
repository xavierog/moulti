import os
import sys
import json
import time
import asyncio
import datetime
import selectors
import subprocess
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Any, Callable, Iterator, cast
from socket import socket as Socket
from shutil import which
from time import time_ns, localtime, strftime
from threading import get_ident, Lock
from rich.markup import MarkupError, escape
from rich.text import Text
from textual import work
from textual import __version__ as TEXTUAL_VERSION
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.dom import BadIdentifier
from textual.reactive import reactive
from textual.widgets import Label, ProgressBar
from textual.worker import get_current_worker, NoActiveWorker
from . import __version__ as MOULTI_VERSION
from .ansi import AnsiThemePolicy, dump_filters
from .helpers import call_all, clean_selector
from .protocol import PRINTABLE_MOULTI_SOCKET, clean_socket, current_instance
from .protocol import default_moulti_socket_path, from_printable
from .protocol import moulti_listen, get_unix_credentials, send_json_message
from .protocol import MoultiConnectionClosedException, MoultiProtocolException, Message, FDs
from .protocol import MoultiTLVReader, data_to_message, getraddr
from .search import TextSearch, MatchSpan
from .themes import MOULTI_THEMES
from .widgets import MoultiWidgetException
from .widgets.tui import MoultiWidgets
from .widgets.footer import Footer
from .widgets.stepcontainer import StepContainer
from .widgets.abstractstep.tui import AbstractStep
from .widgets.collapsiblestep.tui import CollapsibleStep
from .widgets.step.tui import Step
from .widgets.moulticonsole import MoultiConsole
from .widgets.quitdialog import QuitDialog
from .widgets.searchinput import SearchInput, SearchInputWidget
from .widgets.helpscreen import HelpScreen


MOULTI_RUN_OUTPUT_STEP_ID = 'moulti_run_output'

def timestamp() -> str:
	timestamp_ns = time_ns()
	timestamp_s = timestamp_ns//10**9
	ns = timestamp_ns - timestamp_s * 10**9
	ms = ns // 10**6
	timestr = strftime('%FT%T', localtime(timestamp_s))
	timestr = f'{timestr}.{ms:03d} '

	return timestr

def is_ansible(command: list[str]) -> bool:
	return bool(len(command)) and 'ansible' in command[0]

def add_abs_path_to_environment(env: dict[str, str], env_var: str, command: str) -> bool:
	if abs_path := which(command):
		env[env_var] = abs_path
		return True
	return False

def run_environment(command: list[str], socket_path: str|None, copy: bool = True) -> dict[str, str]:
	"""
	Return environment variables set by "Moulti run <command>".
	"""
	environment = os.environ.copy() if copy else {}

	environment['MOULTI_RUN'] = 'moulti'
	environment['MOULTI_SOCKET_PATH'] = socket_path or PRINTABLE_MOULTI_SOCKET
	environment['MOULTI_INSTANCE_PID'] = str(os.getpid())

	if 'SSH_ASKPASS' not in os.environ:
		environment['SSH_ASKPASS'] = 'moulti-askpass'
		environment['SSH_ASKPASS_REQUIRE'] = 'force'

	if 'SUDO_ASKPASS' not in os.environ:
		# sudo requires an absolute path:
		add_abs_path_to_environment(environment, 'SUDO_ASKPASS', 'moulti-askpass')

	if (ansible_policy := os.environ.get('MOULTI_ANSIBLE', 'default')) != 'no':
		if ansible_policy == 'force' or (is_ansible(command) and 'ANSIBLE_STDOUT_CALLBACK' not in os.environ):
			from . import ansible # pylint: disable=import-outside-toplevel
			if ansible_callback_paths := os.environ.get('ANSIBLE_CALLBACK_PLUGINS', ''):
				ansible_callback_paths += ':'
			ansible_callback_paths += ansible.__path__[0]
			environment['ANSIBLE_CALLBACK_PLUGINS'] = ansible_callback_paths
			environment['ANSIBLE_STDOUT_CALLBACK'] = 'moulti'
			environment['ANSIBLE_FORCE_COLOR'] = 'yes'
			# ansible-playbook may still read from /dev/tty through getpass.getpass():
			ansible_askpass = {
				'ANSIBLE_CONNECTION_PASSWORD_FILE': {'args': ('-k', '--ask-pass'), 'suffix': 'connection-password'},
				'ANSIBLE_BECOME_PASSWORD_FILE': {'args': ('-K', '--ask-become-pass'), 'suffix': 'become-password'},
				'ANSIBLE_VAULT_PASSWORD_FILE': {
					'args': ('-J', '--ask-vault-pass', '--ask-vault-password'),
					'suffix': 'vault-client',
				},
			}
			for env_var, conf in ansible_askpass.items():
				if env_var in environment:
					continue
				for arg in conf['args']:
					if arg in command:
						add_abs_path_to_environment(environment, env_var, f'moulti-askpass-{conf["suffix"]}')
						del command[command.index(arg)]

	return environment

class MoultiMessageException(Exception):
	pass

class Moulti(App):
	"""
	moulti is a Terminal User Interface (TUI) meant to display multiple outputs.
	It is visually similar to https://github.com/dankilman/multiplex but unlike
	it, moulti does not do anything until instructed to.
	"""

	# The header and search input widgets should remain visible in maximized mode:
	ALLOW_IN_MAXIMIZED_VIEW = '#header,SearchInputWidget,' + App.ALLOW_IN_MAXIMIZED_VIEW

	BINDINGS = [
		("s", "save", "Save"),
		Binding("z", "toggle_console", "Console"),
		("x", "collapse_all(False)", "Expand all"),
		("o", "collapse_all(True)", "Collapse all"),
		Binding("X", "collapse_new(False)", "Expand new widgets", show=False),
		Binding("O", "collapse_new(True)", "Collapse new widgets", show=False),
		Binding("ctrl+x", "collapse_both(False)", "Expand", show=False),
		Binding("ctrl+o", "collapse_both(True)", "Collapse", show=False),
		Binding("d", "light_mode", "Light"),
		Binding("d", "dark_mode", "Dark"),
		("h", "help", "Help"),
		("q", "quit", "Quit"),
		Binding("/", "search(True)", "Search forward", show=False),
		Binding("?", "search(False)", "Search backward", show=False),
		Binding("N", "search_previous(False)", "Previous search result", show=False),
		Binding("n", "search_next(False)", "Next search result", show=False),
	]

	# Disable Textual's command palette; it may come back if Moulti ends up with too many commands though:
	ENABLE_COMMAND_PALETTE = False
	# Do not minimize on 'escape' because widgets need to restore their max height:
	ESCAPE_TO_MINIMIZE = False

	dark = reactive(True)
	"""True for dark mode, False for light mode."""

	def __init__(self, command: list[str]|None = None, instance_name: str|None = None):
		self.instance_name = instance_name
		self.socket_path = default_moulti_socket_path(instance_name) if instance_name else PRINTABLE_MOULTI_SOCKET
		self.init_security()
		self.init_quit_policy()
		self.init_widgets()
		self.end_user_console = MoultiConsole('moulti_console', classes='hidden')
		self.init_command = command
		self.init_command_running: bool|None = None
		"""Whether the init command is running: None until it starts, True while it runs, False afterwards."""
		self.exit_first_policy = ''
		"""What to do when "moulti run" must exit before the process it launched? 'terminate' terminates the process,
		any other value leaves it running in the background."""
		self.save_lock = Lock()
		"""
		Lock that ensures Moulti does not generate multiple exports of the current instance at a time.
		"""
		self.enforce_collapsible: bool|None = self.init_enforce_collapsible()
		"""
		Whether to enforce the state of new collapsible widgets.
		None: do not enforce
		True: force-collapse new collapsible widgets
		False: force-expand new collapsible widgets
		"""
		self.current_search: TextSearch|None = None
		"""
		Current text search.
		"""
		self.title_search_cursor: MatchSpan = None
		self.search_cursor: bool|None = None
		"""
		False: search the title; True: search steps; None: decide based on search.next_result.
		"""
		super().__init__()
		self.dark = os.environ.get('MOULTI_MODE', 'dark') != 'light'
		self.set_title('Moulti')

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

	def init_quit_policy(self) -> None:
		"""
		Initialize the quit policy, i.e. how Moulti should behave when end users request to quit.
		"""
		# Default quit policy: ask if the driving process is still running, otherwise quit directly:
		self.quit_policy = {'running': 'ask', 'default': 'quit'}
		# The default policy can be overridden through the environment variable MOULTI_QUIT_POLICY:
		for override in os.environ.get('MOULTI_QUIT_POLICY', '').split(';'):
			if override.startswith('running='):
				override = override[8:]
				if override in ('ask', 'leave', 'terminate'):
					self.quit_policy['running'] = override
			elif override.startswith('default='):
				override = override[8:]
				if override in ('ask', 'quit'):
					self.quit_policy['default'] = override

	def init_widgets(self) -> None:
		self.title_label = Label('Title', id='header')
		self.title_label.tooltip = f'Instance name: {current_instance()}'
		self.steps_container = StepContainer()
		self.search_input = SearchInputWidget(id='search_bar')
		self.progress_bar = ProgressBar(id='progress_bar', show_eta=False)
		self.footer = Footer()

	def init_enforce_collapsible(self) -> bool|None:
		mec_env_var = os.environ.get('MOULTI_ENFORCE_COLLAPSIBLE')
		if mec_env_var == 'collapse':
			return True
		if mec_env_var == 'expand':
			return False
		return None

	def set_title(self, title: str) -> None:
		self.title = title
		self.title_label.update(title)

	def setup_ansi_behavior(self) -> None:
		"""
		By default and by design, Textual strives to avoid outputting ANSI colors (i.e. the 16 colors that have no
		official value). This makes perfect sense for most applications. Moulti is special because its users expect
		steps to display the exact same thing as their terminal with no or little care for portability.
		"""
		if os.environ.get('MOULTI_ANSI') == 'textual_default':
			# MOULTI_ANSI=textual_default means Moulti neither loads, applies nor alters any theme.
			# However, Textual default themes will apply, unaltered.
			return
		policy = AnsiThemePolicy.from_environment('MOULTI_')
		self.logconsole(f'{policy}')
		policy.apply(self)
		self.logconsole(f'Textual filters: {dump_filters(self) or "none"}')

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
		yield self.search_input
		yield self.progress_bar
		yield self.footer
		yield self.end_user_console

	def on_mount(self) -> None:
		for theme in MOULTI_THEMES.values():
			self.register_theme(theme)
		self.theme = 'moulti-dark' if self.dark else 'moulti-light'

	def on_ready(self) -> None:
		self.logconsole(f'Moulti v{MOULTI_VERSION}, Textual v{TEXTUAL_VERSION}, Python v{sys.version}')
		self.logconsole(f'instance "{current_instance()}", PID {os.getpid()}')
		self.logconsole('quit policy: ' + ', '.join(f"{k}='{v}'" for k,v in self.quit_policy.items()))
		self.setup_ansi_behavior()
		self.init_threads()
		widget_list = ' '.join(MoultiWidgets.registry().keys())
		self.logconsole(f'known widgets: {widget_list}')
		self.network_loop()

	def on_search_input_cancel_search(self, _event: SearchInput.CancelSearch) -> None:
		if self.screen.maximized:
			self.screen.maximized.focus()

	def on_search_input_widget_new_search(self, message: SearchInputWidget.NewSearch) -> None:
		self.current_search = message.search
		if self.screen.maximized:
			self.screen.maximized.focus()
		self.search(self.current_search)

	def search_title(self, search: TextSearch) -> bool:
		text = Text.from_markup(self.title)
		self.title_search_cursor = search.search(text.plain, self.title_search_cursor)
		if found := self.title_search_cursor is not None:
			search.highlight(text, *self.title_search_cursor)
		self.title_label.update(text)
		return found

	@work(exclusive=True, group='search', name='search')
	async def search(self, search: TextSearch) -> bool:
		if self.search_cursor is None:
			self.search_cursor = not search.next_result
			parts_to_search = 2 # Only 2 parts to search here
		else:
			# This is a 3-part search:
			# 1. from the latest result to the end of the current part
			# 2. inside the other part
			# 3. from the start of the current part to the latest result
			parts_to_search = 3
		for _ in range(parts_to_search):
			found = self.steps_container.search(search) if self.search_cursor else self.search_title(search)
			if found:
				return True
			self.search_cursor = not self.search_cursor
		search_str = escape(str(search))
		self.notify(f'{search_str}: not found', title='Text search: pattern not found', severity='error')
		return False

	def network_loop_is_ready(self) -> None:
		if self.init_command is not None:
			self.exec(self.init_command)

	def output_policy(self) -> bool|None:
		"""
		`moulti run` launches an arbitrary command. In an ideal world, this command should not output anything on
		stdout/stderr. In practice, this method returns:
		- None if Moulti should ignore stdout/stderr (default)
		- False if Moulti should discard stdout/stderr
		- True if Moulti should harvest stdout/stderr and append it to the "moulti_run_output" step
		"""
		policy = None
		if value := os.environ.get('MOULTI_RUN_OUTPUT'):
			if value == 'discard':
				policy = False
			elif value == 'harvest':
				policy = True
		return policy

	def output_policy_popen_args(self) -> dict[str, Any]:
		"""
		Return the adequate subprocess.Popen() arguments for `moulti run` based on output_policy().
		"""
		policy = self.output_policy()
		if policy is None: # default/ignore
			return {'stdout': None, 'stderr': None}
		if policy: # harvest
			return {
				'stdout': subprocess.PIPE,
				'stderr': subprocess.STDOUT,
				'text': False,
			}
		# discard:
		return {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}

	def output_policy_step(self) -> Step:
		"""
		Return the step that should display unexpected stdout/stderr lines harvested by `moulti run`.
		"""
		step = self.step_from_message({'id': MOULTI_RUN_OUTPUT_STEP_ID})
		if step is not None:
			return cast(Step, step)
		# This should not fail since the id is valid and reserved:
		step = Step(id=MOULTI_RUN_OUTPUT_STEP_ID, collapsed=False)
		call = (self.steps_container.add_step, step)
		self.call_from_thread(call_all, [call])
		return step

	def output_policy_pass(self, step: Step, filedesc: Any, initial_data: str) -> None:
		"""
		Set up the queue and threads necessary to display unexpected stdout/stderr lines harvested by `moulti run`.
		"""
		# This method is very similar to Step.cli_action_pass().
		queue: Queue = Queue()
		# Helper functions:
		def reply(**_kwargs: Any) -> None:
			pass
		def debug(line: str) -> None:
			self.logconsole(f'exec: {line}')
		helpers = {'file_descriptors': [filedesc], 'debug': debug, 'reply': reply}
		step.append_from_queue(queue, helpers)
		queue.put_nowait(initial_data)
		step.append_from_file_descriptor_to_queue(queue, {}, helpers)

	@work(thread=True, group='app-exec', name='moulti-run')
	def exec(self, command: list[str]) -> None:
		"""
		Launch the given command with the assumption it is meant to drive the current Moulti instance.
		This method is the heart of `moulti run`.
		"""
		worker = get_current_worker()
		harvest_output = self.output_policy() # Harvest stdout/stderr lines
		output_delegated = False
		try:
			self.init_command_running = True
			original_command = command.copy()
			self.logconsole(f'exec: about to run {original_command}')
			environment = run_environment(command, self.socket_path)
			popen_args: dict[str, Any] = {'env': environment, 'stdin': subprocess.DEVNULL}
			# Important: run_environment() may have modified command:
			if command != original_command:
				self.logconsole(f'exec: command changed to {command}')
			# Not using 'with' because that waits for the process to exit; pylint: disable=consider-using-with
			process = subprocess.Popen(command, **popen_args, **self.output_policy_popen_args())
			self.logconsole(f'exec: {command} launched with PID {process.pid}')
			returncode = None
			output_selector = None
			if harvest_output:
				output_selector = selectors.DefaultSelector()
				assert process.stdout is not None # for mypy
				output_selector.register(process.stdout, selectors.EVENT_READ)

			while not worker.is_cancelled:
				if output_selector is not None and output_selector.select(0):
					# If the child process outputs anything other than end-of-file, pass it to a special step:
					assert process.stdout is not None and hasattr(process.stdout, 'raw') # for mypy
					if initial_data := process.stdout.raw.read(1):
						step = self.output_policy_step()
						self.logconsole(f'exec: output detected on fd {process.stdout.fileno()}, harvesting')
						self.output_policy_pass(step, process.stdout, initial_data)
						output_delegated = True
					# We no longer need to watch output in this loop:
					clean_selector(output_selector, close_fds=False, close=True)
					output_selector = None
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
		finally:
			clean_selector(output_selector, close_fds=False, close=True)
			if harvest_output and not output_delegated and process.stdout is not None:
				self.logconsole(f'exec: no output harvested, closing child process stdout fd {process.stdout.fileno()}')
				process.stdout.close()

	def all_steps(self) -> Iterator[AbstractStep]:
		return self.steps_container.ordered_steps()

	def export_properties(self) -> dict[str, Any]:
		prop: dict[str, Any] = {}
		prop['title'] = self.title
		prop['progress_bar'] = self.progress_bar.styles.display == 'block'
		prop['progress_target'] = self.progress_bar.total
		prop['progress'] = self.progress_bar.progress
		prop['step_position'] = 'bottom' if self.steps_container.has_class('bottom') else 'top'
		prop['step_direction'] = 'down' if self.steps_container.layout_direction_is_down else 'up'
		return prop

	def logconsole(self, line: str) -> None:
		line = timestamp() + line + '\n'
		if self._thread_id == get_ident():
			self.end_user_console.write(line)
		else:
			try:
				worker = get_current_worker()
			except NoActiveWorker:
				worker = None
			if worker and not worker.is_cancelled:
				self.call_from_thread(self.end_user_console.write, line)

	def action_light_mode(self) -> None:
		self.theme = 'moulti-light'
		self.dark = False
		self.refresh_bindings()

	def action_dark_mode(self) -> None:
		self.theme = 'moulti-dark'
		self.dark = True
		self.refresh_bindings()

	def check_action(self, action: str, _parameters: tuple[object, ...]) -> bool:
		if action == 'light_mode':
			return self.dark
		if action == 'dark_mode':
			return not self.dark
		if self.screen.maximized and action in ('save', 'toggle_console', 'collapse_all'):
			return False
		return True

	def action_toggle_console(self) -> None:
		"""Toggle the console."""
		self.end_user_console.toggle_class('hidden')
		if self.end_user_console.has_class('hidden'):
			# Not ideal but reasonable:
			self.steps_container.focus(False)
			# Work around a rendering issue after the console is hidden:
			# Certainly https://github.com/Textualize/textual/issues/5056
			self.refresh(layout=True)
		else:
			# It is often necessary to scroll the console, so give it the focus:
			self.end_user_console.log_widget.focus(False)

	def action_search(self, next_result: bool) -> None:
		self.search_input.action_pop(next_result)
		# Work around a rendering issue when the search bar appears:
		# Likely https://github.com/Textualize/textual/issues/5056
		self.refresh(layout=True)

	def action_search_previous(self) -> None:
		if self.current_search is not None:
			search_copy = self.current_search.copy()
			search_copy.next_result = not search_copy.next_result
			self.search(search_copy)

	def action_search_next(self) -> None:
		if self.current_search is not None:
			self.search(self.current_search)

	def action_collapse_all(self, collapsed: bool = True) -> None:
		"""Collapse all existing steps."""
		for step in self.steps_container.query('CollapsibleStep').results(CollapsibleStep):
			step.collapsible.collapsed = collapsed

	def action_collapse_new(self, enforce: bool) -> None:
		"""Collapse new steps."""
		action = {True: 'collapsing', False: 'expanding'}
		desc = ''
		if self.enforce_collapsible == enforce:
			desc = f'No longer {action[self.enforce_collapsible]}'
			self.enforce_collapsible = None
		else:
			self.enforce_collapsible = enforce
			desc = action[self.enforce_collapsible].capitalize()
		self.notify(f'{desc} new steps')

	def action_collapse_both(self, collapsed: bool) -> None:
		"""Collapse both existing and new steps."""
		if self.enforce_collapsible != collapsed:
			self.action_collapse_new(collapsed)
		self.action_collapse_all(collapsed)

	def action_help(self) -> None:
		"""Display the help screen."""
		self.push_screen(HelpScreen())

	async def action_quit(self) -> None:
		"""Quit Moulti."""
		mode = 'default'
		message = ''
		allow_terminate = False
		if self.init_command is not None and self.init_command_running:
			mode = 'running'
			message = 'The command passed to "moulti run" is still running.'
			allow_terminate = True
		policy = self.quit_policy[mode]
		if policy == 'ask':
			try:
				self.query_one('QuitDialog', QuitDialog).new_quit_request()
			except NoMatches:
				self.push_screen(QuitDialog(message, allow_terminate))
			return
		# leave/quit, terminate:
		self.exit_first_policy = policy
		await super().action_quit()

	def on_quit_dialog_exit_request(self, exit_request: QuitDialog.ExitRequest) -> None:
		"""Exit Moulti, as instructed by the Quit Dialog."""
		self.exit_first_policy = exit_request.exit_first_policy
		self.exit()

	@work(thread=True, group='app-save', name='save')
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
		calls: list[Any] = []
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
					# Users may create the 'moulti_run_output' step but it MUST be a step, not a question or a divider:
					if message['id'] == MOULTI_RUN_OUTPUT_STEP_ID and message['command'] != 'step':
						err = f'{MOULTI_RUN_OUTPUT_STEP_ID} is a reserved id that must be assigned to a step'
						raise MoultiMessageException(err)
					if self.enforce_collapsible is not None:
						message['collapsed'] = self.enforce_collapsible
					calls.append((self.steps_container.add_step, command_class(**message)))
				else:
					# All other actions require an existing step:
					if not step:
						raise MoultiMessageException(f'unknown id: {message.get("id")}')
					if not isinstance(step, command_class):
						raise MoultiMessageException(f'{message.get("id")} is not a {command}')
					if action == 'update':
						step.check_properties(message)
						if self.enforce_collapsible is not None and message.get('collapsed') is not None:
							del message['collapsed']
						calls.append((step.update_properties, message))
					elif action == 'delete':
						if step.prevent_deletion:
							err = 'cannot proceed with deletion as '
							err += f'{step.prevent_deletion} ongoing operations prevent it'
							raise MoultiMessageException(err)
						calls.append((self.steps_container.remove_step, step))
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
						if call:
							calls.append(call)
						else:
							finally_reply = False
			elif command == 'set':
				if message.get('title') is not None:
					calls.append((self.set_title, str(message['title'])))
				if message.get('step_position') is not None:
					calls.append((self.steps_container.set_class, message['step_position'] == 'bottom', 'bottom'))
				if message.get('step_direction') is not None:
					is_down = bool(message['step_direction'] != 'up')
					calls.append((setattr, self.steps_container, 'layout_direction_is_down', is_down))
				if message.get('progress_bar') is not None:
					display_progress_bar = 'block' if bool(message['progress_bar']) else 'none'
					calls.append((setattr, self.progress_bar.styles, 'display', display_progress_bar))
				if message.get('progress_target') is not None:
					progress_target = float(message['progress_target'])
					final_progress_target: float|None = None if progress_target <= 0 else progress_target
					calls.append((setattr, self.progress_bar, 'total', final_progress_target))
				if message.get('progress') is not None:
					progress_float = float(message['progress'])
					progress_str = str(message['progress'])
					if progress_str.startswith('+') or progress_str.startswith('-'):
						calls.append((self.progress_bar.advance, progress_float))
					else:
						calls.append((setattr, self.progress_bar, 'progress', progress_float))
			elif command == 'scroll':
				step = self.step_from_message(message)
				if step is None:
					raise MoultiMessageException(f'unknown id: {message.get("id")}')
				try:
					offset = int(message['offset'])
				except Exception:
					offset = True
				calls.append((self.steps_container.scroll_to_step, step, offset))
			elif command == 'ping':
				pass
			else:
				raise MoultiMessageException(f'unknown command {command}')
			# At this stage, the analysis is complete; perform the required action and reply accordingly:
			if calls:
				self.call_from_thread(call_all, calls)
		except (BadIdentifier, MarkupError, MoultiMessageException, MoultiWidgetException, ValueError) as exc:
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

	@work(thread=True, group='app-network', name='network-loop')
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
			server_socket, server_socket_is_abstract = moulti_listen(bind=from_printable(self.socket_path))
		except Exception as exc:
			# A Moulti instance is useless if it cannot listen:
			tip = 'Tip: try setting the MOULTI_INSTANCE environment variable, e.g. MOULTI_INSTANCE=$$ moulti init'
			self.exit(return_code=100, message=f'Fatal: {exc}\n{tip}')
			return
		socket_type = "abstract socket" if server_socket_is_abstract else "socket"
		self.logconsole(f'listening on {socket_type} {self.socket_path}')

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
			clean_socket(self.socket_path)
			# Explicitly stop listening and close all sockets: this makes sense when and if the
			# Python process does not exit after this App has finished running.
			server_socket.close()
			clean_selector(server_selector, close_fds=True, close=True)

	DEFAULT_CSS = """
	/* Styles inherited by all widgets: */
	$scrollbar_background: #b2b2b2;
	$scrollbar_inactive_bar: #686868;
	$scrollbar_active_bar: $primary-darken-1;
	Widget {
		/* By default, in dark mode, scrollbars are not rendered clearly; enforce their colours: */
		scrollbar-background: $scrollbar_background;
		scrollbar-background-hover: $scrollbar_background;
		scrollbar-background-active: $scrollbar_background;
		scrollbar-color: $scrollbar_inactive_bar;
		scrollbar-color-active: $scrollbar_active_bar;
		scrollbar-color-hover: $scrollbar_active_bar;
	}
	#textual-tooltip { /* overrides "Tooltip" since it is more specific */
		background: $surface;
	}

	/* One-line title at the top of the screen: */
	#header {
		text-align: center;
		/* For the title to appear centered, the widget must occupy all available width: */
		width: 100%;
		background: $primary;
		color: $text;
		dock: top; /* relevant in maximized mode */
	}

	/* Show the progress bar as a full-width extension of the footer: */
	#progress_bar {
		display: none; /* Do not display by default */
		background: $primary;
		padding-left: 1;
		padding-right: 1;
		width: 100%;
		&> Bar {
			width: 1fr;
			&> .bar--bar {
				color: $warning;
			}
		}
	}
	"""

	# Allow end users to redefine Moulti's look and feel through an optional
	# custom CSS set through an environment variable:
	CSS_PATH = os.environ.get('MOULTI_CUSTOM_CSS') or None

def main(command: list[str]|None = None) -> None:
	moulti_app = Moulti(command=command)
	moulti_app.run()
	sys.exit(moulti_app.return_code)

if __name__ == '__main__':
	main()
else:
	app = Moulti()

from __future__ import annotations
import os
import sys
import subprocess as sp
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING
# pylint: disable=import-error
from ansible.errors import AnsiblePromptInterrupt # type: ignore
from ansible.utils.color import parsecolor # type: ignore
from ansible.utils.display import Display # type: ignore
try: # for Ansible 2.16
	from ansible.utils.display import proxy_display # type: ignore
except ImportError: # for Ansible >= 2.17
	proxy_display = Display._proxy # pylint: disable=protected-access
from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule # type: ignore
from ansible.utils.unsafe_proxy import wrap_var # type: ignore

if TYPE_CHECKING:
	import collections.abc as c

DOCUMENTATION = '''
    name: moulti
    type: stdout
    short_description: Moulti output for Ansible playbooks
    version_added: N/A
    description:
        - This callback issues `moulti` commands to append plays and tasks to a pre-existing [Moulti](https://github.com/xavierog/moulti) instance.
    extends_documentation_fragment:
      - default_callback
      - result_format_callback
    requirements:
      - set as stdout in configuration
'''

Answer = tuple[str, list[str]]
"""
The first element of the tuple is the answer itself.
The second element is the list of inputquestion widgets created to obtain this answer.
"""

COLLAPSIBLE = ('prompt', 'recap', 'task')
COLLAPSE = [part for part in os.environ.get('MOULTI_ANSIBLE_COLLAPSE', '').split(',') if part in COLLAPSIBLE]
COLLAPSE = ['ansible_' + part for part in COLLAPSE]

def escape_rich_tags(value: str) -> str:
	return value.replace('[', r'\[')

class MoultiDisplay(Display):
	"""
	Variant of Ansible's regular display that:
	- spawns a new Moulti step for some (but not all) banners
	- writes regular messages to the last spawned Moulti step
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super().__init__(*args, **kwargs)
		self.step_counter = 0
		self.current_step: str|None = None
		self.current_type: str|None = None
		self.start_time = datetime.now()
		self.pipes: dict[str, sp.Popen|None] = {}
		if 'MOULTI_ANSIBLE_NO_TITLE' not in os.environ:
			self.set_title_from_command_line()
		self.is_task: bool = False
		self.task_class: str|None = None
		self.task_class_priority: int = -1
		# Hijack sys.stdout and sys.stderr to harvest as much output as possible:
		sys.stdout = sys.stderr = self

	def __del__(self) -> None:
		# Close the last remaining pipe, if any:
		self.close_current_pipe()

	def moulti(self, args: list[str], **sp_args: Any) -> sp.CompletedProcess:
		return sp.run(['moulti'] + args, shell=False, check=True, **sp_args)

	def set_title_from_command_line(self) -> None:
		simplified_args = []
		for arg in sys.argv:
			if arg.startswith('/'):
				arg = Path(arg).name
			simplified_args.append(arg)
		self.set_title(' '.join(simplified_args))

	def set_title(self, title: str) -> None:
		self.moulti(['set', '--title', title])

	def new_step_id(self) -> str:
		step_id = f'ansible_{os.getpid()}_{self.step_counter}'
		self.step_counter += 1
		return step_id

	def new_widget(self, widget_type: str, title: str, classes: str, *args: str) -> str:
		self.tidy()
		widget_id = self.new_step_id()
		all_classes = 'ansible ' + classes
		final_title = escape_rich_tags(title)
		moulti_args = [widget_type, 'add', widget_id, '--title', final_title, '--classes', all_classes]
		for one_class in classes.split():
			if one_class in COLLAPSE:
				moulti_args += ['--collapsed']
				break
		moulti_args += ['--scroll-on-activity=-1']
		moulti_args += [*args]
		self.moulti(moulti_args)
		self.current_step = widget_id
		self.current_type = widget_type
		return widget_id

	def new_playbook(self, title: str) -> str:
		return self.new_widget('divider', f'PLAYBOOK: {title}', 'ansible_playbook')

	def new_play(self, title: str) -> str:
		return self.new_widget('divider', f'PLAY: {title}', 'ansible_play')

	def date_time(self, date: datetime|None = None) -> str:
		date = datetime.now() if date is None else date
		return date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] # milliseconds, not microseconds

	def duration(self, start_date: datetime, end_date: datetime) -> str:
		duration = end_date - start_date
		duration_parts = str(duration).split('.')
		return f'{duration_parts[0]}.{duration_parts[1][:3]}' # milliseconds, not microseconds

	def new_task(self, title: str) -> str:
		task_id = self.new_widget('step', f'{title}', 'ansible_task', '--bottom-text', ' ')
		self.start_time = datetime.now()
		self.moulti(['step', 'update', task_id, '--top-text', f'Started {self.date_time(self.start_time)}'])
		self.is_task = True
		self.task_class = None
		self.task_class_priority = -1
		return task_id

	def new_recap(self, title: str) -> str:
		return self.new_widget('step', f'{title}', 'ansible_recap', '--bottom-text', ' ')

	def tidy(self) -> None:
		date_time = datetime.now()
		self.close_current_pipe()
		if self.current_step and self.is_task:
			duration = self.duration(self.start_time, date_time)
			args = ['--bottom-text', f'Finished {self.date_time(date_time)} - duration: {duration}']
			# Color the previous task green if needed:
			if not self.task_class:
				args += ['--classes', 'ansible ansible_task success']
			self.moulti(['step', 'update', self.current_step, *args])
		self.is_task = False
		self.task_class = None

	def open_pipe(self, step_id: str) -> sp.Popen:
		# pylint: disable=consider-using-with
		pipe = sp.Popen(['moulti', 'pass', step_id], stdin=sp.PIPE, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
		self.pipes[step_id] = pipe
		return pipe

	def get_pipe(self, step_id: str) -> sp.Popen:
		pipe = self.pipes.get(step_id)
		return self.open_pipe(step_id) if pipe is None else pipe

	def close_pipe(self, step_id: str) -> None:
		pipe = self.pipes.get(step_id)
		if pipe is not None:
			pipe.stdin.close() # type: ignore
			self.pipes[step_id] = None
			pipe.wait()

	def close_current_pipe(self) -> None:
		if self.current_step:
			self.close_pipe(self.current_step)

	def do_write(self, step_id: str, msg: str) -> None:
		pipe = self.get_pipe(step_id)
		data = msg
		if not data.endswith('\n'):
			data += '\n'
		pipe.stdin.write(data.encode('utf-8')) # type: ignore
		pipe.stdin.flush() # type: ignore

	@proxy_display
	def display(self, msg: str, color: str | None = None, stderr: bool = False, screen_only: bool = False,
		log_only: bool = False, newline: bool = True, **kwargs: Any
	) -> None:
		_ = stderr
		if log_only or not screen_only:
			super().display(msg=msg, color=color, stderr=False, screen_only=False, log_only=True, newline=newline,
				**kwargs)

		if screen_only or not log_only:
			if not msg:
				return
			task_class, priority = None, -1
			if color is not None:
				color_code = parsecolor(color)
				msg = '\n'.join([f'\033[{color_code}m{t}\033[0m' for t in msg.split('\n')])
				if color in ('red', 'bright red'):
					task_class, priority = 'error', 10
				elif color in ('yellow', 'bright yellow'):
					task_class, priority = 'warning', 5
				elif color in ('green', 'bright green'):
					task_class, priority = 'success', 3
				elif color in ('cyan', 'bright cyan'): # "skipping" and "included" lines
					task_class, priority = 'inactive', 0
			step_id = self.write(msg)
			if task_class is not None and task_class != self.task_class and priority > self.task_class_priority:
				self.task_class = task_class
				self.task_class_priority = priority
				self.moulti(['step', 'update', step_id, '--classes', 'ansible ansible_task ' + self.task_class])

	def banner(self, msg: str, color: str | None = None, _cows: bool = True) -> None:
		if msg.startswith('TASK'):
			self.new_task(f'TASK: {msg[6:-1]}')
		elif msg.startswith('PLAY RECAP'):
			self.new_recap(msg)
		elif msg.startswith('PLAYBOOK'):
			self.new_playbook(msg[10:])
		elif msg.startswith('PLAY'):
			self.new_play(msg[6:-1])
		else:
			super().banner(msg, color, cows=False)

	def write(self, data: str) -> str:
		if self.current_step and self.current_type == 'step':
			step_id = self.current_step
		else:
			step_id = self.new_task('Ansible standard output')
		self.do_write(step_id, data)
		return step_id

	def flush(self) -> None:
		pass

	def close(self) -> None:
		pass

	def get_answer(self, inputquestion_id: str, default: str | None = None) -> str:
		cpe = self.moulti(['inputquestion', 'get-answer', '--wait', inputquestion_id], capture_output=True)
		answer = cpe.stdout.decode('utf-8', errors='surrogate_or_strict').rstrip('\n')
		if not answer and default is not None:
			answer = default
		return answer

	def simple_prompt(self, msg: str, *args: Any, private: bool = False, default: str | None = None) -> Answer:
		cmd_args = list(args)
		if private:
			cmd_args.append('--password')
		if default is not None and not private:
			cmd_args.append(f'--bottom-text=Default value: {default}')
		question_id = self.new_widget('inputquestion', msg, 'ansible_prompt warning', *cmd_args)
		self.moulti(['scroll', question_id, '-1'])
		answer = self.get_answer(question_id, default)
		return (answer, [question_id])

	def confirm_prompt(self, msg: str, *args: Any, private: bool = False, default: str | None = None) -> Answer:
		widgets = []
		confirm = '--top-text=Please enter the value again to confirm:'
		mismatch = '--top-text=[bold]Values entered do not match[/]'
		while True:
			answer1, id1 = self.simple_prompt(msg, *args, private=private, default=default)
			answer2, id2 = self.simple_prompt(msg, *args, confirm, private=private, default=default)
			widgets.extend(id1)
			widgets.extend(id2)
			if answer1 == answer2:
				return (answer1, widgets)
			for widget_id in (id1[0], id2[0]):
				self.moulti(['inputquestion', 'update', '--classes=ansible_prompt error', mismatch, widget_id])

	def prompt(self, msg: str, private: bool = False, default: str | None = None) -> str:
		return self.simple_prompt(msg, private=private, default=default)[0]

	def do_var_prompt(
		self,
		varname: str,
		private: bool = True,
		prompt: str | None = None,
		encrypt: str | None = None,
		confirm: bool = False,
		salt_size: int | None = None,
		salt: str | None = None,
		default: str | None = None,
		unsafe: bool = False,
	) -> str:
		do_prompt = self.confirm_prompt if confirm else self.simple_prompt
		msg = prompt if prompt is not None and prompt != varname else f'Input for {varname}?'
		result, _widgets = do_prompt(msg, private=private, default=default)

		if encrypt:
			# Circular import because encrypt needs a display class
			from ansible.utils.encrypt import do_encrypt # type: ignore # pylint: disable=import-outside-toplevel
			result = do_encrypt(result, encrypt, salt_size=salt_size, salt=salt)
		if unsafe:
			result = wrap_var(result)

		return result

	def byte_to_text(self, byte: bytes) -> str:
		try:
			return byte.decode().upper()
		except UnicodeDecodeError:
			return str(byte)

	def prompt_until(
		self,
		msg: str,
		private: bool = False,
		seconds: int | None = None,
		interrupt_input: c.Container[bytes] | None = None,
		complete_input: c.Container[bytes] | None = None,
	) -> bytes:
		cmd_args = []
		if private:
			cmd_args.append('--password')
		if complete_input is not None and hasattr(complete_input, '__iter__'):
			for key in complete_input:
				key_text = self.byte_to_text(key)
				cmd_args += ['--button', '{input}', 'success', key_text]
		else:
			cmd_args += ['--button', '{input}', 'success', 'Enter']

		if interrupt_input is not None and hasattr(interrupt_input, '__iter__'):
			for key in interrupt_input:
				key_text = self.byte_to_text(key)
				cmd_args += ['--button', ':interrupt:', 'error', key_text]
		else:
			cmd_args += ['--button', ':interrupt:', 'error', 'Interrupt']

		question_id = self.new_widget('question', msg, 'ansible_prompt warning', *cmd_args)
		self.moulti(['scroll', question_id, '-1'])

		command = ['question', 'get-answer', '--wait', question_id]
		try:
			cpe = self.moulti(command, capture_output=True, timeout=seconds)
			answer = cpe.stdout.rstrip(b'\n')
		except sp.TimeoutExpired:
			return b''
		if answer == b':interrupt:':
			raise AnsiblePromptInterrupt('user interrupt')
		return answer

class CallbackModule(DefaultCallbackModule):
	"""
	Same as Ansible's default callback module, with a "MoultiDisplay" instead of a regular Display.
	"""
	CALLBACK_VERSION = 1.0
	CALLBACK_TYPE = 'stdout'
	CALLBACK_NAME = 'moulti'

	def __init__(self) -> None:
		super().__init__()
		# Get a reference to the original Display singleton that was initialized before this file was even loaded:
		original_display = Display()
		# Replace it with our own Display:
		self._display: Display = MoultiDisplay(verbosity=original_display.verbosity)
		# But various other parts of Ansible kept a reference to the original Display singleton.
		# Hijack its do_var_prompt() method (+prompt(), just in case) to handle vars_prompt:
		original_display.do_var_prompt = self._display.do_var_prompt
		original_display.prompt = self._display.prompt
		original_display.prompt_until = self._display.prompt_until

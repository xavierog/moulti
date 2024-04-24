from __future__ import annotations
import os
import sys
import subprocess as sp
from datetime import datetime
from pathlib import Path
from typing import Any
# pylint: disable=import-error
from ansible.utils.color import parsecolor # type: ignore
from ansible.utils.display import proxy_display, Display # type: ignore
from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule # type: ignore

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
		self.start_time = datetime.now()
		self.pipes: dict[str, sp.Popen|None] = {}
		if 'MOULTI_ANSIBLE_NO_TITLE' not in os.environ:
			self.set_title_from_command_line()
		self.is_task: bool = False
		self.task_class: str|None = None
		# Hijack sys.stdout and sys.stderr to harvest as much output as possible:
		sys.stdout = sys.stderr = self

	def __del__(self) -> None:
		# Close the last remaining pipe, if any:
		self.close_current_pipe()

	def moulti(self, args: list[str]) -> sp.CompletedProcess:
		return sp.run(['moulti'] + args, shell=False, check=True)

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
		moulti_args += ['--scroll-on-activity=-1']
		moulti_args += [*args]
		self.moulti(moulti_args)
		self.current_step = widget_id
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
		task_id = self.new_widget('step', f'TASK: {title}', 'ansible_task', '--bottom-text', ' ')
		self.start_time = datetime.now()
		self.moulti(['step', 'update', task_id, '--top-text', f'Started {self.date_time(self.start_time)}'])
		self.is_task = True
		self.task_class = None
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
		log_only: bool = False, newline: bool = True,
	) -> None:
		_ = stderr
		if log_only or not screen_only:
			super().display(msg, color, False, False, True, newline)

		if screen_only or not log_only:
			if not msg:
				return
			if color is not None:
				color_code = parsecolor(color)
				msg = '\n'.join([f'\033[{color_code}m{t}\033[0m' for t in msg.split('\n')])
			step_id = self.write(msg)
			if self.task_class != 'error':
				task_class = None
				if color in ('red', 'bright red'):
					task_class = 'error'
				elif color in ('yellow', 'bright yellow'):
					task_class = 'warning'
				if task_class is not None and task_class != self.task_class:
					self.task_class = task_class
					self.moulti(['step', 'update', step_id, '--classes', 'ansible ansible_task ' + self.task_class])

	def banner(self, msg: str, color: str | None = None, _cows: bool = True) -> None:
		if msg.startswith('TASK'):
			self.new_task(msg[6:-1])
		elif msg.startswith('PLAY RECAP'):
			self.new_recap(msg)
		elif msg.startswith('PLAYBOOK'):
			self.new_playbook(msg[10:])
		elif msg.startswith('PLAY'):
			self.new_play(msg[6:-1])
		else:
			super().banner(msg, color, cows=False)

	def write(self, data: str) -> str:
		step_id = self.current_step or self.new_task('Pre-task output')
		self.do_write(step_id, data)
		return step_id

	def flush(self) -> None:
		pass

	def close(self) -> None:
		pass

class CallbackModule(DefaultCallbackModule):
	"""
	Same as Ansible's default callback module, with a "MoultiDisplay" instead of a regular Display.
	"""
	CALLBACK_VERSION = 1.0
	CALLBACK_TYPE = 'stdout'
	CALLBACK_NAME = 'moulti'

	def __init__(self) -> None:
		super().__init__()
		self._display: Display = MoultiDisplay(verbosity=self._display.verbosity)

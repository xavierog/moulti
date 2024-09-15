import os
import re
import sys
import subprocess
from io import StringIO
from typing import Any, Generator
from unidiff import PatchSet # type: ignore
from .pipeline import pipeline

ANSI_GREEN = '\x1b[0;32m' # ANSI green bold is hard to read on light backgrounds
ANSI_RED_BOLD = '\x1b[1;31m'
ANSI_RESET = '\x1b[0m'
DIFF_FIRST_LINE_RE = r'^(?:diff|index|\-\-\-|\+\+\+|Binary files)\s'
ENCODING = os.environ.get('MOULTI_DIFF_ENCODING', 'utf-8')

def separate_header_and_data(filedesc: Any) -> tuple[str, str]:
	"""
	unidiff discards all lines above the first file/hunk.
	"""
	header = []
	diff_data = ''
	while line := filedesc.readline():
		if re.search(DIFF_FIRST_LINE_RE, line):
			diff_data = line + filedesc.read()
			break
		header.append(line)
	return ''.join(header), diff_data

def colorize_hunk(hunk: str, strip_first_line: bool = True) -> str:
	lines = []
	for line_num, line in enumerate(hunk.split('\n')):
		if not line_num and strip_first_line:
			continue
		color = None
		if line.startswith('+'):
			color = ANSI_GREEN
		elif line.startswith('-'):
			color = ANSI_RED_BOLD
		if color:
			line = color + line + ANSI_RESET
		lines.append(line)
	return '\n'.join(lines)

def commands(title: str, header: str, diff: PatchSet) -> Generator:
	"""
	Yield pipeline()-compatible triplets.
	"""
	if 'MOULTI_DIFF_NO_TITLE' not in os.environ:
		yield None, {'command': 'set', 'title': title}, None

	delta_lines: list[str] = []
	if 'MOULTI_DIFF_NO_DELTA' not in os.environ:
		try:
			delta = ['delta', '--color-only']
			diff_s = str(diff)
			delta_output = subprocess.check_output(delta, input=diff_s, encoding=ENCODING, errors='surrogateescape')
			delta_lines = delta_output.splitlines()
		except Exception:
			pass

	print_steps = bool(os.environ.get('MOULTI_DIFF_VERBOSE'))
	pid = os.getpid()
	counter = {'step': 1}
	def step(cmd: str, title: str, **kwargs: Any) -> tuple[str, dict, None]:
		step_id = f'diff_{pid}_{counter["step"]}'
		counter['step'] += 1
		step = {'command': cmd, 'action': 'add', 'id': step_id, 'title': title, 'classes': 'diff', **kwargs}
		if print_steps:
			print(f'{cmd} {step_id}')
		return step_id, step, None

	if header:
		yield step('step', 'Header', text=header, bottom_text=' ', collapsed=False)
	for file in diff:
		# One divider per file:
		step_id, divider, fd = step('divider', file.path)

		if file.is_rename:
			source_file = file.source_file
			if file.source_file.startswith('a/') and file.target_file.startswith('b/'):
				source_file = source_file[2:]
			divider['title'] = f'renamed: {source_file} -> {file.path}'
			divider['classes'] += ' warning'
		elif file.is_removed_file:
			divider['title'] = f'removed: {file.path}'
			divider['classes'] += ' error'
		elif file.is_added_file:
			divider['title'] = f'added: {file.path}'
			divider['classes'] += ' success'

		if file.is_binary_file:
			divider['title'] += ' (binary)'

		yield step_id, divider, fd

		for hunk in file:
			# One step per hunk:
			source = f'{hunk.source_start},{hunk.source_length}'
			target = f'{hunk.target_start},{hunk.target_length}'
			# Green and pink colors with a 7.3 contrast ratio, assuming background color #004578:
			stats = f'[#00FF66]+{hunk.added}[/][#FFD0EB]-{hunk.removed}[/]'
			title = f' [yellow1]@@ {source} {target} @@[/] {stats} [gray]{hunk.section_header}[/]'
			if delta_lines:
				hunk_first_line = hunk[0].diff_line_no
				hunk_last_line = hunk[-1].diff_line_no
				text = '\n'.join(delta_lines[hunk_first_line-1:hunk_last_line])
			else:
				text = colorize_hunk(str(hunk), True)
			yield step('step', title, text=text, bottom_text=' ', collapsed=False, max_height=0)

def handle_diff_from_file_descriptor(title: str, filedesc: Any) -> None:
	header, diff_data = separate_header_and_data(filedesc)
	diff = PatchSet.from_string(diff_data)
	pipeline(commands(title, header, diff))

def handle_diff_from_string(title: str, data: str) -> None:
	handle_diff_from_file_descriptor(title, StringIO(data))

def diff_parse(args: dict) -> None:
	filepath = args['diff_filepath']
	with open(filepath, 'r', encoding=ENCODING, errors='surrogateescape') as filedesc:
		title = f'{filepath}'
		handle_diff_from_file_descriptor(title, filedesc)

def diff_run(args: dict) -> None:
	command = args['command']
	res = subprocess.run(command, check=False, stdout=subprocess.PIPE, encoding=ENCODING, errors='surrogateescape')
	if res.stdout:
		title = ' '.join(command)
		handle_diff_from_string(title, res.stdout)
	if res.returncode and not res.stdout:
		sys.stderr.write(f'diff_run: {command} produced no output and exited with status {res.returncode}\n')
		sys.exit(res.returncode)
	sys.exit(0)

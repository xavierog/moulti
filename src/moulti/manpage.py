import os
import re
import sys
import subprocess
from io import StringIO
from typing import Any, Generator
from rich.text import Text
from .pipeline import pipeline

ENCODING = os.environ.get('MOULTI_MANPAGE_ENCODING', 'utf-8')

def overtype_to_ansi(content: str) -> str:
	"""
	Under *BSD and macOS, man pages are formatted using overtypes, like an
	actual teleprinter would do.
	Rich/Textual handle ANSI escape sequences but not overtypes.
	"""
	# character, backspace, character = bold character
	content = re.sub(r'(.)\x08\1', '\x1b[1m\\1\x1b[0m', content)
	# underscore, backspace, character = underlined character
	content = re.sub(r'_\x08(.)', '\x1b[4m\\1\x1b[24m', content)
	return content

def dissect_manpage(filedesc: Any) -> dict:
	title = ''
	while line := filedesc.readline():
		line = line.strip('\n')
		if line:
			title = overtype_to_ansi(line)
			break
	all_lines = [overtype_to_ansi(line) for line in filedesc.readlines()]
	footer = all_lines.pop().strip('\n')

	sections: list[dict] = []
	current_section = {'title': '', 'text': ''}

	def add_section(section: dict[str, str]) -> None:
		section['text'] = section['text'].strip('\n')
		if section['title'] or section['text']:
			sections.append(section)

	for line in all_lines:
		if line.startswith(' ') or line == '\n': # regular line
			current_section['text'] += line
		else: # section title
			add_section(current_section)
			current_section = {'title': line.strip('\n'), 'text': ''}
	add_section(current_section) # Handle the last section

	return {
		'title': title,
		'sections': sections,
		'footer': footer,
	}

def line_indent_size(line: str) -> int:
	size = 0
	for char in line:
		if char != ' ':
			break
		size += 1
	return size

def section_indent_size(text: str) -> int|None:
	size = None
	for line in text.split('\n'):
		if not line:
			continue
		lis = line_indent_size(line)
		if size is None or lis < size:
			size = lis
	return size

def unindent(text: str, max_size: int = -1) -> str:
	size = section_indent_size(text)
	if size is None:
		return text
	if max_size >= 0:
		size = min(size, max_size)
	result = []
	for line in text.split('\n'):
		if line:
			line = line[size:]
		result.append(line)
	return '\n'.join(result)

def ansi_to_markup(text: str) -> str:
	return Text.from_ansi(text).markup

def commands(title: str, manpage: dict) -> Generator:
	"""
	Yield pipeline()-compatible triplets.
	"""
	if 'MOULTI_MANPAGE_NO_TITLE' not in os.environ:
		yield None, {'command': 'set', 'title': title}, None

	print_steps = bool(os.environ.get('MOULTI_MANPAGE_VERBOSE'))
	pid = os.getpid()
	counter = {'step': 1}
	def step(cmd: str, title: str, **kwargs: Any) -> tuple[str, dict, None]:
		step_id = f'manpage_{pid}_{counter["step"]}'
		counter['step'] += 1
		step = {'command': cmd, 'action': 'add', 'id': step_id, 'title': title, 'classes': 'manpage', **kwargs}
		if print_steps:
			print(f'{cmd} {step_id}')
		return step_id, step, None

	yield step('divider', ansi_to_markup(manpage['title']), classes='manpage title')
	max_unindent = 3
	for section in manpage['sections']:
		text = unindent(section['text'], max_unindent)
		yield step('step', ansi_to_markup(section['title']), text=text, collapsed=False, max_height=0)
	yield step('divider', ansi_to_markup(manpage['footer']), classes='manpage footer')

def handle_manpage_from_file_descriptor(title: str, filedesc: Any) -> None:
	pipeline(commands(title, dissect_manpage(filedesc)))

def handle_manpage_from_string(title: str, data: str) -> None:
	handle_manpage_from_file_descriptor(title, StringIO(data))

def manpage_parse(args: dict) -> None:
	filepath = args['manpage_filepath']
	with open(filepath, 'r', encoding=ENCODING, errors='surrogateescape') as filedesc:
		title = f'{filepath}'
		handle_manpage_from_file_descriptor(title, filedesc)

def manpage_run(args: dict) -> None:
	command = args['command']
	os.environ['MAN_KEEP_FORMATTING'] = 'y'
	res = subprocess.run(command, check=False, stdout=subprocess.PIPE, encoding=ENCODING, errors='surrogateescape')
	if res.stdout:
		title = ' '.join(command)
		handle_manpage_from_string(title, res.stdout)
	if res.returncode and not res.stdout:
		sys.stderr.write(f'manpage_run: {command} produced no output and exited with status {res.returncode}\n')
		sys.exit(res.returncode)
	sys.exit(0)

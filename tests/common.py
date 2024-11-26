import os
from glob import glob
from pathlib import Path
from typing import Awaitable, Callable, Iterable
from uuid import uuid4
import pytest
from _pytest.fixtures import FixtureRequest
from textual.pilot import Pilot
from moulti.app import Moulti

TERMINAL_SIZE = (128, 36)
COMMAND_PREFIX = 'tests/scripts/'

async def wait_script_start(pilot):
	"""Wait until the script starts."""
	while pilot.app.init_command_running is None:
		await pilot.pause(0.1)

async def wait_script_end(pilot):
	"""Wait until the script finishes, assuming it has started already."""
	while pilot.app.init_command_running:
		await pilot.pause(0.1)

async def wait_script(pilot):
	"""Wait until the script finishes."""
	await wait_script_start(pilot)
	await wait_script_end(pilot)

@pytest.fixture
def moulti_test(request: FixtureRequest, snap_compare):
	"""
	Helper fixture that wraps around Textual's snap_compare. It takes care of:
	- setting THE terminal size;
	- picking a non-conflicting Moulti instance name, with optional suffix;
	- creating a Moulti instance;
	- passing an optional command;
	- taking a snapshot through snap_compare;
	- exiting the Moulti instance so it stops listening;
	- returning snap_compare's result.
	press, run_before and terminal_size are the same as snap_compare's.
	If a command is passed, run_before defaults to wait_script, so that the snapshot is not taken prematurely.
	"""
	def compare(
		command: list[str]|None = None,
		press: Iterable[str] = (),
		run_before: Callable[[Pilot], Awaitable[None]|None]|None = None,
		run_after: Callable|None = None,
		terminal_size: tuple[int, int] = TERMINAL_SIZE,
		suffix: str|None = None,
	):
		name = request.node.reportinfo()[2].replace('_', '-')
		if suffix is not None:
			name += suffix
		if command:
			if command[0] != 'moulti' and not command[0].startswith(COMMAND_PREFIX):
				command[0] = COMMAND_PREFIX + command[0]
			if not run_before:
				run_before = wait_script
		moulti_app = Moulti(command=command, instance_name=f'{os.getpid()}-{name}')
		result = snap_compare(moulti_app, press, terminal_size, run_before)
		if run_after:
			run_after(moulti_app)
		else:
			moulti_app.exit()
		return result
	return compare

def steps(max_step):
	"""
	Helper that iterates from 1 to max_step (inclusive) and yields
	integer-string-suffix tuples, e.g. (2, '2', '-02').
	"""
	for index in range(1, max_step+1):
		yield (index, str(index), f'-{index:02d}')

def moulti_test_steps(moulti_test, script_path, max_step):
	"""
	Helper that runs a script through moulti_test max_step times in a row.
	"""
	for _, i, suffix in steps(max_step):
		assert moulti_test(command=[script_path, i], suffix=suffix)


class Beacon:
	"""
	A beacon is a file-based semaphore used to synchronize a Moulti-driving
	shell script and a Moulti-driving Textual Pilot.
	"""
	def __init__(self, monkeypatch = None):
		self._path = f'/tmp/{uuid4()}'
		if monkeypatch is not None:
			monkeypatch.setenv('MOULTI_TEST_BEACON', self._path)

	def __exit__(self):
		if not self._path:
			return
		for filepath in glob(f'{self._path}*'):
			os.unlink(filepath)

	def path(self, suffix=''):
		return Path(f'{self._path}{suffix}')

	def light(self, suffix=''):
		self.path(suffix).touch()

	def clear(self, suffix=''):
		self.path(suffix).unlink()

	def lit(self, suffix=''):
		return self.path(suffix).exists()

	async def wait(self, pilot, suffix='', pause_interval=0.1):
		path = self.path(suffix)
		while not path.exists():
			await pilot.pause(pause_interval)

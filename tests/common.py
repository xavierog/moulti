import os
from typing import Awaitable, Callable, Iterable
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

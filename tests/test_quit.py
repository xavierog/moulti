from os.path import exists as path_exists
from time import sleep
from uuid import uuid4
from .common import moulti_test, wait_script_start
assert moulti_test

def moulti_test_child_beacon(moulti_test, expectation):
	alive_path = f'/tmp/{uuid4()}'

	async def wait_for_child_beacon(pilot):
		await wait_script_start(pilot)
		while not path_exists(alive_path):
			await pilot.pause(0.1)

	def check_child_beacon(moulti_app):
		# Moulti must have exited:
		assert moulti_app.return_code == 0
		sleep(1)
		# The child process must have been terminated:
		assert path_exists(alive_path) == expectation

	assert moulti_test(
		command=['sleep.bash', '10', alive_path],
		run_before=wait_for_child_beacon,
		press='q',
		run_after=check_child_beacon
	)

def test_quit_default_ask(moulti_test, monkeypatch):
	monkeypatch.setenv('MOULTI_QUIT_POLICY', 'default=ask')
	assert moulti_test(press='q')

def test_quit_default_quit(moulti_test, monkeypatch):
	monkeypatch.setenv('MOULTI_QUIT_POLICY', 'default=quit')
	def run_after(moulti_app):
		assert moulti_app.return_code == 0
	assert moulti_test(press=('q'), run_after=run_after)

def test_quit_running_ask(moulti_test, monkeypatch):
	monkeypatch.setenv('MOULTI_QUIT_POLICY', 'running=ask')
	assert moulti_test(command=['sleep.bash', '1'], run_before=wait_script_start, press='q')

def test_quit_running_terminate(moulti_test, monkeypatch):
	monkeypatch.setenv('MOULTI_QUIT_POLICY', 'running=terminate')
	moulti_test_child_beacon(moulti_test, False)

def test_quit_running_leave(moulti_test, monkeypatch):
	monkeypatch.setenv('MOULTI_QUIT_POLICY', 'running=leave')
	moulti_test_child_beacon(moulti_test, True)

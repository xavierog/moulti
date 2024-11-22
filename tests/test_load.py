from filecmp import cmpfiles
from pathlib import Path
from os import listdir, getpid
from tempfile import TemporaryDirectory
from moulti.app import Moulti
from .common import moulti_test, wait_script
assert moulti_test

LOAD_DIR = 'tests/data/social-preview'
LOAD_COMMAND = ['moulti', 'load', LOAD_DIR]

def test_load(moulti_test):
	assert moulti_test(command=LOAD_COMMAND)

async def test_save(monkeypatch):
	"""
	Load the same directory as test_load, save it to a temporary directory then
	compare the resulting files against the original ones.
	"""
	with TemporaryDirectory() as working_directory:
		monkeypatch.setenv('MOULTI_SAVE_PATH', working_directory)
		moulti_app = Moulti(command=LOAD_COMMAND, instance_name=f'{getpid()}-test-save')
		async with moulti_app.run_test() as pilot:
			await wait_script(pilot) # wait until everything is loaded
			await pilot.press('s') # save
			await pilot.pause(.5) # enough time to do the job
			await pilot.press('q') # quit
		save_directory = Path(working_directory) / listdir(working_directory)[0]
		# The save directory should contain the exact same files as the load directory:
		save_files = sorted(listdir(save_directory))
		assert save_files == sorted(listdir(LOAD_DIR))
		assert cmpfiles(save_directory, LOAD_DIR, save_files)

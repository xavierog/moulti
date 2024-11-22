from shutil import which
from .common import moulti_test
assert moulti_test

COMMAND = ['diff.bash']

def test_diff_no_delta(moulti_test, monkeypatch):
	monkeypatch.setenv('MOULTI_DIFF_NO_DELTA', 'yes')
	assert moulti_test(command=COMMAND)

if which('delta'):
	def test_diff_with_delta(moulti_test):
		assert moulti_test(command=COMMAND)

from .common import moulti_test
assert moulti_test

def do_test(moulti_test, monkeypatch, value, extra_args = None):
	monkeypatch.setenv('MOULTI_RUN_OUTPUT', value)
	command = ['run-output.bash']
	if extra_args is not None:
		command += extra_args
	assert moulti_test(command=command)

def test_discard_output(moulti_test, monkeypatch):
	do_test(moulti_test, monkeypatch, 'discard')

def test_harvest_output(moulti_test, monkeypatch):
	do_test(moulti_test, monkeypatch, 'harvest')

def test_custom_step(moulti_test, monkeypatch):
	do_test(moulti_test, monkeypatch, 'harvest', ['--create-step'])

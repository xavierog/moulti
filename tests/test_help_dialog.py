from .common import moulti_test
assert moulti_test

def test_help_dialog(moulti_test):
	assert moulti_test(press='h')

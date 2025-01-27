from .common import moulti_test
assert moulti_test

def test_pass_empty_file(moulti_test):
	assert moulti_test(command=['pass-empty-file.bash'])

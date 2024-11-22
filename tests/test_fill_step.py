from .common import moulti_test
assert moulti_test

def test_fill_step(moulti_test):
	assert moulti_test(command=['fill-step.bash'])

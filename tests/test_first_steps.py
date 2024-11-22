from .common import moulti_test, moulti_test_steps
assert moulti_test

def test_first_steps(moulti_test):
	"""
	Run all commands taken from the documentation's "First steps with Moulti" section.
	"""
	moulti_test_steps(moulti_test, 'first-steps.bash', 12)

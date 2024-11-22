from .common import moulti_test, moulti_test_steps
assert moulti_test

def test_divider(moulti_test):
	"""
	Run all commands taken from the documentation's "Dividers" section.
	"""
	moulti_test_steps(moulti_test, 'divider.bash', 3)

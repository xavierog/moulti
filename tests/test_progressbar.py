from .common import moulti_test, moulti_test_steps
assert moulti_test

def test_progressbar(moulti_test):
	"""
	Run commands taken from the documentation's "Progress bar" section.
	"""
	moulti_test_steps(moulti_test, 'progressbar.bash', 4)

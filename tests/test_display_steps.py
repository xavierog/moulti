from .common import moulti_test
assert moulti_test

def do_test(moulti_test, position, direction):
	command = ['display-steps.bash', '--step-position', position, '--step-direction', direction]
	assert moulti_test(command=command)

def test_display_steps_top_down(moulti_test):
	do_test(moulti_test, 'top', 'down')

def test_display_steps_top_up(moulti_test):
	do_test(moulti_test, 'top', 'up')

def test_display_steps_bottom_down(moulti_test):
	do_test(moulti_test, 'bottom', 'down')

def test_display_steps_bottom_up(moulti_test):
	do_test(moulti_test, 'bottom', 'up')

from .common import moulti_test
assert moulti_test

COMMAND = ['maximize.bash']

def test_maximize_small_step(moulti_test):
	# Maximize the first step:
	assert moulti_test(command=COMMAND, press=('tab', 'tab', 'f'))

def test_unmaximize_small_step(moulti_test):
	# Maximize then unmaximize the first step:
	assert moulti_test(command=COMMAND, press=('tab', 'tab', 'f', 'f'))

def test_maximize_large_step(moulti_test):
	# Maximize the last step:
	assert moulti_test(command=COMMAND, press=('shift+tab', 'f'))

def test_unmaximize_large_step(moulti_test):
	# Maximize then unmaximize the last step:
	assert moulti_test(command=COMMAND, press=('shift+tab', 'f', 'f'))

def test_search_maximize(moulti_test):
	press = (
		'tab', 'tab', 'f', # maximize the first step
		'/', *r'\b5\b', 'enter', # search it for a standalone '5' character
		'f', # unmaximize it
		'n', # ask for the next result, which is expected in the second step
	)
	assert moulti_test(command=COMMAND, press=press)

def test_search_unmaximize(moulti_test):
	press = (
		'/', *r'\b5\b', 'enter', # search for a standalone '5' character, which is expected in the first step
		'tab', 'tab', 'tab', 'f', # maximize the second step
		'n', # search it for the next result
		'f', # unmaximize it
		'n', # ask for the next result, which is expected in the third step
	)
	assert moulti_test(command=COMMAND, press=press)

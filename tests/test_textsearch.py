from .common import moulti_test
assert moulti_test

COMMAND = ['text-search.bash']

def test_search_bar(moulti_test):
	bad_regex, good_regex = r'[aeiou', r'[aeiou]'
	assert moulti_test(press=('/', *bad_regex)) # Regex + red pattern
	assert moulti_test(press=('/', 'ctrl+r', *bad_regex)) # Plain + white pattern
	assert moulti_test(press=('/', 'ctrl+r', 'ctrl+t', *good_regex)) # PLAIN + white pattern
	assert moulti_test(press=('/', 'ctrl+t', *good_regex)) # REGEX + white pattern

def test_plain_pattern_case_sensitive(moulti_test):
	assert moulti_test(command=COMMAND, press=('/', 'ctrl+r', *'sed', 'enter', 'n')) # second "sed"
	assert moulti_test(command=COMMAND, press=('/', 'ctrl+r', *'sed', 'enter', 'n', 'N')) # first "sed"

def test_plain_pattern_case_insensitive(moulti_test):
	assert moulti_test(command=COMMAND, press=('/', 'ctrl+r', 'ctrl+t', *'sed', 'enter')) # first "Sed"

def test_regex_pattern_case_sensitive(moulti_test):
	assert moulti_test(command=COMMAND, press=('/', *r'\b\w{3}\b', 'enter', 'n', 'n', 'n')) # first "vel"

def test_regex_pattern_case_insensitive(moulti_test):
	assert moulti_test(command=COMMAND, press=('/', *r'\blor[aeiou]m\b', 'ctrl+t', 'enter')) # first "Lorem"

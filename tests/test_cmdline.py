import pytest
from moulti.cli import adjust_cli_args, first_non_option_argument, inject_double_dash_before_command

def test_first_non_option_argument():
	assert first_non_option_argument(['--foo', '-b']) is None
	assert first_non_option_argument(['foo']) == 0
	assert first_non_option_argument(['--foo', '-b', 'bar']) == 2
	assert first_non_option_argument(['moulti', 'run', 'foo'], 2) == 2
	assert first_non_option_argument(['moulti', 'run', '--foo', '-b', 'foo'], 2) == 4

INJECT_DOUBLE_DASH_BEFORE_COMMAND = [
	{
		'args': ['--foo', '-b'],
		'start': 0,
		'result': ['--foo', '-b'],
	},
	{
		'args': ['foo'],
		'start': 0,
		'result': ['foo'],
	},
	{
		'args': ['--foo', '-b', 'bar'],
		'start': 0,
		'result': ['--foo', '-b', '--', 'bar'],
	},
	{
		'args': ['moulti', 'run', 'foo'],
		'start': 2,
		'result': ['moulti', 'run', '--', 'foo'],
	},
	{
		'args': ['moulti', 'run', '--foo', '-b', 'foo'],
		'start': 2,
		'result': ['moulti', 'run', '--foo', '-b', '--', 'foo'],
	},
	{
		'args': ['moulti', 'run', '--foo', '-b', '--', 'foo'],
		'start': 2,
		'result': ['moulti', 'run', '--foo', '-b', '--', 'foo'],
	},
]

@pytest.mark.parametrize('test', INJECT_DOUBLE_DASH_BEFORE_COMMAND)
def test_inject_double_dash_before_command(test):
	inject_double_dash_before_command(test['args'], test['start'])
	assert test['args'] == test['result']

ADJUST_CLI_ARGS = [
	{'args': ['moulti', 'run']},
	{'args': ['moulti', 'run', '--help']},
	{'args': ['moulti', 'run', 'ls'], 'result': ['moulti', 'run', '--', 'ls']},
	{'args': ['moulti', 'run', 'ls', '-al'], 'result': ['moulti', 'run', '--', 'ls', '-al']},
	{
		'args': ['moulti', 'run', 'moulti', 'diff', 'run', 'git', 'diff', '--cached'],
		'result': ['moulti', 'run', '--', 'moulti', 'diff', 'run', 'git', 'diff', '--cached'],
	},
	{
		'args': ['moulti', 'diff', 'run', 'git', 'diff'],
		'result': ['moulti', 'diff', 'run', '--', 'git', 'diff'],
	},
	{
		'args': ['moulti', 'diff', 'run', 'git', 'diff', '--cached'],
		'result': ['moulti', 'diff', 'run', '--', 'git', 'diff', '--cached'],
	},
]

@pytest.mark.parametrize('test', ADJUST_CLI_ARGS)
def test_adjust_cli_args(test):
	expectation = test.get('result') or test['args'].copy()
	adjust_cli_args(test['args'])
	assert test['args'] == expectation

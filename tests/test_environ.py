from moulti.environ import env, enva, envd, pint

def test_env(monkeypatch):
	monkeypatch.delenv('NON_EXISTENT_ENV_VAR', False)
	assert env('NON_EXISTENT_ENV_VAR', 'default') == 'default'

	monkeypatch.setenv('EMPTY', '')
	assert env('EMPTY', 'default') == ''

	monkeypatch.setenv('NAME', 'value')
	assert env('NAME', 'default') == 'value'

	monkeypatch.setenv('INTEGER', '123')
	assert env('INTEGER', -1, [int]) == 123

	monkeypatch.setenv('NON_INTEGER', 'foo')
	assert env('NON_INTEGER', -1, [int]) == -1
	assert env('NON_INTEGER', -1, [int, str]) == 'foo'
	assert env('NON_INTEGER', -1, [str, int]) == 'foo'


def test_enva(monkeypatch):
	monkeypatch.delenv('NON_EXISTENT_ENV_VAR', False)
	assert enva('NON_EXISTENT_ENV_VAR', [1, 2, 3]) == [1, 2, 3]

	monkeypatch.setenv('EMPTY', '')
	assert enva('EMPTY', [1, 2, 3]) == []

	monkeypatch.setenv('INTEGERS', '-2,-1,0,1,2')
	assert enva('INTEGERS', [1, 2, 3]) == ['-2', '-1', '0', '1', '2']

	monkeypatch.setenv('INTEGERS', '-2,-1,0,1,2')
	assert enva('INTEGERS', [1, 2, 3], [int]) == [-2, -1, 0, 1, 2]

	monkeypatch.setenv('INTEGERS', '-2,-1,0,1,2')
	assert enva('INTEGERS', [1, 2, 3], [pint]) == [1, 2, 3]

	monkeypatch.setenv('INTEGERS', '-2,-1,0,1,2')
	assert enva('INTEGERS', [1, 2, 3], [pint], strict=False) == [0, 1, 2]

	monkeypatch.setenv('INTEGERS', '-2,-1,0,1,2')
	assert enva('INTEGERS', [1, 2, 3], [pint, str]) == ['-2', '-1', 0, 1, 2]

	monkeypatch.setenv('INTEGERS', '-2;-1;0;1;2')
	assert enva('INTEGERS', [1, 2, 3], [int], sep=';') == [-2, -1, 0, 1, 2]

	# Separator with multiple characters:
	monkeypatch.setenv('INTEGERS', '-2;;-1;;0;;1;;2')
	assert enva('INTEGERS', [1, 2, 3], [int], sep=';;') == [-2, -1, 0, 1, 2]

	monkeypatch.setenv('INTEGERS', '-2;;-1;;0;;1;2')
	assert enva('INTEGERS', [1, 2, 3], [int], sep=';;') == [1,2,3]

	monkeypatch.setenv('INTEGERS', '-2;;-1;;0;;1;2')
	assert enva('INTEGERS', [1, 2, 3], [int], sep=';;', strict=False) == [-2, -1, 0]

	# Trailing separator:
	monkeypatch.setenv('INTEGERS', '-2;;-1;;0;;1;2;;')
	assert enva('INTEGERS', [1, 2, 3], [int], sep=';;', strict=False) == [-2, -1, 0]

	monkeypatch.setenv('INTEGERS', '-2;;-1;;0;;1;2;;')
	assert enva('INTEGERS', [1, 2, 3], [int], sep=';;', strict=True) == [1, 2, 3]


def test_envd(monkeypatch):
	monkeypatch.delenv('NON_EXISTENT_ENV_VAR', False)
	assert envd('NON_EXISTENT_ENV_VAR', {'a': 'b'}) == {'a': 'b'}

	monkeypatch.setenv('EMPTY', '')
	assert envd('EMPTY', {'a': 'b'}) == {}

	monkeypatch.setenv('INTEGERS', 'a=1,b=2,c=3')
	assert envd('INTEGERS') == {'a': '1', 'b': '2', 'c': '3'}

	monkeypatch.setenv('INTEGERS', 'a=1,b=2,c=3')
	assert envd('INTEGERS', types=[int]) == {'a': 1, 'b': 2, 'c': 3}

	monkeypatch.setenv('INTEGERS', 'a=1,b=2,c=3,d=foo')
	assert envd('INTEGERS', types=[int]) is None

	monkeypatch.setenv('INTEGERS', 'a=1,b=2,c=3,d=foo')
	assert envd('INTEGERS', types=[int], strict=False) == {'a': 1, 'b': 2, 'c': 3}

	monkeypatch.setenv('INTEGERS', 'a=1,b=2,c=3,d=foo=')
	assert envd('INTEGERS', types=[int, str]) == {'a': 1, 'b': 2, 'c': 3, 'd': 'foo='}

	monkeypatch.setenv('INTEGERS', 'a==1,b==2,c==3,d==foo==')
	assert envd('INTEGERS', types=[int, str], sepkv='==') == {'a': 1, 'b': 2, 'c': 3, 'd': 'foo=='}

	monkeypatch.setenv('INTEGERS', 'a=1,b,c=3')
	assert envd('INTEGERS', types=[int], sepkv='==') is None

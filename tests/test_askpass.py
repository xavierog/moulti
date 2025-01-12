from _pytest.fixtures import FixtureRequest
from os import getpid, environ
from asyncio import create_subprocess_exec as async_exec
from asyncio.subprocess import PIPE
import pytest
from moulti.app import Moulti
from .common import moulti_test
assert moulti_test

PASSWORD = 'The secret!'
INPUT_SECRET = ['ctrl+y', *PASSWORD]
INPUT_YES = ['ctrl+y', *'yes']
HIT_1ST_BUTTON = ['ctrl+y']
HIT_2ND_BUTTON = ['ctrl+y', 'tab']
FINGERPRINT_PROMPT = """The authenticity of host '[example.org]:22 ([12.34.56.78]:22)' can't be established.
ED25519 key fingerprint is SHA256:s2DYbBHs784Xe7/LvXCybJe6ncu+x2Dn9mxLwXQ+TfM.
Are you sure you want to continue connecting (yes/no/[fingerprint])?"""

TESTS = [
	{'cmd': ['moulti-askpass']},
	{'cmd': ['moulti-askpass'], 'env': {'MOULTI_ASKPASS_DEFAULT_PROMPT': 'Env-based custom prompt?'}},
	{'cmd': ['moulti-askpass-become-password']},
	{'cmd': ['moulti-askpass-connection-password']},
	{'cmd': ['moulti-askpass-vault-client']},
	{'cmd': ['moulti-askpass', 'Command-line custom prompt?']},
	{'cmd': ['moulti-askpass', '--vault-id', 'SHINY_VAULT']},
	{'cmd': ['moulti-askpass', FINGERPRINT_PROMPT], 'input': INPUT_YES, 'output': 'yes'},
	{'cmd': ['moulti-askpass'], 'env': {'SSH_ASKPASS_PROMPT': 'none'}, 'input': HIT_1ST_BUTTON, 'output': ''},
	{'cmd': ['moulti-askpass'], 'env': {'SSH_ASKPASS_PROMPT': 'confirm'}, 'input': HIT_1ST_BUTTON, 'output': ''},
	{'cmd': ['moulti-askpass'], 'env': {'SSH_ASKPASS_PROMPT': 'confirm'}, 'input': HIT_2ND_BUTTON, 'output': '', 'rc': 1},
]
for index, test in enumerate(TESTS):
	test['index'] = index

@pytest.mark.parametrize('test', TESTS)
def test_askpass_visual(test, moulti_test, monkeypatch):
	"""Visual tests: ensure the askpass step looks like expected."""
	for name, value in test.get('env', {}).items():
		monkeypatch.setenv(name, value)
	async def run_before(pilot):
		await pilot.pause(.5)
		await pilot.press(*test.get('input', INPUT_SECRET))
	assert moulti_test(command=test['cmd'], run_before=run_before)

@pytest.mark.parametrize('test', TESTS)
async def test_askpass_password(test, moulti_test, monkeypatch, request: FixtureRequest):
	"""Functional tests: ensure moulti-askpass returns the right secret and return code."""
	instance_name = f'{getpid()}-askpass-{test["index"]}'
	env = environ | test.get('env', {}) | {'MOULTI_INSTANCE': instance_name}
	moulti_app = Moulti(instance_name=instance_name)
	async with moulti_app.run_test() as pilot:
		proc = await async_exec(*test['cmd'], env=env, stdout=PIPE)
		await pilot.pause(.5)
		await pilot.press(*test.get('input', INPUT_SECRET), 'enter')
		password = await proc.stdout.readline()
		await proc.wait()
		assert proc.returncode == test.get('rc', 0)
		assert password.decode('utf-8').rstrip() == test.get('output', PASSWORD)
		await pilot.press('q')

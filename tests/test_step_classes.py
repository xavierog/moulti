from pathlib import Path
from moulti.app import Moulti
from .common import moulti_test
assert moulti_test

def test_step_classes(moulti_test, monkeypatch):
	css_path = Path('tests/styles/customstate.css').absolute()
	monkeypatch.setattr(Moulti, 'CSS_PATH', str(css_path))
	assert moulti_test(command=['step-classes.bash'])

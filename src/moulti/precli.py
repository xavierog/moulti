"""
This file can be used to run instructions early, before the interpreter tries to import Moulti modules.
"""
# PYTHON_ARGCOMPLETE_OK

import sys
if sys.platform == 'win32':
	WINDOWS_MESSAGE = """It seems you are trying to run moulti on Microsoft Windows.
Alas, as these lines are being written:
- Moulti does not work on this operating system.
- The blocking point is https://github.com/python/cpython/issues/77589

IF this blocking point appears to be resolved, try to upgrade Moulti.
If you are still getting this message, feel free to report this issue.
"""
	print(WINDOWS_MESSAGE)
	sys.exit(1)

from .cli import main # pylint: disable=wrong-import-position; multiple import statements fail on Microsoft Windows
assert bool(main) # main will be called by the console_scripts wrapper; this makes all linters happy.

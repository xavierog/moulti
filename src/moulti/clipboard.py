import os
from textual.app import App
from pyperclip import copy as pyperclip_copy # type: ignore
from pyperclip import PyperclipException

COPY_POLICY = os.environ.get('MOULTI_CLIPBOARD_COPY')

class ClipboardException(Exception):
	pass

def osc_52_copy(app: App, data: str) -> None:
	app.copy_to_clipboard(data)
	# Alas, it is not possible to determine whether this method actually succeeded.

def copy(app: App, data: str) -> None:
	if COPY_POLICY == 'terminal-osc-52':
		osc_52_copy(app, data)
	elif COPY_POLICY == 'pyperclip':
		pyperclip_copy(data)
	else:
		# Default policy: pyperclip with failover to OSC 52:
		try:
			pyperclip_copy(data)
		except PyperclipException as pyperclip_exc:
			try:
				osc_52_copy(app, data)
			except ClipboardException as osc_52_exc:
				# pylint: disable=raise-missing-from
				raise ClipboardException(f'{pyperclip_exc}\nAdditionally, {osc_52_exc}')

import os
from selectors import BaseSelector
from typing import Any
from .environ import env, pint

def abridge_string(value: str, threshold: int = 100, sep: str = '...') -> str:
	"""
	Abridge a string longer than threshold; the result reflects the start middle and end, separated with the given
	separator.
	"""
	if len(value) <= threshold:
		return value
	sep_len = 2 * len(sep) # the abridged string features 3 parts and thus 2 separators
	chars_len = threshold - sep_len
	part_len = chars_len // 3
	delta = chars_len % 3
	middle = int((len(value) / 2) - (part_len / 2))
	return value[:part_len+delta] + sep + value[middle:middle+part_len] + sep + value[-part_len:]

def abridge_dict(message: dict[str, Any], threshold: int = 100, sep: str = '...') -> dict[str, Any]:
	"""
	Abridge the string values of a given dict using abridge_string().
	This function only processes first-level string values and does not work recursively.
	"""
	long_keys = []
	for key, value in message.items():
		if isinstance(value, str) and len(value) > threshold:
			long_keys.append(key)
	if not long_keys:
		return message
	abridged_message = {}
	for key, value in message.items():
		abridged_message[key] = abridge_string(value, threshold, sep) if key in long_keys else value
	return abridged_message

def call_all(calls: list[Any]) -> None:
	for call in calls:
		call[0](*call[1:])

def clean_selector(selector: BaseSelector|None, close_fds: bool = False, close: bool = True) -> None:
	"""
	Clean a Selector object, as offered by the selectors module, by systematically unregistering and optionally
	closing all registered file descriptors then closing the Selector object itself.
	"""
	if not selector:
		return
	for selectorkey in list(selector.get_map().values()):
		selector.unregister(selectorkey.fileobj)
		if close_fds:
			if hasattr(selectorkey.fileobj, 'close'):
				selectorkey.fileobj.close()
			elif isinstance(selectorkey.fileobj, int):
				os.close(selectorkey.fileobj)
	if close:
		selector.close()

DEFAULT_TAB_SIZE = 8

def get_tab_size() -> int:
	return env('MOULTI_TAB_SIZE', DEFAULT_TAB_SIZE, types=(pint,))

TAB_SIZE = get_tab_size()
TAB_SPACES_STR = ' '*TAB_SIZE
TAB_SPACES_BYTES = b' '*TAB_SIZE

ANSI_ESCAPE_SEQUENCE_STR = '\x1b'
ANSI_ESCAPE_SEQUENCE_BYTES = b'\x1b'

ANSI_RESET_SEQUENCES_STR = ('\x1b[0m', '\x1b[m')
ANSI_RESET_SEQUENCES_BYTES = (b'\x1b[0m', b'\x1b[m')

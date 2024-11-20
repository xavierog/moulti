import os
import sys
from selectors import BaseSelector
from typing import Any, cast
from argparse import ArgumentTypeError
from .pipeline import pipeline
from .protocol import Message, send_to_moulti
Args = dict[str, Any]

def pint(value: str) -> int:
	integer_value = int(value)
	if integer_value < 0:
		raise ArgumentTypeError('expected a positive integer')
	return integer_value

def float_str(value: str) -> str:
	_ = float(value)
	return value

def bool_or_int(value: str) -> bool|int:
	if value.lower() == 'false':
		return False
	if value.lower() == 'true':
		return True
	return int(value)

def handle_reply(reply: Message) -> None:
	success = reply.get('done') is True
	if not success:
		fallback = 'alas, no error message was provided.'
		error_message = reply.get('error', fallback)
		sys.stderr.write(f'Something went wrong: {error_message}\n')
	sys.exit(0 if success else 1)

def send_to_moulti_and_handle_reply(message: Message) -> None:
	reply = cast(dict[str, Any], send_to_moulti(message))
	handle_reply(reply)

def send_no_none_to_moulti_and_handle_reply(args: Args) -> None:
	no_none_args = {k:v for (k,v) in args.items() if v is not None}
	send_to_moulti_and_handle_reply(no_none_args)

def send_delete(args: Args) -> None:
	errors = pipeline((step_id, {**args, 'id': step_id}, None) for step_id in args['id'])
	sys.exit(1 if errors else 0)

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
	try:
		return pint(os.environ.get('MOULTI_TAB_SIZE', ''))
	except Exception:
		return DEFAULT_TAB_SIZE

TAB_SIZE = get_tab_size()
TAB_SPACES_STR = ' '*TAB_SIZE
TAB_SPACES_BYTES = b' '*TAB_SIZE

ANSI_ESCAPE_SEQUENCE_STR = '\x1b'
ANSI_ESCAPE_SEQUENCE_BYTES = b'\x1b'

ANSI_RESET_SEQUENCES_STR = ('\x1b[0m', '\x1b[m')
ANSI_RESET_SEQUENCES_BYTES = (b'\x1b[0m', b'\x1b[m')

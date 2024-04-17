import sys
from typing import Any, cast
from argparse import ArgumentTypeError
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

def call_all(calls: list[Any]) -> None:
	for call in calls:
		call[0](*call[1:])

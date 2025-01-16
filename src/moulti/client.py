"""
High-level functions relevant to implement Moulti clients.
"""
import sys
from typing import Any, cast
# Some of the names provided by this module come straight from the pipeline and protocol modules:
# ruff: noqa: F401 imported but unused
# pylint: disable=W0611 unused-import
from .pipeline import pipeline
from .protocol import Message, Socket
from .protocol import moulti_connect, recv_json_message, send_json_message, send_to_moulti
from .protocol import moulti_socket_path, current_instance

Args = dict[str, Any]

def send(socket: Socket, message: Message) -> Message:
	send_json_message(socket, message)
	return recv_json_message(socket, 0)[0]

def handle_reply(reply: Message) -> None:
	success = reply.get('done') is True
	if not success:
		fallback = 'alas, no error message was provided.'
		error_message = reply.get('error', fallback)
		sys.stderr.write(f'Something went wrong: {error_message}\n')
	sys.exit(0 if success else 1)

def send_to_moulti_and_handle_reply(message: Message) -> None:
	reply = cast(Message, send_to_moulti(message))
	handle_reply(reply)

def send_no_none_to_moulti_and_handle_reply(args: Args) -> None:
	no_none_args = {k:v for (k,v) in args.items() if v is not None}
	send_to_moulti_and_handle_reply(no_none_args)

def send_delete(args: Args) -> None:
	errors = pipeline((step_id, {**args, 'id': step_id}, None) for step_id in args['id'])
	sys.exit(1 if errors else 0)

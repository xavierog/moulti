import os
import sys
from typing import Any, Generator
from .protocol import moulti_connect, send_json_message, recv_json_message

def pipeline(messages: Generator, read_size: int = 1024**2) -> int:
	"""
	Pipeline multiple messages to a Moulti instance.
	messages should be a generator that yields triplets:
	- step id (str; None for instance properties)
	- Moulti message to send (dict[str, Any])
	- file descriptor number (int) if it is necessary to pass data, None otherwise
	read_size is used for all "pass" operations.
	Note: so far, this is the only function in Moulti that pipelines messages and replies. Therefore, it is also the
	only function that actually leverages message ids.
	"""
	errors = 0
	sent_messages: dict[str, bool] = {}
	def send_message(*args: Any) -> None:
		msg_id = send_json_message(*args)
		sent_messages[msg_id] = False
	filenos = []
	with moulti_connect() as moulti_socket:
		for step_id, data, fileno in messages:
			# Send all messages using protocol pipelining:
			try:
				# Properties, typically a command that creates and configures a step:
				send_message(moulti_socket, data)
				# Contents:
				if fileno is not None:
					filenos.append(fileno)
					pass_msg = {'command': 'pass', 'id': step_id, 'read_size': read_size}
					send_message(moulti_socket, pass_msg, [fileno])
			except Exception as exc:
				errors += 1
				sys.stderr.write(f'Error with {step_id}/{data}/{fileno}: {exc}\n')
		# Receive replies to all sent messages:
		while not all(sent_messages.values()):
			reply, _ = recv_json_message(moulti_socket, 0)
			if 'msgid' in reply and reply['msgid'] in sent_messages:
				sent_messages[reply['msgid']] = True
				if reply.get('done') is not True:
					errors += 1
					sys.stderr.write(f'Error: {reply.get("error")}\n')
		for fileno in filenos:
			os.close(fileno)
	return errors

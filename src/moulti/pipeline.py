import os
import sys
from threading import Thread
from typing import Any, Generator
from queue import Queue
from .protocol import moulti_connect, send_json_message, recv_json_message, MoultiConnectionClosedException, Message

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
	sender_thread: Queue = Queue()
	receiver_thread = sender_thread
	filenos = []
	sent_messages: dict[str, bool] = {}
	stats = {'errors': 0}
	unexpected_replies = []

	def send_message(*args: Any) -> None:
		msg_id = send_json_message(*args)
		sent_messages[msg_id] = False
		receiver_thread.put_nowait(msg_id)

	def process_reply(reply: Message, store: bool = False) -> bool:
		if 'msgid' in reply:
			if reply['msgid'] in sent_messages:
				sent_messages[reply['msgid']] = True
				if reply.get('done') is not True:
					stats['errors'] += 1
					sys.stderr.write(f'Error: {reply.get("error")}\n')
				return True
		if store:
			unexpected_replies.append(reply)
		return False

	def recheck_unexpected_replies() -> None:
		if unexpected_replies:
			for index in range(len(unexpected_replies) - 1, -1, -1):
				if process_reply(unexpected_replies[index], store=False):
					del unexpected_replies[index]

	with moulti_connect() as moulti_socket:
		# Spawn a thread that receives as many replies as sent messages:
		def recv_messages() -> None:
			try:
				while sender_thread.get() is not None:
					recheck_unexpected_replies()
					reply, _ = recv_json_message(moulti_socket, 0)
					process_reply(reply, store=True)
			except MoultiConnectionClosedException:
				pass
		recv_msg_thread = Thread(target=recv_messages)
		recv_msg_thread.start()

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
				stats['errors'] += 1
				sys.stderr.write(f'Error with {step_id}/{data}/{fileno}: {exc}\n')
		receiver_thread.put_nowait(None)
		recv_msg_thread.join()
		recheck_unexpected_replies()
		for fileno in filenos:
			os.close(fileno)
	return stats['errors']

import os
import re
from struct import calcsize, unpack
from socket import socket as Socket, AF_UNIX, SOCK_STREAM, SOL_SOCKET, SO_PEERCRED, recv_fds, send_fds
import json
from json.decoder import JSONDecodeError
from typing import Any

Message = dict[str, Any]
FDs = list[int]

def from_printable(socket_path: str) -> str:
	if socket_path and socket_path[0] == '@':
		socket_path = '\0' + socket_path[1:]
	return socket_path

def to_printable(socket_path: str) -> str:
	if socket_path and socket_path[0] == '\0':
		socket_path = '@' + socket_path[1:]
	return socket_path


PRINTABLE_MOULTI_SOCKET = os.environ.get('MOULTI_SOCKET_PATH', '@moulti.socket')
MOULTI_SOCKET = from_printable(PRINTABLE_MOULTI_SOCKET)

class MoultiProtocolException(Exception):
	pass

class MoultiConnectionClosedException(Exception):
	def __init__(self, expected_bytes: int = 0):
		self.expected_bytes = expected_bytes
		self.anomaly = True
	def __str__(self) -> str:
		if self.anomaly:
			return f'connection closed by peer while expecting {self.expected_bytes} bytes'
		return 'connection closed by peer'

def moulti_unix_socket() -> Socket:
	return Socket(AF_UNIX, SOCK_STREAM, 0)

def moulti_listen(bind: str = MOULTI_SOCKET, backlog: int = 100, blocking: bool = False) -> Socket:
	try:
		server_socket = moulti_unix_socket()
		server_socket.bind(bind)
		server_socket.listen(backlog)
		server_socket.setblocking(blocking)
		return server_socket
	except Exception as exc:
		err = f'cannot listen on {to_printable(bind)} (with backlog={backlog} and blocking={blocking}): {exc}'
		raise MoultiProtocolException(err) from exc

def get_unix_credentials(socket: Socket) -> tuple[int, int, int]:
	# struct ucred is { pid_t, uid_t, gid_t }
	struct_ucred = '3i'
	unix_credentials = socket.getsockopt(SOL_SOCKET, SO_PEERCRED, calcsize(struct_ucred))
	pid, uid, gid = unpack(struct_ucred, unix_credentials)
	return pid, uid, gid

def moulti_connect(address: str = MOULTI_SOCKET, bind: str | None = None) -> Socket:
	client_socket = moulti_unix_socket()
	client_socket.bind(bind if bind else f'\0moulti-client-{os.getpid()}.socket')
	client_socket.connect(address)
	return client_socket

def read_fixed_amount_from_socket(socket: Socket, amount: int) -> bytes:
	data = bytes()
	if amount <= 0:
		return data
	while amount > 0:
		new_data = socket.recv(amount)
		if not new_data:
			raise MoultiConnectionClosedException(amount)
		data += new_data
		amount -= len(new_data)
	return data

def write_fixed_amount_to_socket(socket: Socket, data: bytes) -> None:
	if not data:
		return
	to_send = len(data)
	sent = 0
	while to_send > 0:
		just_sent = socket.send(data[sent:])
		to_send -= just_sent
		sent += just_sent

def read_tlv_data_from_socket(socket: Socket, max_fds: int = 1) -> tuple[str, bytes, FDs]:
	# This is a simple text-based TLV (type-length-value) protocol.
	# preamble examples: ":JSON:0000000002048:" ":TXT_:0000000002048:"
	preamble_regex = r'^:[A-Z_]{4}:[0-9]{13}:$'
	preamble_fixed_length = 20

	file_descriptors: FDs = []
	if max_fds > 0:
		_, file_descriptors, _, _ = recv_fds(socket, 0, max_fds)

	try:
		preamble = read_fixed_amount_from_socket(socket, preamble_fixed_length).decode('ascii')
	except MoultiConnectionClosedException as mcce:
		mcce.anomaly = mcce.expected_bytes != preamble_fixed_length
		raise mcce
	except UnicodeDecodeError as ude:
		raise MoultiProtocolException('non-ASCII preamble: {str(preamble)}') from ude
	rem = re.match(preamble_regex, preamble)
	if not rem:
		raise MoultiProtocolException(f'invalid preamble: {preamble}')
	data_type = preamble[1:5].rstrip('_')
	if not data_type:
		raise MoultiProtocolException(f'invalid data type: {preamble[1:5]}')
	data_length = int(preamble[6:19])

	return data_type, read_fixed_amount_from_socket(socket, data_length), file_descriptors

def write_tlv_data_to_socket(socket: Socket, data: bytes, data_type: str = 'JSON', fds: FDs|None = None) -> None:
	data_type = data_type + '____'
	data_length = len(data)
	preamble = f':{data_type[0:4]}:{data_length:013}:'.encode('ascii')
	if fds:
		send_fds(socket, [preamble], fds)
	else:
		write_fixed_amount_to_socket(socket, preamble)
	write_fixed_amount_to_socket(socket, data)

def data_to_message(data: bytes) -> Message:
	try:
		string = data.decode('utf-8')
		message = json.loads(string)
		return message
	except UnicodeDecodeError as ude:
		raise MoultiProtocolException(f'received non UTF-8 {len(data)}-byte line') from ude
	except JSONDecodeError as jde:
		raise MoultiProtocolException('received non-JSON message') from jde

def message_to_data(message: Message) -> bytes:
	string = json.dumps(message)
	data = string.encode('utf-8')
	return data

def send_json_message(socket: Socket, message: Message, fds: FDs | None = None) -> None:
	data = message_to_data(message)
	write_tlv_data_to_socket(socket, data, 'JSON', fds)

def recv_json_message(socket: Socket, max_fds: int = 1) -> tuple[Message, FDs]:
	data_type, data, file_descriptors = read_tlv_data_from_socket(socket, max_fds)
	if data_type != 'JSON':
		raise MoultiProtocolException('received non-JSON message')
	return data_to_message(data), file_descriptors

def send_to_moulti(message: Message, wait_for_reply: bool = True) -> Message | None:
	with moulti_connect() as moulti_socket:
		send_json_message(moulti_socket, message)
		if wait_for_reply:
			reply, _ = recv_json_message(moulti_socket, 0)
			return reply
	return None

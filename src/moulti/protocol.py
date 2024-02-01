import os
import re
import socket as socket_module
import json
from json.decoder import JSONDecodeError

def from_printable(socket_path):
	if socket_path and socket_path[0] == '@':
		socket_path = '\0' + socket_path[1:]
	return socket_path

def to_printable(socket_path):
	if socket_path and socket_path[0] == '\0':
		socket_path = '@' + socket_path[1:]
	return socket_path


PRINTABLE_MOULTI_SOCKET = os.environ.get('MOULTI_SOCKET_PATH', '@moulti.socket')
MOULTI_SOCKET = from_printable(PRINTABLE_MOULTI_SOCKET)

class MoultiProtocolException(Exception):
	pass

class MoultiConnectionClosedException(Exception):
	def __init__(self, expected_bytes=0):
		self.expected_bytes = expected_bytes
		self.anomaly = True
	def __str__(self):
		if self.anomaly:
			return f'connection closed while expecting {self.expected_bytes} bytes'
		return 'connection closed'

def moulti_unix_socket():
	return socket_module.socket(socket_module.AF_UNIX, socket_module.SOCK_STREAM, 0)

def moulti_listen(bind=MOULTI_SOCKET, backlog=100, blocking=False):
	try:
		server_socket = moulti_unix_socket()
		server_socket.bind(bind)
		server_socket.listen(backlog)
		server_socket.setblocking(blocking)
		return server_socket
	except Exception as exc:
		raise MoultiProtocolException(f'cannot listen on {to_printable(bind)} (with backlog={backlog} and blocking={blocking}): {exc}')

def moulti_connect(address=MOULTI_SOCKET, bind=None):
	client_socket = moulti_unix_socket()
	client_socket.bind(bind if bind else f'\0moulti-client-{os.getpid()}.socket')
	client_socket.connect(address)
	return client_socket

def read_fixed_amount_from_socket(socket, amount: int):
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

def write_fixed_amount_to_socket(socket, data: bytes):
	if not data:
		return
	to_send = len(data)
	sent = 0
	while to_send > 0:
		just_sent = socket.send(data[sent:])
		to_send -= just_sent
		sent += just_sent

def read_tlv_data_from_socket(socket, max_fds=1):
	# This is a simple text-based TLV (type-length-value) protocol.
	# preamble examples: ":JSON:0000000002048:" ":TXT_:0000000002048:"
	preamble_regex = r'^:[A-Z_]{4}:[0-9]{13}:$'
	preamble_fixed_length = 20

	file_descriptors = []
	if max_fds > 0:
		_, file_descriptors, _, _ = socket_module.recv_fds(socket, 0, max_fds)

	try:
		preamble = read_fixed_amount_from_socket(socket, preamble_fixed_length).decode('ascii')
	except MoultiConnectionClosedException as mcce:
		mcce.anomaly = mcce.expected_bytes != preamble_fixed_length
		raise mcce
	except UnicodeDecodeError:
		raise MoultiProtocolException('non-ASCII preamble: {str(preamble)}')
	rem = re.match(preamble_regex, preamble)
	if not rem:
		raise MoultiProtocolException(f'invalid preamble: {preamble}')
	data_type = preamble[1:5].rstrip('_')
	if not data_type:
		raise MoultiProtocolException(f'invalid data type: {preamble[1:5]}')
	data_length = int(preamble[6:19])

	return data_type, read_fixed_amount_from_socket(socket, data_length), file_descriptors

def write_tlv_data_to_socket(socket, data: bytes, data_type: str = 'JSON', fds=None):
	data_type = data_type + '____'
	data_length = len(data)
	preamble = f':{data_type[0:4]}:{data_length:013}:'.encode('ascii')
	if fds:
		socket_module.send_fds(socket, [preamble], [fd.fileno() for fd in fds])
	else:
		write_fixed_amount_to_socket(socket, preamble)
	write_fixed_amount_to_socket(socket, data)

def data_to_message(data: bytes) -> dict:
	try:
		string = data.decode('utf-8')
		message = json.loads(string)
		return message
	except UnicodeDecodeError:
		raise MoultiProtocolException(f'received non UTF-8 {len(data)}-byte line')
	except JSONDecodeError:
		raise MoultiProtocolException(f'received non-JSON message')
		return

def message_to_data(message: dict) -> bytes:
	string = json.dumps(message)
	data = string.encode('utf-8')
	return data

def send_json_message(socket, message, fds=None):
	data = message_to_data(message)
	write_tlv_data_to_socket(socket, data, 'JSON', fds)

def recv_json_message(socket, max_fds=1):
	data_type, data, file_descriptors = read_tlv_data_from_socket(socket, max_fds)
	if data_type != 'JSON':
		raise MoultiProtocolException('received non-JSON message')
	return data_to_message(data), file_descriptors

def send_to_moulti(message, wait_for_reply=True):
	with moulti_connect() as moulti_socket:
		send_json_message(moulti_socket, message)
		if wait_for_reply:
			reply, _ = recv_json_message(moulti_socket, 0)
			return reply
	return None

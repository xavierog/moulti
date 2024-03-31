import os
import re
import sys
import pwd
import uuid
from struct import calcsize, unpack
from socket import socket as Socket, AF_UNIX, SOCK_STREAM, SOL_SOCKET
from socket import recv_fds as socket_recv_fds, send_fds
import json
from json.decoder import JSONDecodeError
from typing import Any, Callable

Message = dict[str, Any]
FDs = list[int]
TLVCallback = Callable[[Socket, str, str, bytes, FDs], None]
LogCallback = Callable[[str], None]

# recv_fds() uses CMSG_LEN instead of CMSG_SPACE to compute the ancillary data buffer size (socklen_t msg_controllen)
# and is thus liable to underestimate it. On some platforms (e.g. FreeBSD+amd64), this results in MSG_CTRUNC.
# A simple workaround is to adjust/increment max_fds.
CMSG_ADJUSTMENT = 1 if 'bsd' in sys.platform else 0

def recv_fds(sock: Socket, bufsize: int, maxfds: int, flags: int = 0) -> tuple[Any, Any, Any, Any]:
	return socket_recv_fds(sock, bufsize, maxfds + CMSG_ADJUSTMENT, flags)

def abstract_unix_sockets_supported() -> bool:
	# According to https://github.com/microsoft/WSL/issues/4240#issuecomment-620805115 :
	# > "Windows implementation of AF_UNIX does not support abstract sockets"
	# Consequently, assume only Linux supports abstract Unix sockets:
	return sys.platform == 'linux'

def run_dir() -> str:
	# This mess is *exactly* why we prefer abstract Unix sockets:
	if 'XDG_RUNTIME_DIR' in os.environ:
		return os.environ['XDG_RUNTIME_DIR']
	our_directory = 'moulti'
	if 'XDG_CACHE_HOME' in os.environ:
		return os.path.join(os.environ['XDG_CACHE_HOME'], our_directory)
	caches = os.path.expanduser('~/Library/Caches')
	if os.path.isdir(caches):
		return os.path.join(caches, our_directory)
	return os.path.join(os.path.expanduser('~/.cache'), our_directory)
	# Fallback on /tmp would have brought security implications (e.g. umask).

def current_username() -> str:
	uid = os.getuid()
	return pwd.getpwuid(uid).pw_name

def current_instance() -> str:
	return os.environ.get('MOULTI_INSTANCE') or 'default'

def make_socket_path(filename: str, abstract: bool, dirpath: str|None = None, printable: bool = True) -> str:
	if abstract:
		return ('@' if printable else '\0') + filename
	return os.path.join(dirpath or run_dir(), filename)

def default_moulti_socket_path() -> str:
	username = current_username()
	instance = current_instance()
	socket_filename = f'moulti-{username}-{instance}.socket'
	return make_socket_path(socket_filename, abstract_unix_sockets_supported())

def moulti_bind_path(abstract: bool) -> str:
	username = current_username()
	pid = os.getpid()
	socket_filename = f'moulti-client-{username}-{pid}.socket'
	return make_socket_path(socket_filename, abstract, printable=False)

def is_abstract_socket(socket_path: str) -> bool:
	return bool(socket_path and socket_path[0] == '\0')

def from_printable(socket_path: str) -> str:
	if socket_path and socket_path[0] == '@':
		socket_path = '\0' + socket_path[1:]
	return socket_path

def to_printable(socket_path: str) -> str:
	if is_abstract_socket(socket_path):
		socket_path = '@' + socket_path[1:]
	return socket_path

PRINTABLE_MOULTI_SOCKET = os.environ.get('MOULTI_SOCKET_PATH') or default_moulti_socket_path()
MOULTI_SOCKET = from_printable(PRINTABLE_MOULTI_SOCKET)

class MoultiProtocolException(Exception):
	pass

class MoultiConnectionClosedException(Exception):
	def __init__(self, expected_bytes: int = 0, anomaly: bool = True):
		self.expected_bytes = expected_bytes
		self.anomaly = anomaly
	def __str__(self) -> str:
		if self.anomaly:
			return f'connection closed by peer while expecting {self.expected_bytes} bytes'
		return 'connection closed by peer'

def moulti_unix_socket() -> Socket:
	return Socket(AF_UNIX, SOCK_STREAM, 0)

def moulti_listen(bind: str = MOULTI_SOCKET, backlog: int = 100, blocking: bool = False) -> tuple[Socket, bool]:
	try:
		server_socket = moulti_unix_socket()
		abstract = is_abstract_socket(bind)
		if not abstract:
			os.makedirs(os.path.dirname(bind), exist_ok=True)
		server_socket.bind(bind)
		server_socket.listen(backlog)
		server_socket.setblocking(blocking)
		return server_socket, abstract
	except Exception as exc:
		err = f'cannot listen on {to_printable(bind)} (with backlog={backlog} and blocking={blocking}): {exc}'
		raise MoultiProtocolException(err) from exc

def clean_socket(socket_path: str = PRINTABLE_MOULTI_SOCKET) -> None:
	if not socket_path.startswith('@'):
		try:
			os.unlink(socket_path)
		except FileNotFoundError:
			pass

def get_unix_credentials(socket: Socket) -> tuple[int, int, int]:
	# struct ucred is { pid_t, uid_t, gid_t }
	struct_ucred = '3i'
	from socket import SO_PEERCRED # pylint: disable=import-outside-toplevel
	unix_credentials = socket.getsockopt(SOL_SOCKET, SO_PEERCRED, calcsize(struct_ucred))
	pid, uid, gid = unpack(struct_ucred, unix_credentials)
	return pid, uid, gid

def moulti_connect(address: str = MOULTI_SOCKET, bind: str | None = None) -> Socket:
	client_socket = moulti_unix_socket()
	abstract = is_abstract_socket(address)
	final_bind = bind or moulti_bind_path(abstract)
	client_socket.bind(final_bind)
	if not is_abstract_socket(final_bind):
		# As a pure client, we do not actually need to keep our socket file:
		clean_socket(final_bind)
	client_socket.connect(address)
	return client_socket

def getraddr(socket: Socket) -> str:
	"""
	Return the remote address of the given socket.
	"""
	try:
		raddr = socket.getpeername()
	except OSError as ose:
		raddr = f'unknown/errno={ose.errno}'
	if not isinstance(raddr, str):
		raddr = raddr.decode('utf-8')
	raddr = raddr.replace('\0', '@')
	return raddr + ':fd' + str(socket.fileno())

# This is a simple text-based TLV (type-length-value) protocol.
# preamble examples: ":JSON:0000000002048:" ":TXT_:0000000002048:"
PREAMBLE_FIXED_LENGTH = 20
PREAMBLE_REGEX = r'^:[A-Z_]{4}:[0-9]{13}:$'

def parse_preamble(preamble_data: bytes) -> tuple[str, int]:
	"""
	Parse a Moulti TLV preamble; return type and length or raise
	MoultiProtocolException.
	"""
	try:
		preamble = preamble_data.decode('ascii')
	except UnicodeDecodeError as ude:
		raise MoultiProtocolException('non-ASCII preamble: {str(preamble)}') from ude
	if not re.match(PREAMBLE_REGEX, preamble):
		raise MoultiProtocolException(f'invalid preamble: {preamble}')
	data_type = preamble[1:5].rstrip('_')
	if not data_type:
		raise MoultiProtocolException(f'invalid data type: {preamble[1:5]}')
	data_length = int(preamble[6:19])
	return data_type, data_length

def read_fixed_amount_from_socket(socket: Socket, amount: int) -> bytes:
	data = bytes()
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
	file_descriptors: FDs = []
	if max_fds > 0:
		_, file_descriptors, _, _ = recv_fds(socket, 0, max_fds)

	try:
		preamble = read_fixed_amount_from_socket(socket, PREAMBLE_FIXED_LENGTH)
	except MoultiConnectionClosedException as mcce:
		mcce.anomaly = mcce.expected_bytes != PREAMBLE_FIXED_LENGTH
		raise mcce
	data_type, data_length = parse_preamble(preamble)
	return data_type, read_fixed_amount_from_socket(socket, data_length), file_descriptors

def write_tlv_data_to_socket(socket: Socket, data: bytes, data_type: str = 'JSON', fds: FDs|None = None) -> None:
	data_type = data_type + '____'
	data_length = len(data)
	preamble = f':{data_type[0:4]}:{data_length:013}:'.encode('ascii')
	to_send = preamble + data
	if fds:
		send_fds(socket, [to_send], fds)
	else:
		write_fixed_amount_to_socket(socket, to_send)

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

def send_json_message(socket: Socket, message: Message, fds: FDs | None = None) -> str:
	# Setting a message id yields smaller replies as the server does not have to send the original data again:
	if 'msgid' not in message:
		message = {'msgid': str(uuid.uuid4()), **message}
	data = message_to_data(message)
	write_tlv_data_to_socket(socket, data, 'JSON', fds)
	return message['msgid']

def recv_json_message(socket: Socket, max_fds: int = 1) -> tuple[Message, FDs]:
	data_type, data, file_descriptors = read_tlv_data_from_socket(socket, max_fds)
	if data_type != 'JSON':
		raise MoultiProtocolException('received non-JSON message')
	return data_to_message(data), file_descriptors

def send_to_moulti(message: Message, wait_for_reply: bool = True) -> Message | None:
	with moulti_connect() as moulti_socket:
		msgid = send_json_message(moulti_socket, message)
		if wait_for_reply:
			reply, _ = recv_json_message(moulti_socket, 0)
			if msgid in reply and reply['msgid'] != msgid:
				raise MoultiProtocolException('expected message id {msgid} but received {reply["msgid"]}')
			return reply
	return None

class MoultiTLVReader:
	"""
	Helper that reads TLV data from a given socket each time read() is called.
	Each time a complete TLV dataset has been read, call a given callback.
	"""
	# pylint: disable=attribute-defined-outside-init
	def __init__(
		self,
		socket: Socket,
		raddr: str,
		callback: TLVCallback,
		log_callback: LogCallback|None = None,
		max_fds: int = 1
	):
		self.socket = socket
		self.raddr = raddr
		self.callback = callback
		self.log_callback = log_callback
		self.max_fds = max_fds
		self.reset()

	def reset(self) -> None:
		self.recv_fds_done = False
		self.file_descriptors: FDs = []

		self.recv_preamble_done = False
		self.preamble_data = bytes()
		self.data_type = ''
		self.data_length = 0
		self.data_value = bytes()

	def log(self, line: str) -> None:
		if self.log_callback:
			self.log_callback(line)

	def got_complete_tlv(self) -> None:
		data_type, data, file_descriptors = self.data_type, self.data_value, self.file_descriptors
		self.reset()
		self.callback(self.socket, self.raddr, data_type, data, file_descriptors)

	def read(self) -> None:
		try:
			# Read file descriptors:
			if self.max_fds > 0 and not self.recv_fds_done:
				_, self.file_descriptors, _, _ = recv_fds(self.socket, 0, self.max_fds)
				self.recv_fds_done = True
			# Read preamble:
			if not self.recv_preamble_done:
				amount = PREAMBLE_FIXED_LENGTH - len(self.preamble_data)
				while amount > 0:
					new_data = self.socket.recv(amount)
					if not new_data:
						# If we notice the client closed its connection here, it may be normal:
						anomaly = amount != PREAMBLE_FIXED_LENGTH
						raise MoultiConnectionClosedException(amount, anomaly=anomaly)
					self.preamble_data += new_data
					amount -= len(new_data)
				self.data_type, self.data_length = parse_preamble(self.preamble_data)
				self.recv_preamble_done = True
			# Read data:
			while self.data_length > 0:
				new_data = self.socket.recv(self.data_length)
				if not new_data:
					raise MoultiConnectionClosedException(self.data_length)
				self.data_value += new_data
				self.data_length -= len(new_data)
			self.got_complete_tlv()
		except BlockingIOError:
			# It turns out there is nothing (left) to read; better luck next read().
			return

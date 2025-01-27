import os
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
from socket import socket as Socket
from queue import Queue, Empty
from typing import Callable
from .helpers import abridge_dict, clean_selector
from .protocol import MoultiTLVReader, MoultiTLVWriter
from .protocol import MoultiProtocolException, MoultiConnectionClosedException
from .protocol import clean_socket, current_instance, data_to_message, moulti_socket_path, FDs, from_printable
from .protocol import getraddr, LogCallback, Message, message_to_data, moulti_listen

LoopCallback = Callable[[], bool]
MessageCallback = Callable[[Socket, str, Message, FDs], None]
ReadyCallback = Callable[[], None]
SecurityCallback = Callable[[Socket], str]

TYPE_ACCEPT = 1
TYPE_READ_WRITE = 2
TYPE_NOTIFY = 3

class MoultiServer:
	"""
	A server implementation of the Moulti protocol. It uses non-blocking
	sockets polled in an event loop that is expected to run in a dedicated thread.
	"""
	def __init__(
		self,
		instance_name: str|None,
		socket_path: str|None,
		loop_callback: LoopCallback,
		message_callback: MessageCallback,
		log_callback: LogCallback|None = None,
		ready_callback: ReadyCallback|None = None,
		security_callback: SecurityCallback|None = None,
	):
		"""
		socket_path: printable path describing the socket to listen to
		loop_callback: function that returns True if the event loop should keep running, False if it should stop
		message_callback: called after a complete message was received from a client
		log_callback: (optional) called whenever this class wishes to log something
		ready_callback: (optional) called right before the event loop starts; should NOT block
		security_callback: (optional) called after a new client connection was established; should return a non-empty
		error message to deny the connection or an empty string to accept it
		"""
		self.server_selector = DefaultSelector()
		self.instance_name = instance_name or current_instance()
		self.socket_path = socket_path or moulti_socket_path(self.instance_name)
		self.server_socket: Socket|None = None
		self.server_socket_is_abstract = False
		self.loop_callback = loop_callback
		self.message_callback = message_callback
		self.log_callback = log_callback
		self.ready_callback = ready_callback
		self.security_callback = security_callback
		self.replies: Queue = Queue()
		"""Queue used to receive replies that the network loop should send to clients."""
		# That queue cannot be polled through the selectors module: combine it with a Unix pipe:
		self.notifications, self.notify = os.pipe()
		os.set_blocking(self.notifications, False)
		os.set_blocking(self.notify, False)

	def log(self, data: str) -> None:
		if self.log_callback is not None:
			self.log_callback(data)

	def is_listening(self) -> bool:
		return self.server_socket is not None

	def listen(self) -> None:
		self.server_socket, self.server_socket_is_abstract = moulti_listen(bind=from_printable(self.socket_path))
		socket_type = "abstract socket" if self.server_socket_is_abstract else "socket"
		self.log(f'listening on {socket_type} {self.socket_path}')

	def network_loop(self) -> None:
		if not self.is_listening():
			return
		try:
			self.server_selector.register(self.notifications, EVENT_READ, {'type': TYPE_NOTIFY})
			assert self.server_socket is not None
			self.server_selector.register(self.server_socket, EVENT_READ, {'type': TYPE_ACCEPT})

			if self.ready_callback is not None:
				self.ready_callback()

			while self.loop_callback():
				events = self.server_selector.select(0.1)
				# This loop is not entirely event-based: it also dequeues replies, hence the relatively short duration
				# in select().
				for key, mask in events:
					assert isinstance(key.data, dict)
					if key.data['type'] == TYPE_ACCEPT:
						assert isinstance(key.fileobj, Socket)
						self.accept(key.fileobj)
					elif key.data['type'] == TYPE_READ_WRITE:
						if mask & EVENT_WRITE:
							self.write(key.data['writer'])
						if mask & EVENT_READ:
							self.read(key.data['reader'])
					elif key.data['type'] == TYPE_NOTIFY:
						self.clear_notifications()
						self.handle_replies()
		except Exception as exc:
			self.log(f'network loop: {exc}')
		finally:
			clean_socket(self.socket_path)
			# Explicitly stop listening and close all sockets: this makes sense when and if the
			# Python process does not exit after this App has finished running.
			if self.server_socket is not None:
				self.server_socket.close()
				self.server_socket = None
			os.close(self.notify)
			clean_selector(self.server_selector, close_fds=True, close=True)

	def send_notification(self) -> None:
		if not self.is_listening():
			return
		try:
			os.write(self.notify, b'x')
		except BlockingIOError:
			# The pipe is full, but this can be ignored.
			pass

	def clear_notifications(self) -> None:
		try:
			while True:
				os.read(self.notifications, 1024)
		except BlockingIOError:
			# All done: the pipe is empty.
			pass

	def accept(self, socket: Socket) -> None:
		raddr = None
		try:
			connection, _ = socket.accept()
			raddr = getraddr(connection)
			self.log(f'{raddr}: accept: accepted new connection')
			if self.security_callback is not None:
				if error_message := self.security_callback(connection):
					connection.close()
					self.log(f'{raddr}: accept: closed connection: {error_message}')
					return
			connection.setblocking(False)
			data = {
				'type': TYPE_READ_WRITE,
				'reader': MoultiTLVReader(connection, raddr, self.got_tlv, self.log_callback),
				'writer': MoultiTLVWriter(connection, raddr, None, self.log_callback),
			}
			self.server_selector.register(connection, EVENT_READ, data)
		except Exception as exc:
			self.log(f'{raddr}: accept: {exc}')

	def read(self, tlv_reader: MoultiTLVReader) -> None:
		raddr = tlv_reader.raddr
		try:
			try:
				# Read whatever there is to read; if a complete TLV message is received, calls got_tlv, which calls
				# handle_message, which calls reply().
				tlv_reader.read()
			except (MoultiProtocolException, MoultiConnectionClosedException, ConnectionResetError) as exc:
				self.server_selector.unregister(tlv_reader.socket)
				tlv_reader.socket.close()
				self.log(f'{raddr}: read: closed connection; cause: {exc}')
		except Exception as exc:
			self.log(f'{raddr}: read: {exc}')

	def write(self, tlv_writer: MoultiTLVWriter) -> None:
		raddr = tlv_writer.raddr
		try:
			try:
				# Write whatever there is to write:
				all_written = tlv_writer.write()
				self.watch_write_events(tlv_writer.socket, not all_written)
			except (MoultiProtocolException, MoultiConnectionClosedException, ConnectionResetError) as exc:
				self.server_selector.unregister(tlv_writer.socket)
				tlv_writer.socket.close()
				self.log(f'{raddr}: write: closed connection; cause: {exc}')
		except Exception as exc:
			self.log(f'{raddr}: write: {exc}')

	def got_tlv(self, socket: Socket, raddr: str, data_type: str, data: bytes, file_descriptors: FDs) -> None:
		if data_type == 'JSON':
			message = data_to_message(data)
			log_message = abridge_dict(message)
			self.log(f'{raddr}: => message={log_message} {file_descriptors=}')
			self.message_callback(socket, raddr, message, file_descriptors)
		else:
			raise MoultiProtocolException(f'cannot handle {data_type} {len(data)}-byte message')

	def reply(self, socket: Socket, message: Message) -> None:
		# Delegate to the network loop through a queue:
		self.replies.put_nowait((socket, message))
		self.send_notification()
		# This approach makes this function thread-safe.

	def handle_replies(self) -> None:
		try:
			while True:
				socket, message = self.replies.get_nowait()
				self.handle_reply(socket, message)
		except Empty:
			pass

	def handle_reply(self, socket: Socket, message: Message) -> None:
		try:
			# Get the TLV writer for the given socket:
			tlv_writer = self.server_selector.get_key(socket).data['writer']
			# Provide the TLV writer with the reply message so it stores it but does not try to send it:
			tlv_writer.write_message(message_to_data(message), 'JSON', immediate=False)
			# Let write() handle the rest:
			self.write(tlv_writer)
		except Exception as exc:
			self.log(f'handle_reply: {exc}')

	def watch_write_events(self, socket: Socket, watch: bool) -> None:
		"""
		Enable or disable the watching of write events for the given socket.
		Such watching is relevant only when we have data to write to that socket.
		In particular, watching write events for an idle socket leads to 100% CPU consumption as the selector keeps
		returning the socket is ready for writing.
		"""
		key = self.server_selector.get_key(socket)
		events = EVENT_READ
		if watch:
			events |= EVENT_WRITE
		if events != key.events:
			self.server_selector.modify(socket, events, key.data)

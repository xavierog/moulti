"""
Provide everything to reject unauthorized Moulti clients.
"""
from os import environ, getuid
from struct import calcsize, unpack
import sys
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .app import Moulti
	from socket import socket as Socket

def ids_from_env(env_var_name: str) -> list[int]:
	try:
		return [int(xid) for xid in environ.get(env_var_name, '').split(',')]
	except Exception:
		return []

def get_unix_credentials(socket: 'Socket') -> tuple[int, int, int]:
	if sys.platform == 'linux':
		# struct ucred is { pid_t, uid_t, gid_t }
		struct_ucred = '3i'
		from socket import SOL_SOCKET, SO_PEERCRED # pylint: disable=import-outside-toplevel,no-name-in-module
		unix_credentials = socket.getsockopt(SOL_SOCKET, SO_PEERCRED, calcsize(struct_ucred))
		pid, uid, gid = unpack(struct_ucred, unix_credentials)
		return pid, uid, gid
	return -1, -1, -1

class MoultiSecurityPolicy:
	def __init__(self, app: 'Moulti'):
		self.app = app

		# By default, allow only the current uid to connect to Moulti:
		self.allowed_uids = [getuid()]
		self.allowed_gids = []

		# Make this behaviour configurable through environment variables:
		self.allowed_uids.extend(ids_from_env('MOULTI_ALLOWED_UID'))
		self.allowed_gids.extend(ids_from_env('MOULTI_ALLOWED_GID'))

	def check(self, socket: 'Socket') -> str:
		# Check Unix credentials (uid/gid) if and only if Moulti listens on an abstract socket.
		# Regular sockets are protected by file permissions.
		if self.app.server is not None and self.app.server.server_socket_is_abstract:
			_, uid, gid = get_unix_credentials(socket)
			allowed = uid in self.allowed_uids or gid in self.allowed_gids
			if not allowed:
				return f'invalid Unix credentials {uid}:{gid}'
		return ''

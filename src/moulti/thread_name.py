"""
Provide helpers to assign human-friendly names to system threads.
"""

import sys
from ctypes import CDLL, c_char_p, c_void_p
from ctypes.util import find_library
from functools import cache, wraps
from threading import current_thread
from typing import Any, Callable
from .environ import env
from .helpers import abridge_string

def thread_name_max_len() -> int:
	"""
	Return the maximum name length (excluding trailing null byte) for system threads.
	"""
	platform = sys.platform
	# Most Unix operating systems truncate thread names to MAXCOMLEN characters + a null byte:
	max_len = 15
	if platform.startswith("darwin"):
		max_len = 63
	elif platform.startswith("freebsd"):
		max_len = 19
	elif platform.startswith("openbsd"):
		max_len = 23
	elif platform.startswith("netbsd"):
		max_len = 15
	return max_len


THREAD_NAME_MAX_LEN = thread_name_max_len()


@cache
def pthread_set_name_function() -> Callable:
	"""
	Return a simple wrapper around pthread_setname_np().
	This wrapper expects a name as single string (str) argument and assigns it to the current thread.
	"""
	# Access the pthread library:
	pthread_lib = CDLL(find_library("pthread"))

	# Access the pthread_self function:
	pthread_self = pthread_lib.pthread_self
	pthread_self.restype = c_void_p

	# Access the pthread_set_name_np function:
	try:
		pthread_setname_np = pthread_lib.pthread_setname_np
	except AttributeError:
		pthread_setname_np = pthread_lib.pthread_set_name_np

	# Deal with its non-portable (hence "_np") arguments:
	if sys.platform.startswith("netbsd"):
		pthread_setname_np.argtypes = [c_void_p, c_char_p, c_char_p]
		def make_args(name: bytes) -> tuple:
			return (pthread_self(), b"%s\0", name)
	elif sys.platform.startswith("darwin"):
		pthread_setname_np.argtypes = [c_char_p]
		def make_args(name: bytes) -> tuple:
			return (name,)
	else:
		pthread_setname_np.argtypes = [c_void_p, c_char_p]
		def make_args(name: bytes) -> tuple:
			return (pthread_self(), name,)

	def function(name: str) -> None:
		name_bytes = name.encode("ascii", "replace")[:THREAD_NAME_MAX_LEN] + b"\0"
		pthread_setname_np(*make_args(name_bytes))
	return function


def set_thread_name(name: str) -> None:
	"""
	Assign the given name to the current thread.
	If necessary, the name gets abridged so as to fit system limitations (typically 15 or 63 characters max).
	"""
	if env("MOULTI_NAME_THREADS") == "no":
		return
	abridged_name = abridge_string(name, threshold=THREAD_NAME_MAX_LEN, sep="")

	# Python >= 3.14 assigns names to system threads out of the box:
	if sys.version_info >= (3, 14):
		current_thread().name = abridged_name
	else: # Previous versions of Python:
		try:
			pthread_set_name_np = pthread_set_name_function()
			pthread_set_name_np(abridged_name)
		except Exception:
			# Best-effort: we are not even interested in what went wrong.
			pass



IDLE_THREAD_NAME = "thread-pool"
"""
Thread name set by the thread_name() decorator after a decorated function
returns. This value reflects the underlying thread has become idle and has
reintegrated the thread pool.
"""

KEEP_THREAD_NAME = None
"""
Legible constant, to be used with the thread_name() decorator.
"""

def thread_name(start: str|None = KEEP_THREAD_NAME, end: str|None = IDLE_THREAD_NAME) -> Callable:
	"""
	Decorator that calls:
	- set_thread_name(start) before the decorated function, unless start is KEEP_THREAD_NAME;
	- set_thread_name(end) after the decorated function, unless end is KEEP_THREAD_NAME.
	"""
	def thread_name_decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(*args: Any, **kwargs: Any) -> Any:
			try:
				if start is not KEEP_THREAD_NAME:
					set_thread_name(start)
				return func(*args, **kwargs)
			finally:
				if end is not KEEP_THREAD_NAME:
					set_thread_name(end)
		return wrapper
	return thread_name_decorator

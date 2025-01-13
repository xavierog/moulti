"""
Provide everything to get settings from environment variables.
"""
from os import environ
from os.path import isfile
from typing import Any, Type, TypeAlias, Callable, Iterable
from argparse import ArgumentTypeError

AcceptableType: TypeAlias = Type|Callable[[str], Any]
AcceptableTypes: TypeAlias = Iterable[AcceptableType]
OptionalAcceptableTypes: TypeAlias = AcceptableTypes|None


def pint(value: str) -> int:
	integer_value = int(value)
	if integer_value < 0:
		raise ArgumentTypeError('expected a positive integer')
	return integer_value


def spint(value: str) -> int:
	integer_value = int(value)
	if integer_value <= 0:
		raise ArgumentTypeError('expected a strictly positive integer')
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


def existing_filepath(value: str) -> str:
	if not isfile(value):
		raise ArgumentTypeError('expected an existing filepath')
	return value


def try_types(value: Any, types: AcceptableTypes) -> tuple[Any, bool]:
	for acceptable_type in types:
		try:
			return acceptable_type(value), True
		except Exception:
			pass
	return value, False


def env(
	name: str,
	default: Any = None,
	types: OptionalAcceptableTypes = None,
) -> Any:
	"""
	Return environment variable name and ensure it fits one of the provided types.
	Otherwise, return the default value.
	"""
	if (value := environ.get(name)) is not None:
		if types is None:
			return value
		value, ok = try_types(value, types)
		if ok:
			return value
	return default


def enva(
	name: str,
	default: Any = None,
	types: OptionalAcceptableTypes = None,
	sep: str = ',',
	strict: bool = True,
) -> Any:
	"""
	Get an array from the environment.
	Specifically, get environment variable name, split it using separator sep and ensure each resulting item fits one of
	the provided types.
	If strict is False and an item does not fit any type, it is discarded from the returned array.
	If strict is True and an item does not fit any type, this function returns the default value.
	"""
	if (value := environ.get(name)) is None:
		return default
	if not value:
		return []
	values = value.split(sep)
	if types is None:
		return values

	final_list = []
	for item in values:
		value, ok = try_types(item, types)
		if ok:
			final_list.append(value)
		elif strict:
			return default
	return final_list


def envd(
	name: str,
	default: Any = None,
	types: OptionalAcceptableTypes = None,
	sepa: str = ',',
	sepkv: str = '=',
	strict: bool = True,
) -> Any:
	"""
	Get a dict from the environment.
	Specifically, get environment variable name, split it using array separator sepa, split each resulting item using
	key-value separator sepkv then ensure each resulting value fits one of the provided types.
	If strict is False and a value does not fit any type, the key-value pair is discarded from the returned array.
	If strict is True and a value does not fit any type, this function returns the default value.
	"""
	key_values = enva(name, default=None, types=None, sep=sepa)
	if key_values is None:
		# enva() returned the default value, and so does this function:
		return default
	final_dict = {}
	for key_value in key_values:
		if sepkv in key_value:
			key, value = key_value.split(sepkv, maxsplit=1)
		else:
			return default
		if types is None:
			final_dict[key] = value
		else:
			value, ok = try_types(value, types)
			if ok:
				final_dict[key] = value
			elif strict:
				return default
	return final_dict

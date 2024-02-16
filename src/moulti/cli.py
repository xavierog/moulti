# ruff: noqa: E501 Line too long
import sys
from argparse import ArgumentParser, _SubParsersAction
from .helpers import pint, send_to_moulti_and_handle_reply
from .protocol import send_to_moulti, PRINTABLE_MOULTI_SOCKET
from .widgets.cli import add_cli_arguments

def init(args: dict) -> None:
	"""Start a new Moulti instance."""
	from .app import main as init_moulti # pylint: disable=import-outside-toplevel
	init_moulti(**args)

def wait(verbose: bool = False, delay: int = 500, max_attempts: int = 0) -> None:
	"""Wait until the Moulti instance is available.
	Args:
		verbose: if True, output the reason why each connection attempt failed
		delay: number of milliseconds between two connection attempts
		max_attempts: maximum number of attempts before giving up; 0 means "never give up"
	"""
	import time # pylint: disable=import-outside-toplevel
	connected = False
	attempts = 0
	while not connected:
		try:
			attempts += 1
			send_to_moulti({'command': 'ping'})
			connected = True
			break
		except Exception as exc:
			if verbose:
				print(f'Connection #{attempts} to {PRINTABLE_MOULTI_SOCKET}: {exc}')
			if max_attempts > 0 and attempts == max_attempts:
				print('Giving up.')
				break
			time.sleep(delay / 1000.0)
	sys.exit(0 if connected else 1)

def add_main_commands(subparsers: _SubParsersAction) -> None:
	# moulti init
	init_parser = subparsers.add_parser('init', help='Start a new Moulti instance.')
	init_parser.set_defaults(func=init)

	# moulti run
	run_parser = subparsers.add_parser('run', help='Start a new Moulti instance and run a command')
	run_parser.set_defaults(func=init)
	run_parser.add_argument('command', type=str, nargs='+', help='command to run along with its arguments')

	# moulti wait
	wait_parser = subparsers.add_parser('wait', help='Wait until the Moulti instance is available.')
	wait_parser.set_defaults(func=wait)
	wait_parser.add_argument('--verbose', '-v', action='store_true', help='if True, output the reason why each connection attempt failed')
	wait_parser.add_argument('--delay', '-d', type=pint, default=500, help='number of milliseconds between two connection attempts')
	wait_parser.add_argument('--max-attempts', '-m', type=pint, default=0, help='maximum number of attempts before giving up; 0 means "never give up"')

	# moulti set
	set_parser = subparsers.add_parser('set', help='Set Moulti options')
	set_parser.set_defaults(func=send_to_moulti_and_handle_reply, command='set')
	set_parser.add_argument('--title', '-t', type=str, help='title displayed at the top of the screen')

def build_arg_parser() -> ArgumentParser:
	arg_parser = ArgumentParser(prog='moulti', description='step-by-step logs')
	subparsers = arg_parser.add_subparsers(required=True)
	# moulti init, moulti wait:
	add_main_commands(subparsers)
	# moulti <widget>:
	add_cli_arguments(subparsers)
	return arg_parser

def main() -> None:
	try:
		arg_parser = build_arg_parser()
		args = vars(arg_parser.parse_args())
		func = args.pop('func')
		# Subtlety: func and args are not always used the same way:
		if func == wait: # pylint: disable=comparison-with-callable
			wait(**args)
		else:
			func(args)
	except KeyboardInterrupt:
		print('')
		sys.exit(1)

if __name__ == '__main__':
	main()

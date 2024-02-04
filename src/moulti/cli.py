# ruff: noqa: E501 Line too long
import sys
import uuid
from typing import Any, cast
from argparse import ArgumentParser, BooleanOptionalAction, _SubParsersAction
from .protocol import moulti_connect, send_to_moulti, send_json_message, recv_json_message
from .protocol import Message, PRINTABLE_MOULTI_SOCKET

Args = dict[str, Any]

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
			with moulti_connect():
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

def handle_reply(reply: Message) -> None:
	success = reply.get('done') is True
	if not success:
		fallback = 'alas, no error message was provided.'
		print('Something went wrong: ' + reply.get('error', fallback))
	sys.exit(0 if success else 1)

def send_to_moulti_and_handle_reply(message: Message) -> None:
	# Setting a message id yields smaller replies as the server does not have
	# to send the original data again:
	message = {'msgid': str(uuid.uuid4()), **message}
	reply = cast(dict[str, Any], send_to_moulti(message))
	handle_reply(reply)

def pass_stdin(args: Args) -> None:
	"""Pass the stdin file descriptor to Moulti and inject everything read from it into a given step."""
	moulti_socket = moulti_connect()
	step_id = args['id']
	# Clear the target step unless told not to through --append or --no-clear:
	if not args.get('append', False):
		send_json_message(moulti_socket, {'command': 'step', 'action': 'clear', 'id': step_id})
		reply, _ = recv_json_message(moulti_socket, 0)
	pass_message = {'command': 'pass', 'id': step_id, 'read_size': args['read_size']}
	send_json_message(moulti_socket, pass_message, [sys.stdin.fileno()])
	# At this stage, the remote Moulti process has the file descriptor and is
	# expected to read lines from it. On our side, we need to remain up &
	# running, otherwise the line-emitting process gets a SIGPIPE.
	# Specifically, we remain up and running until we get a message from the
	# remote Moulti process:
	reply, _ = recv_json_message(moulti_socket, 0)
	moulti_socket.close()
	handle_reply(reply)

set_options = step_add = step_delete = step_clear = step_append = send_to_moulti_and_handle_reply

def step_update(args: Args) -> None:
	no_none_args = {k:v for (k,v) in args.items() if v is not None}
	send_to_moulti_and_handle_reply(no_none_args)

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
	wait_parser.add_argument('--delay', '-d', type=int, default=500, help='number of milliseconds between two connection attempts')
	wait_parser.add_argument('--max-attempts', '-m', type=int, default=0, help='maximum number of attempts before giving up; 0 means "never give up"')

	# moulti set
	set_parser = subparsers.add_parser('set', help='Set Moulti options')
	set_parser.set_defaults(func=set_options, command='set')
	set_parser.add_argument('--title', '-t', type=str, help='title displayed at the top of the screen')

def add_pass_command(subparsers: _SubParsersAction) -> None:
	# moulti pass
	pass_parser = subparsers.add_parser('pass', help='Pass standard input to an existing Moulti step')
	pass_parser.set_defaults(func=pass_stdin)
	pass_parser.add_argument('id', type=str, help='unique identifier')
	pass_parser.add_argument('--append', '--no-clear', '-a', dest='append', action='store_true', help='do not clear the target step')
	pass_parser.add_argument('--read-size', '-rs', dest='read_size', type=int, default=64*1024, help='read size')

def add_step_options(parser: ArgumentParser, none: bool = False) -> None:
	"""Options common to step add (with actual default values) and step update (with None default values)."""
	parser.add_argument('--collapsed', action=BooleanOptionalAction, default=None if none else False, help='whether to collapse the step')
	parser.add_argument('--title', type=str, default=None, help='step title, always visible')
	parser.add_argument('--text', '-t', type=str, default=None if none else '', help='content')
	parser.add_argument('--top-text', '-tt', type=str, default=None if none else '', help='line of text displayed above the content')
	parser.add_argument('--bottom-text', '-bt', type=str, default=None if none else '', help='line of text displayed below the content')
	parser.add_argument('--min-height', '-mh', type=int, default=None if none else  1, help='minimum content height')
	parser.add_argument('--max-height', '-Mh', type=int, default=None if none else 25, help='maximum content height')
	parser.add_argument('--classes', '-c', type=str, default=None if none else 'standard', help='maximum content height')

def add_step_commands(step_subparsers: _SubParsersAction) -> None:
	# moulti step add
	step_add_parser = step_subparsers.add_parser('add', help='Add a new step to Moulti.')
	step_add_parser.set_defaults(func=step_add, command='step', action='add')
	step_add_parser.add_argument('id', type=str, help='unique identifier')
	add_step_options(step_add_parser)

	# moulti step update
	step_update_parser = step_subparsers.add_parser('update', help='Update an existing Moulti step.')
	step_update_parser.set_defaults(func=step_update, command='step', action='update')
	step_update_parser.add_argument('id', type=str, help='unique identifier')
	add_step_options(step_update_parser, none=True)

	# moulti step delete
	step_delete_parser = step_subparsers.add_parser('delete', help='Delete an existing Moulti step.')
	step_delete_parser.set_defaults(func=step_delete, command='step', action='delete')
	step_delete_parser.add_argument('id', type=str, help='unique identifier')

	# moulti step clear
	step_clear_parser = step_subparsers.add_parser('clear', help='Clear the contents of an existing Moulti step.')
	step_clear_parser.set_defaults(func=step_clear, command='step', action='clear')
	step_clear_parser.add_argument('id', type=str, help='unique identifier')

	# moulti step append
	step_append_parser = step_subparsers.add_parser('append', help='Append the given contents to an existing Moulti step.')
	step_append_parser.set_defaults(func=step_append, command='step', action='append')
	step_append_parser.add_argument('id', type=str, help='unique identifier')
	step_append_parser.add_argument('text', type=str, nargs='+', help='strings to append')

def build_arg_parser() -> ArgumentParser:
	arg_parser = ArgumentParser(prog='moulti', description='step-by-step logs')
	subparsers = arg_parser.add_subparsers(required=True)
	# moulti init, moulti wait:
	add_main_commands(subparsers)
	# moulti step:
	step_parser = subparsers.add_parser('step', help='Create and manage steps shown by Moulti.')
	step_subparsers = step_parser.add_subparsers(required=True)
	add_step_commands(step_subparsers)
	# moulti pass:
	add_pass_command(subparsers)
	return arg_parser

def main() -> None:
	arg_parser = build_arg_parser()
	args = vars(arg_parser.parse_args())
	func = args.pop('func')
	# Subtlety: func and args are not always used the same way:
	if func == wait: # pylint: disable=comparison-with-callable
		wait(**args)
	else:
		func(args)

if __name__ == '__main__':
	main()

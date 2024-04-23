import sys
from argparse import ArgumentParser, _SubParsersAction
from moulti.helpers import Args, pint, handle_reply
from moulti.helpers import send_to_moulti_and_handle_reply, send_no_none_to_moulti_and_handle_reply
from moulti.protocol import moulti_connect, send_json_message, recv_json_message
from ..collapsiblestep.cli import add_collapsiblestep_options

COMMAND = 'step'

def add_cli_arguments(subparsers: _SubParsersAction) -> None:
	# moulti step:
	step_parser = subparsers.add_parser(COMMAND, help='Create and manage steps shown by Moulti.')
	step_subparsers = step_parser.add_subparsers(required=True)
	add_step_commands(step_subparsers)
	# moulti pass:
	add_pass_command(subparsers)

def add_step_commands(step_subparsers: _SubParsersAction) -> None:
	# moulti step add
	step_add_parser = step_subparsers.add_parser('add', help='Add a new step to Moulti.')
	step_add_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='add')
	step_add_parser.add_argument('id', type=str, help='unique identifier')
	add_step_options(step_add_parser)

	# moulti step update
	step_update_parser = step_subparsers.add_parser('update', help='Update an existing Moulti step.')
	step_update_parser.set_defaults(func=send_no_none_to_moulti_and_handle_reply, command=COMMAND, action='update')
	step_update_parser.add_argument('id', type=str, help='unique identifier')
	add_step_options(step_update_parser, none=True)

	# moulti step delete
	step_delete_parser = step_subparsers.add_parser('delete', help='Delete an existing Moulti step.')
	step_delete_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='delete')
	step_delete_parser.add_argument('id', type=str, help='unique identifier')

	# moulti step clear
	step_clear_parser = step_subparsers.add_parser('clear', help='Clear the contents of an existing Moulti step.')
	step_clear_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='clear')
	step_clear_parser.add_argument('id', type=str, help='unique identifier')

	# moulti step append
	step_append_parser = step_subparsers.add_parser('append', help='Append the given contents to an existing Moulti step.')
	step_append_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='append')
	step_append_parser.add_argument('id', type=str, help='unique identifier')
	step_append_parser.add_argument('text', type=str, nargs='+', help='strings to append')

def add_pass_command(subparsers: _SubParsersAction) -> None:
	# moulti pass
	pass_parser = subparsers.add_parser('pass', help='Pass standard input to an existing Moulti step')
	pass_parser.set_defaults(func=pass_stdin)
	pass_parser.add_argument('id', type=str, help='unique identifier')
	pass_parser.add_argument('--append', '--no-clear', '-a', dest='append', action='store_true', help='do not clear the target step')
	pass_parser.add_argument('--read-size', '-rs', dest='read_size', type=pint, default=1, help='read size')

def add_step_options(parser: ArgumentParser, none: bool = False) -> None:
	"""Options common to step add (with actual default values) and step update (with None default values)."""
	add_collapsiblestep_options(parser, none)
	parser.add_argument('--text', '-t', type=str, default=None if none else '', help='content')
	parser.add_argument('--min-height', '-mh', type=pint, default=None if none else  1, help='minimum content height')
	parser.add_argument('--max-height', '-Mh', type=pint, default=None if none else 25, help='maximum content height; 0 to disable')

def pass_stdin(args: Args) -> None:
	"""Pass the stdin file descriptor to Moulti and inject everything read from it into a given step."""
	moulti_socket = moulti_connect()
	step_id = args['id']
	# Clear the target step unless told not to through --append or --no-clear:
	if not args.get('append', False):
		send_json_message(moulti_socket, {'command': COMMAND, 'action': 'clear', 'id': step_id})
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

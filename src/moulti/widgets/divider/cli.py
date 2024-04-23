from argparse import _SubParsersAction
from moulti.helpers import send_to_moulti_and_handle_reply, send_no_none_to_moulti_and_handle_reply
from ..abstractstep.cli import add_abstractstep_options

COMMAND = 'divider'

def add_cli_arguments(subparsers: _SubParsersAction) -> None:
	# moulti divider
	divider_parser = subparsers.add_parser(COMMAND, help='Create and manage dividers.')
	divider_subparsers = divider_parser.add_subparsers(required=True)
	add_divider_commands(divider_subparsers)

def add_divider_commands(divider_subparsers: _SubParsersAction) -> None:
	# moulti divider add
	divider_add_parser = divider_subparsers.add_parser('add', help='Add a new divider to Moulti.')
	divider_add_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='add')
	divider_add_parser.add_argument('id', type=str, help='unique identifier')
	add_abstractstep_options(divider_add_parser)

	# moulti divider update
	divider_update_parser = divider_subparsers.add_parser('update', help='Update an existing Moulti divider.')
	divider_update_parser.set_defaults(func=send_no_none_to_moulti_and_handle_reply, command=COMMAND, action='update')
	divider_update_parser.add_argument('id', type=str, help='unique identifier')
	add_abstractstep_options(divider_update_parser, none=True)

	# moulti divider delete
	divider_delete_parser = divider_subparsers.add_parser('delete', help='Delete an existing Moulti divider.')
	divider_delete_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='delete')
	divider_delete_parser.add_argument('id', type=str, help='unique identifier')

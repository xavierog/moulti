from argparse import _SubParsersAction
from moulti.helpers import send_delete, send_to_moulti_and_handle_reply, send_no_none_to_moulti_and_handle_reply
from ..abstractquestion.cli import add_abstractquestion_options, question_get_answer

COMMAND = 'buttonquestion' # abridged 'bq' below

def add_cli_arguments(subparsers: _SubParsersAction) -> None:
	# moulti buttonquestion:
	bq_parser = subparsers.add_parser(COMMAND, help='create and manage interactive questions with buttons')
	bq_subparsers = bq_parser.add_subparsers(required=True)
	add_bq_commands(bq_subparsers)

def add_bq_commands(bq_subparsers: _SubParsersAction) -> None:
	# moulti buttonquestion add
	bq_add_parser = bq_subparsers.add_parser('add', help='add a new question to Moulti')
	bq_add_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='add')
	bq_add_parser.add_argument('id', type=str, help='unique identifier')
	add_abstractquestion_options(bq_add_parser)
	button_metavar = ('VALUE', 'STYLE', 'LABEL')
	helpmsg = 'add a button; available styles: default, primary, error, warning, success'
	bq_add_parser.add_argument('--button', '-b', required=True, action='append', nargs=3, metavar=button_metavar, help=helpmsg)

	# moulti buttonquestion update
	bq_update_parser = bq_subparsers.add_parser('update', help='update an existing Moulti question')
	bq_update_parser.set_defaults(func=send_no_none_to_moulti_and_handle_reply, command=COMMAND, action='update')
	bq_update_parser.add_argument('id', type=str, help='unique identifier')
	add_abstractquestion_options(bq_update_parser, none=True)

	# moulti buttonquestion get-answer
	helpmsg = 'return the answer provided by the end user'
	bq_getanswer_parser = bq_subparsers.add_parser('get-answer', help=helpmsg)
	bq_getanswer_parser.set_defaults(func=question_get_answer, command=COMMAND, action='get-answer')
	bq_getanswer_parser.add_argument('id', type=str, help='unique identifier')
	bq_getanswer_parser.add_argument('--wait', '-w', action='store_true', help='wait until the answer is available')

	# moulti buttonquestion delete
	bq_delete_parser = bq_subparsers.add_parser('delete', help='delete an existing Moulti question')
	bq_delete_parser.set_defaults(func=send_delete, command=COMMAND, action='delete')
	bq_delete_parser.add_argument('id', type=str, nargs='+', help='unique identifier')

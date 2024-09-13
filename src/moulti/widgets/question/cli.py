from argparse import _SubParsersAction
from moulti.helpers import send_delete, send_to_moulti_and_handle_reply, send_no_none_to_moulti_and_handle_reply
from ..abstractquestion.cli import add_abstractquestion_options, question_get_answer
from ..inputquestion.cli import add_inputquestion_options

COMMAND = 'question' # abridged 'q' below

def add_cli_arguments(subparsers: _SubParsersAction) -> None:
	# moulti question:
	q_parser = subparsers.add_parser(COMMAND, help='create and manage interactive questions')
	q_subparsers = q_parser.add_subparsers(required=True)
	add_q_commands(q_subparsers)

def add_q_commands(q_subparsers: _SubParsersAction) -> None:
	# moulti question add
	q_add_parser = q_subparsers.add_parser('add', help='add a new question to Moulti')
	q_add_parser.set_defaults(func=send_to_moulti_and_handle_reply, command=COMMAND, action='add')
	q_add_parser.add_argument('id', type=str, help='unique identifier')
	add_abstractquestion_options(q_add_parser)
	add_inputquestion_options(q_add_parser)
	button_metavar = ('VALUE', 'STYLE', 'LABEL')
	helpmsg = 'add a button; available styles: default, primary, error, warning, success'
	helpmsg += '; VALUE may include the {input} placeholder'
	q_add_parser.add_argument('--button', '-b', required=True, action='append', nargs=3, metavar=button_metavar, help=helpmsg)

	# moulti question update
	q_update_parser = q_subparsers.add_parser('update', help='update an existing Moulti question')
	q_update_parser.set_defaults(func=send_no_none_to_moulti_and_handle_reply, command=COMMAND, action='update')
	q_update_parser.add_argument('id', type=str, help='unique identifier')
	add_abstractquestion_options(q_update_parser, none=True)
	add_inputquestion_options(q_update_parser, none=True)

	# moulti question get-answer
	helpmsg = 'return the answer provided by the end user'
	q_getanswer_parser = q_subparsers.add_parser('get-answer', help=helpmsg)
	q_getanswer_parser.set_defaults(func=question_get_answer, command=COMMAND, action='get-answer')
	q_getanswer_parser.add_argument('id', type=str, help='unique identifier')
	q_getanswer_parser.add_argument('--wait', '-w', action='store_true', help='wait until the answer is available')

	# moulti question delete
	q_delete_parser = q_subparsers.add_parser('delete', help='delete an existing Moulti question')
	q_delete_parser.set_defaults(func=send_delete, command=COMMAND, action='delete')
	q_delete_parser.add_argument('id', type=str, nargs='+', help='unique identifier')

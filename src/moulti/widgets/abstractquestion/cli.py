from argparse import ArgumentParser
from moulti.helpers import Args, handle_reply
from moulti.protocol import send_to_moulti
from ..collapsiblestep.cli import add_collapsiblestep_options

def add_abstractquestion_options(parser: ArgumentParser, none: bool = False) -> None:
	add_collapsiblestep_options(parser, none)
	parser.add_argument('--text', '-t', type=str, default=None if none else '', help='Question text')

def question_get_answer(args: Args) -> None:
	reply = send_to_moulti(args)
	assert reply is not None
	answer = reply.get('answer')
	if answer is not None:
		print(answer)
	handle_reply(reply)

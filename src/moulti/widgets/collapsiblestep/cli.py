from argparse import ArgumentParser, BooleanOptionalAction
from ..abstractstep.cli import add_abstractstep_options

def add_collapsiblestep_options(parser: ArgumentParser, none: bool = False) -> None:
	"""Options common to step add (with actual default values) and step update (with None default values)."""
	add_abstractstep_options(parser, none)
	parser.add_argument('--collapsed', action=BooleanOptionalAction, default=None if none else False, help='whether to collapse the step')
	parser.add_argument('--top-text', '-tt', type=str, default=None if none else '', help='line of text displayed above the content')
	parser.add_argument('--bottom-text', '-bt', type=str, default=None if none else '', help='line of text displayed below the content')

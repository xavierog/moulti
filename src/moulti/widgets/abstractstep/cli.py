from argparse import ArgumentParser
from moulti.helpers import bool_or_int

def add_abstractstep_options(parser: ArgumentParser, none: bool = False) -> None:
	"""Options common to step add (with actual default values) and step update (with None default values)."""
	parser.add_argument('--title', type=str, default=None, help='step title, always visible')
	parser.add_argument('--classes', '-c', type=str, default=None if none else 'standard', help='step class (color): standard, error, warning, success')
	parser.add_argument('--scroll-on-activity', type=bool_or_int, default=None if none else False, help='whether to scroll to this step upon activity', metavar='{true,false,...,-2,-1,0,1,2,...}')

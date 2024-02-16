from argparse import ArgumentParser, BooleanOptionalAction

def add_abstractstep_options(parser: ArgumentParser, none: bool = False) -> None:
	"""Options common to step add (with actual default values) and step update (with None default values)."""
	parser.add_argument('--title', type=str, default=None, help='step title, always visible')
	parser.add_argument('--top-text', '-tt', type=str, default=None if none else '', help='line of text displayed above the content')
	parser.add_argument('--bottom-text', '-bt', type=str, default=None if none else '', help='line of text displayed below the content')
	parser.add_argument('--classes', '-c', type=str, default=None if none else 'standard', help='step class (color): standard, error, warning, success')
	parser.add_argument('--collapsed', action=BooleanOptionalAction, default=None if none else False, help='whether to collapse the step')

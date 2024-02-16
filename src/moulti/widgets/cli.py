"""
This file provides a helper that lets all Moulti widgets declare their CLI arguments.
"""
from argparse import _SubParsersAction
from moulti.widgets import WIDGET_MODULES

def add_cli_arguments(subparsers: _SubParsersAction) -> None:
	for module_name in WIDGET_MODULES:
		cli = __import__(f'moulti.widgets.{module_name}.cli', globals(), locals(), 'add_cli_arguments')
		cli.add_cli_arguments(subparsers)

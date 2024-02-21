"""
This file provides a registry that exposes all TUI/Textual classes for Moulti widgets, keyed by their CLI command. This
can be used to determine whether a given command actually makes sense and which class to use to handle it.
All such widgets are expected to provide two modules (cli and tui) along with the following attributes:
- cli.COMMAND: str
- cli.add_cli_arguments(subparsers: argparse._SubParsersAction) -> None
- tui.MoultiWidgetClass: subclass of AbstractStep
"""
from moulti.widgets import WIDGET_MODULES
from .abstractstep.tui import AbstractStep

Registry = dict[str, type[AbstractStep]]

class MoultiWidgets:
	_registry: Registry = {}

	@classmethod
	def register(cls, command: str, widget_class: type[AbstractStep]) -> None:
		cls._registry[command] = widget_class

	@classmethod
	def register_widget_module(cls, module_name: str) -> None:
		cli = __import__(f'moulti.widgets.{module_name}.cli', globals(), locals(), 'COMMAND')
		tui = __import__(f'moulti.widgets.{module_name}.tui', globals(), locals(), 'MoultiWidgetClass')
		cls.register(cli.COMMAND, tui.MoultiWidgetClass)

	@classmethod
	def register_all_widget_modules(cls) -> None:
		for widget_module in WIDGET_MODULES:
			cls.register_widget_module(widget_module)

	@classmethod
	def registry(cls) -> Registry:
		if not cls._registry:
			cls.register_all_widget_modules()
		return cls._registry

	@classmethod
	def command_to_class(cls, command: str) -> type[AbstractStep] | None:
		if not cls._registry:
			cls.register_all_widget_modules()
		return cls._registry.get(command)

	@classmethod
	def class_to_command(cls, widget_class: type[AbstractStep]) -> str | None:
		for command, moulti_widget_class in cls._registry.items():
			if moulti_widget_class == widget_class:
				return command
		return None

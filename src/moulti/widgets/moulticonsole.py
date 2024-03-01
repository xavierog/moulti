from typing import Any
from typing_extensions import Self
from pyperclip import copy # type: ignore
from textual.app import ComposeResult
from textual.events import Click
from textual.widgets import Label, Static
from .moultilog import MoultiLog

class MoultiConsole(Static):
	BINDINGS = [
		("c", "to_clipboard(False)", "Copy"),
		("w", "to_clipboard(True)", "With colors"),
	]

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.log_widget = MoultiLog()

	def compose(self) -> ComposeResult:
		yield Label('Moulti console')
		yield self.log_widget

	def write(self, content: str) -> Self:
		self.log_widget.write(content)
		return self

	async def on_click(self, event: Click) -> None:
		# Clicking the console (label or log) means focusing its log widget:
		self.log_widget.focus()
		event.stop()

	async def action_to_clipboard(self, keep_styles: bool = False) -> None:
		try:
			copy('\n'.join(self.log_widget.to_lines(keep_styles)))
			title, message, res = 'Console copied!', 'Console lines copied to clipboard', True
		except Exception as exc:
			title, message, res = 'Failed to copy console!', str(exc), False
		self.app.notify(message, title=title, severity='information' if res else 'error')

	DEFAULT_CSS = """
	$moulti_console_color: $accent;
	MoultiConsole {
		Label {
			width: 100%;
			background: $moulti_console_color;
			color: auto;
		}
		MoultiLog {
			min-height: 5;
			max-height: 15;
			border-bottom: none;
			border-top: none;
			border-right: thick $moulti_console_color;
			border-left: thick $moulti_console_color;
			scrollbar-corner-color: $moulti_console_color;
		}
		&.hidden {
			display: none;
		}
	}
	"""

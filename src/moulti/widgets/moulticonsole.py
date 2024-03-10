from typing import Any
from typing_extensions import Self
from pyperclip import copy # type: ignore
from rich.highlighter import Highlighter, RegexHighlighter, ReprHighlighter
from rich.text import Text
from rich.theme import Theme
from textual.app import ComposeResult
from textual.events import Click
from textual.widgets import Label, Static
from .moultilog import MoultiLog

MOULTI_THEME = Theme({
	'moulti.date': 'orchid2',
	'moulti.time': 'orchid2',
	'moulti.socket': 'steel_blue1',
	'moulti.fileno': 'orchid1',
	'moulti.function': 'slate_blue1',
	'moulti.messagein': 'bold dodger_blue2',
	'moulti.messageout': 'bold chartreuse3',
	# Redefine some repr.* styles to avoid ANSI colors:
	'repr.bool_true': 'green1',
	'repr.bool_false': 'deep_pink2',
	'repr.none': 'purple',
	'repr.number': 'cornflower_blue',
	'repr.str': 'sea_green3',
	'repr.attrib_name': 'dark_orange3',
})


class MoultiConsole(Static):
	BINDINGS = [
		("c", "to_clipboard(False)", "Copy"),
		("w", "to_clipboard(True)", "With colors"),
	]

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.log_widget = MoultiLog()
		self.log_widget.follow_ansi_theme = False
		self.log_widget.highlighter = MoultiConsoleHighlighter()
		self.log_widget.highlight = True

	def compose(self) -> ComposeResult:
		self.app.console.push_theme(MOULTI_THEME)
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

class MoultiRegexHighlighter(RegexHighlighter):
	RE_EXT_MODE = '(?x) # extended mode'
	DATE = r'''
(?P<date>
	[1-9][0-9]*-           # year
	(?:0[1-9]|1[0-2])-     # month
	(?:[012][0-9]|3[01])   # day
)'''
	TIME = r'''
(?P<time>
	(?:[01][0-9]|2[0-3]):  # hours
	(?:[0-5][0-9]):        # minutes
	(?:[0-5][0-9])\.       # seconds
	[0-9]+                 # milliseconds
)'''
	DATETIME = DATE + '[T ]' + TIME
	SOCKET = r'(?P<socket>[@/].*\.socket)'
	FILENO = r'fd(?P<fileno>\d+)'
	SOCKET_FILENO = SOCKET + ':' + FILENO
	FUNCTION = r'(?P<function>accept|exec|network loop|pass|read|reply|save)'
	MESSAGE_IN = r'(?P<messagein>=>)'
	MESSAGE_OUT = r'(?P<messageout><=)'
	MESSAGE = '(?:' + MESSAGE_IN + '|' + MESSAGE_OUT + ')'

	base_style: str = "moulti."
	highlights = [
		RE_EXT_MODE + '^' + DATETIME + ' ',
		' ' + SOCKET_FILENO + ': ',
		SOCKET,
		' ' + FUNCTION + ': ',
		': ' + MESSAGE + ' ',
	]

class MoultiConsoleHighlighter(Highlighter):
	SEPARATORS = (' => ', ' <= ', ' exec: ', ' theme policy: ')
	"""
	Everything to the right of these separators is to be highlighted by ReprHighlighter.
	Everything to the left of these separators is to be highlighted by MoultiRegexHighlighter.
	"""

	def __init__(self) -> None:
		self.repr_hl = ReprHighlighter()
		self.moulti_re_hl = MoultiRegexHighlighter()
		super().__init__()

	def highlight(self, text: Text) -> None:
		plain_text = text.plain
		for separator in self.SEPARATORS:
			if separator in plain_text:
				left, right = plain_text.split(separator, 1)
				# Highlight the left part (including the separator):
				text.set_length(len(left) + len(separator))
				self.moulti_re_hl.highlight(text)
				# Highlight the right part:
				right_text = Text(right)
				self.repr_hl.highlight(right_text)
				text.append_text(right_text)
				# All done:
				return
		# No separator? Highlight the entire string using MoultiRegexHighlighter:
		self.moulti_re_hl.highlight(text)

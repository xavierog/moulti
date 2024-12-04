from typing import Any
from typing_extensions import Self
from rich.highlighter import Highlighter, RegexHighlighter, ReprHighlighter
from rich.text import Text
from rich.theme import Theme
from textual.app import ComposeResult
from textual.events import MouseScrollUp, Click
from textual.widgets import Label, Log, Static
from moulti.clipboard import copy
from moulti.widgets.mixin import ToLinesMixin

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
		self.log_widget = MoultiConsoleLog()
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
			copy(self.app, '\n'.join(self.log_widget.to_lines(keep_styles)))
			title, message, res = 'Console copied!', 'Console lines copied to clipboard', True
		except Exception as exc:
			title, message, res = 'Failed to copy console!', str(exc), False
		self.app.notify(message, title=title, severity='information' if res else 'error')

	DEFAULT_CSS = """
	$moulti_console_color: $primary;
	MoultiConsole {
		Label {
			width: 100%;
			background: $moulti_console_color;
			color: auto;
		}
		MoultiConsoleLog {
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

class MoultiConsoleLog(Log, ToLinesMixin):
	"""
	Moulti's console leverages Log and its highlighter
	"""
	def watch_scroll_y(self, old_value: float, new_value: float) -> None:
		"""
		Adjust the behavior of the vertical scrollbar so users can scroll freely despite incoming new lines.
		"""
		# If users grab the vertical scrollbar, auto_scroll should turn off:
		if self.auto_scroll and self.is_vertical_scrollbar_grabbed:
			self.auto_scroll = False
		# ScrollView also implements this watch method: call it or it breaks the entire scrolling.
		super().watch_scroll_y(old_value, new_value)

	# pylint: disable=duplicate-code; copy/paste so as to get the same scrolling behaviour as MoultiLog.
	# Moving duplicate code to a common Mixin works but does not please mypy.
	def on_mouse_scroll_up(self, _: MouseScrollUp) -> None:
		"""Turn auto_scroll off as soon as users scroll up using the mouse wheel."""
		self.auto_scroll = False

	def action_scroll_up(self, *args: Any, **kwargs: Any) -> None:
		"""Turn auto_scroll off as soon as users hit the Up key."""
		self.auto_scroll = False
		super().action_scroll_up(*args, **kwargs)

	def action_page_up(self, *args: Any, **kwargs: Any) -> None:
		"""Turn auto_scroll off as soon as users hit the PgUp key."""
		self.auto_scroll = False
		super().action_page_up(*args, **kwargs)

	def action_scroll_home(self, *args: Any, **kwargs: Any) -> None:
		"""Turn auto_scroll off as soon as users hit the Home key."""
		self.auto_scroll = False
		super().action_scroll_home(*args, **kwargs)

	def action_scroll_end(self, *args: Any, **kwargs: Any) -> None:
		"""Turn auto_scroll on again as soon as users hit the End key."""
		self.auto_scroll = True
		super().action_scroll_end(*args, **kwargs)

	DEFAULT_CSS = """
	MoultiConsoleLog {
		height: auto;
		border-left: blank;
		background: $background;
	}
	MoultiConsoleLog:focus {
		border-left: thick $primary-lighten-3;
		background-tint: white 0%;
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
	SEPARATORS = (' => ', ' <= ', ' exec: ', ' theme policy: ', ' quit policy: ')
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

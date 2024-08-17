from typing import Any, Iterable
from typing_extensions import Self
from rich.text import Text
from textual.color import Color
from textual.events import MouseScrollUp, Click
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip
from moulti.widgets.mixin import ToLinesMixin

class MoultiLog(ScrollView, ToLinesMixin, can_focus=True):
	"""
	This widget is a lightweight variant of RichLog with:
	- the ability to use the App's ANSI theme (background and foreground)
	- custom scrolling behaviour
	- a focus indicator on the left
	"""
	def __init__(
		self,
		*,
		auto_scroll: bool = True,
		name: str | None = None,
		id: str | None = None,  # pylint: disable=redefined-builtin
		classes: str | None = None,
		disabled: bool = False,
	) -> None:
		super().__init__(name=name, id=id, classes=classes, disabled=disabled)
		self.lines: list[str|Text|Strip] = []
		self.max_width: int = 0
		self.auto_scroll = self.default_auto_scroll = auto_scroll
		self.follow_ansi_theme = True

	def on_mount(self) -> None:
		if self.follow_ansi_theme:
			self.watch(self.app, 'dark', self.apply_ansi_fgbg)

	def apply_ansi_fgbg(self, _old: bool, _new: bool) -> None:
		theme = self.app.ansi_theme
		self.styles.auto_color = False
		self.styles.color = Color(*theme.foreground_color)
		self.styles.background = Color(*theme.background_color)

	def watch_scroll_y(self, old_value: float, new_value: float) -> None:
		"""
		Adjust the behavior of the vertical scrollbar so users can scroll freely despite incoming new lines.
		"""
		# If users grab the vertical scrollbar, auto_scroll should turn off:
		if self.auto_scroll and self.is_vertical_scrollbar_grabbed:
			self.auto_scroll = False
		# ScrollView also implements this watch method: call it or it breaks the entire scrolling.
		super().watch_scroll_y(old_value, new_value)

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
		self.auto_scroll = self.default_auto_scroll
		super().action_scroll_end(*args, **kwargs)

	def clear(self) -> Self:
		self.lines.clear()
		self.max_width = 0
		self.virtual_size = Size(self.max_width, len(self.lines))
		self.auto_scroll = self.default_auto_scroll
		self.refresh()
		return self

	async def on_click(self, event: Click) -> None:
		# Clicks grant focus to this widget; keep them.
		# See also: AbstractStep.on_click().
		event.stop()

	def write_lines(self, lines: Iterable[str|Text|Strip], max_cell_len: int) -> Self:
		if max_cell_len > self.max_width: # pylint: disable=consider-using-max-builtin
			self.max_width = max_cell_len
		self.lines.extend(lines)

		self.virtual_size = Size(self.max_width, len(self.lines))
		if self.auto_scroll:
			self.scroll_end(animate=False)

		return self

	def render_line(self, y: int) -> Strip:
		scroll_x, scroll_y = self.scroll_offset
		if scroll_y + y >= len(self.lines):
			return Strip.blank(self.size.width, self.rich_style)
		line = self.line_to_strip(scroll_y + y, True)
		line = line.crop_extend(scroll_x, scroll_x + self.size.width, self.rich_style)
		return line.apply_style(self.rich_style)

	DEFAULT_CSS = """
	MoultiLog {
		background: $surface;
		color: $text;
		overflow-y: scroll;
		height: auto;
		border-left: blank;
	}
	MoultiLog:focus {
		border-left: thick $accent-lighten-3;
	}
	"""

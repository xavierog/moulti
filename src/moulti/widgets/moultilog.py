from typing import Any, Iterable
from typing_extensions import Self
from rich.text import Text
from textual.color import Color
from textual.events import MouseScrollUp, Click
from textual.geometry import Region, Size, Spacing
from textual.scroll_view import ScrollView
from textual.strip import Strip
from moulti.search import MatchSpan, TextSearch
from moulti.widgets.mixin import ToLinesMixin

class MoultiLog(ScrollView, ToLinesMixin, can_focus=True):
	"""
	This widget is a lightweight variant of RichLog with:
	- the ability to use the App's ANSI theme (background and foreground)
	- custom scrolling behaviour
	- a focus indicator on the left
	"""
	BINDINGS = [
		("f", "maximize", "Maximize"),
		("f", "minimize", "Exit maximized mode"),
	]

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
		self.search_cursor: tuple[int|None, MatchSpan] = (None, None)
		self.searched_line_backup: tuple[int, str|Text|Strip] = (-1, '')
		self.max_height_backup: Any = None

	def set_max_height(self, new_max_height: int|None) -> int|None:
		if new_max_height is None:
			actual_max_height = new_max_height
		else:
			actual_max_height = new_max_height if new_max_height > 0 else None

		if self.is_maximized:
			# Maximized mode should ignore `moulti step update id --max-height=42`:
			self.max_height_backup = actual_max_height
		else:
			self.styles.max_height = actual_max_height

		return actual_max_height

	def action_maximize(self) -> None:
		self.max_height_backup = self.styles.max_height
		self.styles.max_height = '99h' # Leave some room for the search widget
		self.screen.maximize(self, False)
		self.refresh_bindings()

	def action_minimize(self) -> None:
		self.screen.minimize()
		self.styles.max_height = self.max_height_backup
		self.refresh_bindings()

	def check_action(self, action: str, parameters: tuple[object, ...]) -> bool:
		if action == 'maximize':
			return not bool(self.screen.maximized)
		if action == 'minimize':
			return bool(self.screen.maximized)
		return True

	def clear_search(self) -> None:
		self.search_cursor = (None, None)
		self.searched_line_backup = (-1, '')

	def on_mount(self) -> None:
		if self.follow_ansi_theme:
			self.watch(self.app, 'dark', self.apply_ansi_fgbg)

	def on_unmount(self) -> None:
		if self.is_maximized:
			self.action_minimize()

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
		self.clear_search()
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

	def backup_line(self, line_number: int) -> None:
		line = self.lines[line_number]
		# str and Strip are immutable but Text is mutable and thus must be explicitly copied:
		backup_line = line.copy() if isinstance(line, Text) else line
		self.searched_line_backup = (line_number, backup_line)

	def restore_line(self, line_number: int) -> None:
		backup_line_number, backup_line = self.searched_line_backup
		if line_number != backup_line_number:
			return
		restore_line = backup_line.copy() if isinstance(backup_line, Text) else backup_line
		self.lines[line_number] = restore_line

	def search_one_line(self, search: TextSearch) -> bool:
		line_number, highlight = self.search_cursor
		assert line_number is not None
		first_occurrence_on_this_line = highlight is None
		self.restore_line(line_number)
		plain_text, text = self.line_to_plain_text(line_number, True)
		result = search.search(plain_text, highlight)
		if result is None:
			self.restore_line(line_number)
			self.refresh()
			return False
		# Occurrence found!
		self.search_cursor = (line_number, result)
		# Highlight:
		if text is None:
			text = self.line_to_text(line_number, True)
		if first_occurrence_on_this_line:
			self.backup_line(line_number)
		self.lines[line_number] = search.highlight(text, *result)
		return True

	def search(self, search: TextSearch) -> bool:
		if search.reset():
			if (line_number := self.search_cursor[0]) is not None:
				self.restore_line(line_number)
				self.refresh()
				self.clear_search()
			return False
		if search.next_result:
			first_line, next_line = 0, 1
		else:
			first_line, next_line = len(self.lines) - 1, -1
		if self.search_cursor[0] is None:
			self.search_cursor = (first_line, None)
		line_number = self.search_cursor[0]
		assert line_number is not None
		while 0 <= line_number < len(self.lines):
			if self.search_one_line(search):
				return True
			line_number += next_line
			self.search_cursor = (line_number, None)
		self.clear_search()
		return False

	def scroll_to_search_highlight(self) -> tuple[Region, Spacing]|None:
		line_number, highlight = self.search_cursor
		if line_number is None or highlight is None:
			return None
		highlight_region = Region(
			highlight[0],
			line_number,
			highlight[1] - highlight[0],
			1
		)
		highlight_spacing = Spacing(1, 5, 1, 10)
		self.auto_scroll = False
		self.scroll_to_region(highlight_region, spacing=highlight_spacing, animate=False)
		self.refresh()
		# Return the highlighted region relatively to this widget:
		highlight_region = highlight_region.translate(-self.scroll_offset)
		return highlight_region, highlight_spacing

	DEFAULT_CSS = """
	MoultiLog {
		background: $surface;
		color: $text;
		overflow-y: scroll;
		height: auto;
		border-left: blank;
	}
	MoultiLog:focus {
		border-left: thick $primary-lighten-3;
	}
	"""

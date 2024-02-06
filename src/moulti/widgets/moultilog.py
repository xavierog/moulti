from typing import Any
from typing_extensions import Self
from textual.events import MouseScrollUp
from textual.geometry import Size
from textual.widgets import RichLog

class MoultiLog(RichLog):
	"""
	This widget is a variant of RichLog that tries to prevent vertical
	scrollbars when max-height is not set.
	"""
	def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
		height = super().get_content_height(container, viewport, width)
		if self.show_horizontal_scrollbar:
			# When RichLog is assigned "height: auto;", the horizontal
			# scrollbar consumes lines from the widget itself, resulting in
			# the apparition of a vertical scrollbar.
			height += self.styles.scrollbar_size_horizontal
		return height

	def clear(self) -> Self:
		self.auto_scroll = True
		return super().clear()

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
		self.auto_scroll = True
		super().action_scroll_end(*args, **kwargs)

	DEFAULT_CSS = """
	MoultiLog {
		height: auto;
	}
	"""
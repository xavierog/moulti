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

	DEFAULT_CSS = """
	MoultiLog {
		height: auto;
	}
	"""

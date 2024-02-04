from textual.containers import VerticalScroll

class VertScroll(VerticalScroll):
	"""
	Variant of Textual's VerticalScroll container that bears the
	"vertical_scrollbar_visible" class when its vertical scrollbar is visible.
	"""
	def watch_show_vertical_scrollbar(self) -> None:
		self.set_class(self.show_vertical_scrollbar, 'vertical_scrollbar_visible')

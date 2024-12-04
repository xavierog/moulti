from typing import Any
from typing_extensions import Self
from textual.app import ComposeResult
from textual.events import Click
from textual.widget import Widget
from textual.widgets import Static, Collapsible
from moulti.search import TextSearch
from ..abstractstep.tui import AbstractStep

SEARCH_RESET = 0
SEARCH_TITLE = 1
SEARCH_TOP_TEXT = 2
SEARCH_SUBWIDGETS = 3
SEARCH_BOTTOM_TEXT = 4

class MoultiCollapsible(Collapsible):
	"""
	Moulti-specific variant of Textual's Collapsible widget.
	"""

	def _watch_collapsed(self, collapsed: bool) -> None:
		"""Override so as not to scroll when expanding."""
		self._update_collapsed(collapsed)
		message = self.Collapsed(self) if self.collapsed else self.Expanded(self)
		self.post_message(message)

class CollapsibleStep(AbstractStep):
	"""
	This is the base class for all collapsible components end users may wish to
	add to Moulti.
	"""

	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		self.collapsible = MoultiCollapsible(title=id)
		self.top_label = Static('', classes='top_text')
		self.bottom_label = Static('', classes='bottom_text')
		self.search_cursor = SEARCH_RESET

		self.top_text = ''
		self.bottom_text = ''

		super().__init__(id=id, **kwargs)

	def subcompose(self) -> ComposeResult:
		return []

	def compose(self) -> ComposeResult:
		with self.collapsible:
			yield self.top_label
			yield from self.subcompose()
			yield self.bottom_label

	def subsearch(self, _: TextSearch) -> bool:
		return False

	def search_part(self, search: TextSearch) -> tuple[bool, Widget|None]:
		if self.search_cursor == SEARCH_TITLE:
			found, text = self.search_label(self.title, search)
			self.collapsible.title = text.markup
			widget = self.query_one('CollapsibleTitle') if found else None
			return found, widget
		if self.search_cursor == SEARCH_TOP_TEXT:
			found, text = self.search_label(self.top_text, search)
			self.top_label.update(text)
			widget = self.top_label if found else None
			return found, widget
		if self.search_cursor == SEARCH_BOTTOM_TEXT:
			found, text = self.search_label(self.bottom_text, search)
			self.bottom_label.update(text)
			widget = self.bottom_label if found else None
			return found, widget
		if self.search_cursor == SEARCH_SUBWIDGETS:
			return self.subsearch(search), None
		return False, None

	def search(self, search: TextSearch) -> bool:
		found = False
		widget = None
		if search.reset():
			if self.search_cursor != SEARCH_RESET:
				self.search_part(search)
			self.search_cursor = SEARCH_RESET
			return False
		if search.next_result:
			parts = (SEARCH_TITLE, SEARCH_TOP_TEXT, SEARCH_SUBWIDGETS, SEARCH_BOTTOM_TEXT, SEARCH_RESET)
		else:
			parts = (SEARCH_BOTTOM_TEXT, SEARCH_SUBWIDGETS, SEARCH_TOP_TEXT, SEARCH_TITLE, SEARCH_RESET)
		if self.search_cursor == SEARCH_RESET:
			self.search_cursor = parts[0]
		while self.search_cursor != SEARCH_RESET:
			found, widget = self.search_part(search)
			if found:
				break
			self.search_cursor = parts[parts.index(self.search_cursor) + 1]
		if found:
			# Expand this collapsible step if necessary:
			if self.search_cursor != SEARCH_TITLE:
				self.collapsible.collapsed = False
			# Grab the focus, except for subwidgets, which have to grab focus explicitly:
			if self.search_cursor != SEARCH_SUBWIDGETS:
				self.focus(False)
			# Scroll to make the highlighted result visible:
			if widget is not None:
				self.post_message(self.ScrollRequest(self, widget, center=True, animate=False))
		return found

	def on_mount(self) -> None:
		self.query_one('CollapsibleTitle').tooltip = f'Step id: {self.title_from_id()}'

	def focus(self, scroll_visible: bool = True) -> Self:
		self.query_one('CollapsibleTitle').focus(scroll_visible)
		return self

	async def on_click(self, _: Click) -> None:
		"""
		Steps are meant to be focusable but it is actually the CollapsibleTitle that holds the focus.
		"""
		self.focus()

	def check_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		self.check_markup_dict(kwargs, 'top_text', 'bottom_text')
		super().check_properties(kwargs)

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		if 'collapsed' in kwargs:
			self.collapsible.collapsed = bool(kwargs['collapsed'])
		if 'top_text' in kwargs:
			self.top_text = str(kwargs['top_text'])
			self.top_label.update(self.top_text)
		self.top_label.styles.display = 'block' if self.top_text else 'none'
		if 'bottom_text' in kwargs:
			self.bottom_text = str(kwargs['bottom_text'])
			self.bottom_label.update(self.bottom_text)
		self.bottom_label.styles.display = 'block' if self.bottom_text else 'none'
		super().update_properties(kwargs)
		self.collapsible.title = self.title

	def export_properties(self) -> dict[str, Any]:
		prop = super().export_properties()
		prop['collapsed'] = self.collapsible.collapsed
		prop['top_text'] = self.top_text
		prop['bottom_text'] = self.bottom_text
		return prop

	DEFAULT_CSS = AbstractStep.DEFAULT_CSS + """
	CollapsibleStep {
		/* Compact design: no padding, no margins, no borders: */
		& Collapsible {
			/* Inherit the parent background instead of altering it via $boost: */
			background: initial;
			padding: 0;
			margin: 0;
			border: none;
		}
		& CollapsibleTitle {
			padding: 0;
			color: $text;
			width: 100%;
		}
		& CollapsibleTitle:focus {
			background: initial;
			color: $text;
			text-style: none;
		}
		& CollapsibleTitle:hover {
			background: $foreground 80%;
			color: $text;
			text-style: none;
		}
		/* Collapsible contents: */
		& Contents {
			/* Leave some space on each side of the contents: */
			padding-left: 2 !important;
			padding-right: 1 !important;
		}
	}
	"""

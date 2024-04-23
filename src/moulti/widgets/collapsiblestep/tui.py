from typing import Any
from textual.app import ComposeResult
from textual.events import Click
from textual.widgets import Static, Collapsible
from ..abstractstep.tui import AbstractStep

class CollapsibleStep(AbstractStep):
	"""
	This is the base class for all collapsible components end users may wish to
	add to Moulti.
	"""

	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		self.collapsible = Collapsible(title=id)
		self.top_label = Static('', classes='top_text')
		self.bottom_label = Static('', classes='bottom_text')

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

	def on_mount(self) -> None:
		self.query_one('CollapsibleTitle').tooltip = f'Step id: {self.title_from_id()}'

	async def on_click(self, _: Click) -> None:
		"""
		Steps are meant to be focusable but it is actually the CollapsibleTitle that holds the focus.
		"""
		self.query_one('CollapsibleTitle').focus()

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
			width: 100%;
		}
		& CollapsibleTitle:focus {
			background: initial;
		}
		& CollapsibleTitle:hover {
			background: $foreground 80%;
		}
		/* Collapsible contents: */
		& Contents {
			/* Leave some space on each side of the contents: */
			padding-left: 2 !important;
			padding-right: 1 !important;
		}
	}
	"""

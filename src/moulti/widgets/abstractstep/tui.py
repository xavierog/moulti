import json
from typing import Any, Callable
from pyperclip import copy # type: ignore
from textual.app import ComposeResult
from textual.events import Click
from textual.widgets import Static, Collapsible

class AbstractStep(Static):
	"""
	This is the base class for all components end users may wish to add to Moulti.
	"""
	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		self.collapsible = Collapsible(title=id)
		self.top_label = Static('', classes='top_text')
		self.bottom_label = Static('', classes='bottom_text')

		self.top_text = ''
		self.bottom_text = ''

		# This attribute is meant to prevent deletion of a step while content
		# is being appended to it:
		self.prevent_deletion = 0

		self.init_kwargs = kwargs

		step_classes = str(kwargs.get('classes', ''))
		super().__init__(id='step_' + id, classes=step_classes)

	def subcompose(self) -> ComposeResult:
		return []

	def compose(self) -> ComposeResult:
		with self.collapsible:
			yield self.top_label
			yield from self.subcompose()
			yield self.bottom_label

	def on_mount(self) -> None:
		self.update_properties(self.init_kwargs)

	async def on_click(self, _: Click) -> None:
		"""
		Steps are meant to be focusable but it is actually the CollapstibleTitle that holds the focus.
		"""
		if hasattr(self.collapsible, '_title'):
			self.collapsible._title.focus() # pylint: disable=protected-access

	def title_from_id(self) -> str:
		self_id = str(self.id)
		if '_' not in self_id:
			return self_id
		return self_id.split('_', 1)[1]

	def index(self) -> int:
		if self.parent is not None:
			return self.parent.children.index(self) + 1
		return -1

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		if 'classes' in kwargs:
			self.set_classes(str(kwargs['classes']))
		if 'title' in kwargs:
			self.collapsible.title = str(kwargs['title']) if kwargs['title'] else self.title_from_id()
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

	def export_properties(self) -> dict[str, Any]:
		prop: dict[str, Any] = {}
		prop['id'] = self.title_from_id()
		prop['classes'] = ' '.join(self.classes)
		prop['title'] = self.collapsible.title
		prop['collapsed'] = self.collapsible.collapsed
		prop['top_text'] = self.top_text
		prop['bottom_text'] = self.bottom_text
		return prop

	def save(self, opener: Callable[[str, int], int], filename: str, extra_properties: dict[str, Any]) -> None:
		properties = {**extra_properties, **self.export_properties()}
		with open(filename + '.properties.json', 'w', encoding='utf-8', opener=opener) as properties_filedesc:
			json.dump(properties, properties_filedesc, indent=4)
			properties_filedesc.write('\n')

	def notify_copy_to_clipboard(self, result: bool, explanation: str) -> None:
		step_index = self.index()
		title = f'Step #{step_index} copied!' if result else f'Failed to copy step #{step_index}'
		if explanation:
			message = explanation
		elif result:
			message = f'Step #{step_index} copied to clipboard'
		else:
			message = f'Could not copy step #{step_index} to clipboard'
		self.app.notify(message, title=title, severity='information' if result else 'error')

	@staticmethod
	def copy_to_clipboard(func: Callable) -> Callable:
		def wrapper(self: AbstractStep, *args: Any, **kwargs: Any) -> None:
			try:
				result, data, explanation = func(self, *args, **kwargs)
				if result:
					copy(data)
			except Exception as exc:
				result, explanation = False, str(exc)
			self.notify_copy_to_clipboard(result, explanation)
		return wrapper

	DEFAULT_COLORS = """
	$step_default: $primary;
	$step_success: ansi_bright_green;
	$step_warning: orange;
	$step_error: tomato;
	"""
	DEFAULT_CSS = DEFAULT_COLORS + """
	AbstractStep {
		/* If we do not specify "auto" here, each step will take 100% of the viewport: */
		height: auto;
		background: $step_default;
		border-left: blank;
		color: auto;
		&.success { background: $step_success; }
		&.warning { background: $step_warning; }
		&.error { background: $step_error; }
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
	AbstractStep:focus, AbstractStep:focus-within {
		border-left: thick $accent-lighten-3;
	}
	"""

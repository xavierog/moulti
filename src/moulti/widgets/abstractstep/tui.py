import json
from operator import attrgetter
from typing import Any, Callable
from pyperclip import copy # type: ignore
from rich.errors import MarkupError
from textual.message import Message
from textual.widgets import Static

class AbstractStep(Static):
	"""
	This is the base class for all components end users may wish to add to Moulti.
	"""

	class StepActivity(Message):
		def __init__(self, step: 'AbstractStep', *args: Any, **kwargs: Any):
			self.step = step
			super().__init__(*args, **kwargs)

	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		self.title = id

		# This attribute is meant to prevent deletion of a step while content
		# is being appended to it:
		self.prevent_deletion = 0

		self.scroll_on_activity: bool|int = False
		self.check_properties(kwargs)
		self.init_kwargs = kwargs

		step_classes = str(kwargs.get('classes', ''))
		super().__init__(id='step_' + id, classes=step_classes)

	def on_mount(self) -> None:
		self.update_properties(self.init_kwargs)

	def title_from_id(self) -> str:
		self_id = str(self.id)
		if '_' not in self_id:
			return self_id
		return self_id.split('_', 1)[1]

	def index(self) -> int:
		if self.parent is not None:
			return sorted(self.parent.children, key=attrgetter('sort_order')).index(self) + 1
		return -1

	def check_markup(self, value: str|int|bool) -> None:
		value = str(value)
		text = self.render_str(value)
		# Extra check to work around https://github.com/Textualize/textual/issues/4248:
		for span in text.spans:
			if hasattr(span.style, 'meta') and span.style.meta.get('@click') == ():
				raise MarkupError('problematic @click tag')

	def check_markup_dict(self, check_dict: dict[str, str|int|bool], *keys: str) -> None:
		for key in keys:
			if key in check_dict:
				self.check_markup(check_dict[key])

	def check_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		self.check_markup_dict(kwargs, 'title')

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		if 'classes' in kwargs:
			self.set_classes(str(kwargs['classes']))
		if 'title' in kwargs:
			self.title = str(kwargs['title']) if kwargs['title'] else self.title_from_id()
		if 'scroll_on_activity' in kwargs:
			scroll_on_activity = kwargs['scroll_on_activity']
			if isinstance(scroll_on_activity, int):
				self.scroll_on_activity = scroll_on_activity
			else:
				self.scroll_on_activity = bool(scroll_on_activity)

	def export_properties(self) -> dict[str, Any]:
		prop: dict[str, Any] = {}
		prop['id'] = self.title_from_id()
		prop['classes'] = ' '.join(self.classes)
		prop['title'] = self.title
		prop['scroll_on_activity'] = self.scroll_on_activity
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

	def activity(self) -> None:
		msg = AbstractStep.StepActivity(self)
		self.call_after_refresh(self.post_message, msg)

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
	}
	AbstractStep:focus, AbstractStep:focus-within {
		border-left: thick $accent-lighten-3;
	}
	"""

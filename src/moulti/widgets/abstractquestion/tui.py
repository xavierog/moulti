from typing import Any
from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static
from moulti.search import TextSearch
from ..collapsiblestep.tui import CollapsibleStep

class AbstractQuestion(CollapsibleStep):
	"""
	This widget represents an interactive question in a script, program or process.
	"""
	def __init__(self, id: str, **kwargs: str|int|bool): # pylint: disable=redefined-builtin
		self.question = ''
		self.question_label = Static(self.question, classes='question_text')
		self.answer: str|None = None
		self.waiting: list[Any] = []
		super().__init__(id=id, **kwargs)

	def cli_action_get_answer(self, kwargs: dict[str, str|int|bool], helpers: dict[str, Any]) -> tuple:
		if self.answer is None:
			if kwargs.get('wait'):
				self.waiting.append((kwargs, helpers))
			else:
				helpers['reply'](done=False, error='answer not available yet')
		else:
			helpers['reply'](answer=self.answer, done=True, error=None)
		return ()

	@work(thread=True, group='question-flush', name='flush-answers')
	def flush_waiting_clients(self) -> None:
		for _kwargs, helpers in self.waiting:
			try:
				if self.answer is None:
					helpers['reply'](done=False, error='no answer from end user')
				else:
					helpers['reply'](done=True, error=None, answer=self.answer)
			except Exception as exc:
				error = str(exc)
				helpers['debug'](f'flush_waiting_clients: {error}')
		self.waiting.clear()

	def subcompose(self) -> ComposeResult:
		yield self.question_label
		yield from self.compose_question()

	def subsearch(self, search: TextSearch) -> bool:
		found, text = self.search_label(self.question, search)
		self.question_label.update(text)
		if found:
			self.focus(False)
			self.post_message(self.ScrollRequest(self, self.question_label, center=True, animate=False))
		return found

	def compose_question(self) -> ComposeResult:
		return []

	def check_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		super().check_properties(kwargs)
		self.check_markup_dict(kwargs, 'text')

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		super().update_properties(kwargs)
		if 'text' in kwargs:
			self.question = str(kwargs['text'])
			self.question_label.update(self.question)

	def export_properties(self) -> dict[str, Any]:
		prop = super().export_properties()
		prop['text'] = str(self.question_label.renderable)
		return prop

	def disable(self) -> None:
		for widget in self.collapsible.query('Collapsible > Contents Widget').results(Widget):
			if widget.focusable:
				widget.blur()
				widget.disabled = True

	def focus_input_widget(self) -> None:
		self.collapsible.collapsed = False
		for widget in self.collapsible.query('Collapsible > Contents Widget').results(Widget):
			if widget.focusable:
				widget.focus()
				break

	def got_answer(self, answer: str) -> None:
		# Disable the question to ensure users answer only once:
		self.disable()
		# Store the answer for future retrieval:
		self.answer = answer
		self.flush_waiting_clients()
		# Emit a GotAnswer message so other components react to the event:
		self.post_message(GotAnswer(self, self.answer))

	def answered(self) -> bool:
		return self.answer is not None

class GotAnswer(Message):
	def __init__(self, origin: AbstractQuestion, answer: str) -> None:
		self.origin = origin
		self.answer = answer
		super().__init__()

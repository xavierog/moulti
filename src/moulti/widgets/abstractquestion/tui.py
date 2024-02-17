from typing import Any
from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static
from ..abstractstep.tui import AbstractStep

class AbstractQuestion(AbstractStep):
	"""
	This widget represents an interactive question in a script, program or process.
	"""
	def __init__(self, id: str, **kwargs: str|int|bool): # pylint: disable=redefined-builtin
		self.question_label = Static('', classes='question_text')
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

	@work(thread=True)
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

	def compose_question(self) -> ComposeResult:
		return []

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		super().update_properties(kwargs)
		if 'text' in kwargs:
			self.question_label.update(str(kwargs['text']))

	def disable(self) -> None:
		for widget in self.collapsible.query('Collapsible > Contents').results():
			widget.disabled = True

	def got_answer(self, answer: str) -> None:
		# Disable the question to ensure users answer only once:
		self.disable()
		# Store the answer for future retrieval:
		self.answer = answer
		self.flush_waiting_clients()
		# Emit a GotAnswer message so other components react to the event:
		self.post_message(GotAnswer(self, self.answer))

class GotAnswer(Message):
	def __init__(self, origin: AbstractQuestion, answer: str) -> None:
		self.origin = origin
		self.answer = answer
		super().__init__()
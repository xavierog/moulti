from typing import Any
from textual.app import ComposeResult
from textual.widgets import Input
from ..abstractquestion.tui import AbstractQuestion

class InputQuestion(AbstractQuestion):
	"""
	This widget represents an interactive question in a script, program or process.
	"""
	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		super().__init__(id='step_' + id, **kwargs)
		self.input = Input()

	def compose_question(self) -> ComposeResult:
		yield self.input

	def on_input_submitted(self, event: Input.Submitted) -> None:
		answer = event.input.value
		if answer is not None:
			self.got_answer(answer)

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		super().update_properties(kwargs)
		if 'placeholder' in kwargs:
			self.input.placeholder = str(kwargs['placeholder'])
		if 'value' in kwargs:
			self.input.value = str(kwargs['value'])
		if 'password' in kwargs:
			self.input.password = bool(kwargs['password'])
		if 'max_length' in kwargs:
			try:
				max_length = int(kwargs['max_length'])
				self.input.max_length = None if max_length == 0 else max_length
			except (ValueError, TypeError):
				pass
		if 'restrict' in kwargs:
			self.input.restrict = None if not kwargs['restrict'] else str(kwargs['restrict'])

MoultiWidgetClass = InputQuestion

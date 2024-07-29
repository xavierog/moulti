from typing import Any
from textual.app import ComposeResult
from textual.widgets import Button
from ..buttonquestion.tui import ButtonQuestion
from ..inputquestion.tui import InputQuestion

class Question(ButtonQuestion, InputQuestion):
	"""
	This widget represents an interactive question in a script, program or process.
	It combines the abilities of InputQuestion (single input field) and ButtonQuestion (buttons).
	"""

	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		ButtonQuestion.__init__(self, id=id, **kwargs)
		InputQuestion.__init__(self, id=id, **kwargs)

	def compose_question(self) -> ComposeResult:
		yield from InputQuestion.compose_question(self)
		yield from ButtonQuestion.compose_question(self)

	def on_button_pressed(self, event: Button.Pressed) -> None:
		# Do not call ButtonQuestion.on_button_pressed():
		event.prevent_default()
		answer = event.button.name
		if answer is not None:
			answer = answer.replace('{input}', self.input.value)
			self.got_answer(answer)

	def check_properties(self, kwargs: dict[str, Any]) -> None:
		ButtonQuestion.check_properties(self, kwargs)
		InputQuestion.check_properties(self, kwargs)

	def export_properties(self) -> dict[str, Any]:
		return {
			**InputQuestion.export_properties(self),
			**ButtonQuestion.export_properties(self)
		}

MoultiWidgetClass = Question

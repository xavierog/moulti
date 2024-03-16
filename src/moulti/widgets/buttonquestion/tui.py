from typing import Any
from textual.app import ComposeResult
from textual.events import Resize
from textual.containers import Horizontal
from textual.reactive import Reactive
from textual.widgets import Button, Static
from ..abstractquestion.tui import AbstractQuestion

DEFAULT_BUTTONS = [
	['yes', 'success', 'Yes'],
	['no', 'error', 'No'],
	['cancel', 'primary', 'Cancel'],
]

class ButtonQuestion(AbstractQuestion):
	"""
	This widget represents an interactive question in a script, program or process.
	"""

	BINDINGS = [
		("c", "to_clipboard(False)", "Copy"),
		("w", "to_clipboard(True)", "With question"),
	]

	known_width = Reactive(-1)

	def __init__(self, id: str, **kwargs: Any): # pylint: disable=redefined-builtin
		super().__init__(id=id, **kwargs)
		self.button_layout: list[int] = []
		self.button_sizes: list[int]|None = None
		self.regenerate_buttons()
		self.vertical = Static(classes='buttons')

	def regenerate_buttons(self) -> None:
		self.buttons = []
		disabled = self.answer is not None
		for value, classes, label in self.init_kwargs.get('button', DEFAULT_BUTTONS):
			self.buttons.append(Button(label, variant=classes, name=value, disabled=disabled))

	def compose_question(self) -> ComposeResult:
		with self.vertical:
			# Initial layout: all buttons in a single row:
			with Horizontal():
				yield from self.buttons

	def on_button_pressed(self, event: Button.Pressed) -> None:
		answer = event.button.name
		if answer is not None:
			self.got_answer(answer)

	def check_properties(self, kwargs: dict[str, Any]) -> None:
		super().check_properties(kwargs)
		for _, _, label in kwargs.get('button', []):
			self.check_markup(label)

	def export_properties(self) -> dict[str, Any]:
		prop = super().export_properties()
		# Buttons cannot be updated so we can simply export the value found in init_kwargs:
		prop['button'] = self.init_kwargs.get('button', DEFAULT_BUTTONS)
		return prop

	@AbstractQuestion.copy_to_clipboard
	def action_to_clipboard(self, with_question: bool = False) -> tuple[bool, str, str]:
		if self.answer is None:
			return False, '', 'Answer not available yet'
		data = f'Q: {self.question()}\nA: {self.answer}\n' if with_question else self.answer
		return True, data, ''

	def measure_buttons(self) -> None:
		if self.button_sizes is None:
			# Harvest current button sizes:
			self.button_sizes = [button.size.width + button.styles.margin.right for button in self.buttons]

	def compute_button_layout(self, width: int = -1) -> list[int]:
		"""
		Return a list of integers representing how many buttons each row should contain.
		"""
		width = self.query('Contents').first().size.width if width == -1 else width
		width -= self.buttons[0].styles.margin.left
		self.measure_buttons()
		rows = []
		row = 0
		row_width = width
		assert self.button_sizes
		for button_width in self.button_sizes:
			if button_width > row_width and row:
				rows.append(row)
				row = 0
				row_width = width
			row += 1
			row_width -= button_width
		rows.append(row)
		width = self.query('Contents').first().size.width
		return rows

	async def apply_button_layout(self, new_layout: list[int]) -> None:
		"""
		Given a list of integers representing how many buttons each row should contain, reorganise the inner containers
		and buttons to achieve that state.
		"""
		# Important: during the removal, it is essential to enforce the height so the widget does not shrink down and
		# potentially triggers the removal of vertical scroll bars on the parent container (which, in turn, would
		# trigger a loop of resize events).
		self.vertical.styles.height = len(new_layout) * 5 # number of rows × height of a Horizontal container (see CSS)
		removal = self.vertical.remove_children()
		self.regenerate_buttons()
		horizontals = []
		i = 0
		for row in new_layout:
			horizontals.append(Horizontal(*self.buttons[i:i+row]))
			i += row
		await removal
		self.vertical.mount_all(horizontals)

	async def watch_known_width(self, _old_width: int, _new_width: int) -> None:
		"""
		Compute and apply a new layout for buttons whenever the width changes.
		"""
		# Do nothing if we ignore our width:
		if self.known_width == -1:
			return
		# Do not bother for zero or one button:
		if len(self.buttons) <= 1:
			return
		# Do not bother if this widget is collapsed:
		if self.collapsible.collapsed:
			# Discard the known width to force a change when this widget is expanded again:
			self.known_width = -1
			return
		# Recompute the layout:
		new_layout = self.compute_button_layout()
		# Do not bother if the layout did not change:
		if new_layout == self.button_layout:
			return
		self.button_layout = new_layout
		await self.apply_button_layout(new_layout)

	def on_resize(self, event: Resize) -> None:
		if self.known_width != event.size.width:
			self.known_width = event.size.width

	DEFAULT_CSS = """
		Static.buttons {
			layout: vertical;
			&> Horizontal {
				align: center middle;
				height: 5; /* Button height + margin */
				&> Button { margin-right: 2; margin-left: 2; margin-top: 1; margin-bottom: 1; }
			}
		}
	"""
MoultiWidgetClass = ButtonQuestion

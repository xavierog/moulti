from typing import Any
from textual.app import ComposeResult
from textual.events import Resize
from textual.containers import Horizontal
from textual.reactive import Reactive
from textual.widgets import Button, Static
from ..abstractquestion.tui import AbstractQuestion
from .. import MoultiWidgetInvalidPropertyException

DEFAULT_BUTTONS = [
	['yes', 'success', 'Yes'],
	['no', 'error', 'No'],
	['cancel', 'primary', 'Cancel'],
]

DUMMY_BUTTON = Button()

def check_button_variant(variant: str) -> bool:
	try:
		Button.validate_variant(DUMMY_BUTTON, variant)
		return True
	# The actual exception is private:
	except Exception as exc:
		msg = f"invalid style '{variant}'. {exc}"
		raise MoultiWidgetInvalidPropertyException(msg) from exc

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
		for _, style, label in kwargs.get('button', []):
			check_button_variant(style)
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
		data = f'Q: {self.question}\nA: {self.answer}\n' if with_question else self.answer
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
		Given a list of integers representing how many buttons each row should contain, achieve that state by:
		- adding new Horizontal containers if needed
		- moving buttons
		- removing unnecessary Horizontal containers, if any
		"""
		horizontals = list(self.vertical.query('Horizontal').results())
		current_button_map: list[int] = []
		for horizontal_index, horizontal in enumerate(horizontals):
			current_button_map.extend(horizontal_index for _ in horizontal.query('Button').results())
		current_horizontal_count = max(current_button_map) + 1

		new_button_map: list[int] = []
		for horizontal_index, button_count in enumerate(new_layout):
			new_button_map.extend(horizontal_index for _ in range(button_count))
		new_horizontal_count = len(new_layout)

		buttons_to_move: dict[tuple[int, int], list[int]] = {}
		for button_index, current_horizontal_index in enumerate(current_button_map):
			new_horizontal_index = new_button_map[button_index]
			if current_horizontal_index != new_horizontal_index:
				move_direction = new_horizontal_index - current_horizontal_index
				move_direction //= abs(move_direction)
				buttons_to_move.setdefault((new_horizontal_index, move_direction), []).append(button_index)

		if not buttons_to_move:
			return

		# Add extra Horizontal containers if needed:
		if new_horizontal_count > current_horizontal_count:
			new_horizontals = list(Horizontal() for _ in range(current_horizontal_count, new_horizontal_count))
			horizontals.extend(new_horizontals)
			self.vertical.mount_all(new_horizontals)

		# Move buttons:
		disabled = self.answer is not None
		buttons_reference = self.init_kwargs.get('button', DEFAULT_BUTTONS)
		for movement, button_indices in buttons_to_move.items():
			fresh_buttons = []
			for button_index in button_indices:
				self.buttons[button_index].remove()
				button_value, button_classes, button_label = buttons_reference[button_index]
				fresh_button = Button(button_label, variant=button_classes, name=button_value, disabled=disabled)
				self.buttons[button_index] = fresh_button
				fresh_buttons.append(fresh_button)
			target_horizontal_index, direction = movement
			if direction > 0:
				horizontals[target_horizontal_index].mount_all(fresh_buttons, before=0)
			else:
				horizontals[target_horizontal_index].mount_all(fresh_buttons)

		# Remove unnecessary Horizontal containers, if any:
		if new_horizontal_count < current_horizontal_count:
			for horizontal_index in range(new_horizontal_count, current_horizontal_count):
				horizontals[horizontal_index].remove()

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

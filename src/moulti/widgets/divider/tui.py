from ..abstractstep.tui import AbstractStep

class Divider(AbstractStep, can_focus=True):
	"""
	Step that simply displays its title.
	"""

	BINDINGS = [
		("c", "to_clipboard", "Copy"),
	]

	def on_mount(self) -> None:
		self.tooltip = f'Step id: {self.title_from_id()}'

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		super().update_properties(kwargs)
		self.update(self.title)

	@AbstractStep.copy_to_clipboard
	def action_to_clipboard(self) -> tuple[bool, str, str]:
		lines_count = len(self.title.split('\n'))
		return True, self.title, f'copied {lines_count} lines, {len(self.title)} characters to clipboard'

	DEFAULT_CSS = AbstractStep.DEFAULT_CSS + """
	Divider {
		text-align: center;
		border-top: hkey yellow;
		border-bottom: hkey yellow;
	}
	"""
MoultiWidgetClass = Divider

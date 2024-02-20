from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label

class QuitDialog(ModalScreen):
	"""
	Modal dialog asking the user whether they actually want to quit Moulti,
	along with an optional extra message detailing why confirmation is required.
	Mostly based on https://textual.textualize.io/guide/screens/#modal-screens
	"""
	def __init__(self, message: str = '') -> None:
		self.message = message
		super().__init__()

	def compose(self) -> ComposeResult:
		base_message = 'Are you sure you want to quit Moulti?'
		if self.message:
			base_message += '\n' + self.message
		with Grid(id='quit_dialog_grid'):
			yield Label(base_message, id='quit_dialog_question')
			yield Button('Quit', variant='error', id='quit_dialog_quit_button')
			yield Button('Cancel', variant='primary', id='quit_dialog_cancel_button')

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'quit_dialog_quit_button':
			self.app.exit()
		else:
			self.app.pop_screen()

	DEFAULT_CSS = """
		QuitDialog {
			align: center middle;
			& Button {
				width: 100%;
			}
		}

		#quit_dialog_grid {
			grid-size: 2;
			grid-gutter: 1 2;
			grid-rows: 1fr 3;
			padding: 0 1;
			width: 60;
			height: 11;
			border: thick $background 80%;
			background: $surface;
		}

		#quit_dialog_question {
			column-span: 2;
			height: 1fr;
			width: 1fr;
			content-align: center middle;
		}

	"""

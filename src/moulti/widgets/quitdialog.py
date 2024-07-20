from textual.app import ComposeResult
from textual.containers import Grid
from textual.message import Message
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
			yield Button('Do not quit', variant='primary', id='do_not_quit')
			yield Button('Quit and leave the process running in the background', variant='warning', id='quit')
			yield Button('Terminate the process and quit', variant='error', id='terminate_and_quit')

	class ExitRequest(Message):
		def __init__(self, exit_first_policy: str):
			self.exit_first_policy = exit_first_policy
			super().__init__()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'do_not_quit':
			self.app.pop_screen()
		else:
			policy = 'terminate' if event.button.id == 'terminate_and_quit' else ''
			self.post_message(self.ExitRequest(policy))

	DEFAULT_CSS = """
		QuitDialog {
			align: center middle;
			& Button {
				width: 100%;
			}
		}

		#quit_dialog_grid {
			grid-size: 1 4;
			grid-gutter: 1 2;
			grid-rows: 1fr 1fr 1fr;
			padding: 0 1;
			width: 65;
			height: 18;
			border: thick $background 80%;
			background: $surface;
		}

		#quit_dialog_question {
			column-span: 2;
			height: 1fr;
			width: 100%;
			content-align: center middle;
		}
	"""

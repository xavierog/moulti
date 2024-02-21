from textual.app import ComposeResult
from textual.containers import Grid
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RadioSet, RadioButton

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
			yield Label(base_message, id='quit_dialog_question', classes='quit_dialog_question')
			yield RadioSet(
				RadioButton(
					'Quit and leave the process running in the background',
					value=True,
					id='quit_dialog_just_quit_option'),
				RadioButton('Terminate the process and quit', id='quit_dialog_terminate_option'),
				classes='quit_dialog_question',
				id='quit_dialog_options'
			)
			yield Button('Quit', variant='error', id='quit_dialog_quit_button')
			yield Button('Cancel', variant='primary', id='quit_dialog_cancel_button')

	def exit_first_policy(self) -> str:
		if self.query_one('#quit_dialog_terminate_option', RadioButton).value:
			return 'terminate'
		return ''

	class ExitRequest(Message):
		def __init__(self, exit_first_policy: str):
			self.exit_first_policy = exit_first_policy
			super().__init__()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'quit_dialog_quit_button':
			self.post_message(self.ExitRequest(self.exit_first_policy()))
		else:
			self.app.pop_screen()

	DEFAULT_CSS = """
		QuitDialog {
			align: center middle;
			& Button {
				width: 100%;
			}
			& RadioButton {
				padding: 1;
				width: 100%;
			}
		}

		#quit_dialog_grid {
			grid-size: 2 3;
			grid-gutter: 1 2;
			grid-rows: 1fr 2fr 3;
			padding: 0 1;
			width: 65;
			height: 18;
			border: thick $background 80%;
			background: $surface;
		}

		.quit_dialog_question {
			column-span: 2;
			height: 1fr;
			width: 100%;
			content-align: center middle;
		}

	"""

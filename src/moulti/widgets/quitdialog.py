from textual.app import ComposeResult
from textual.containers import Grid
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Label

class QuitDialog(ModalScreen):
	"""
	Modal dialog asking the user whether they actually want to quit Moulti,
	along with an optional extra message detailing why confirmation is required.
	Mostly based on https://textual.textualize.io/guide/screens/#modal-screens
	"""
	def __init__(self, message: str = '', allow_terminate: bool = False) -> None:
		self.message = message
		self.allow_terminate = allow_terminate
		self.quit_request_count = 1
		super().__init__()

	def compose(self) -> ComposeResult:
		base_message = 'Are you sure you want to quit Moulti?'
		if self.message:
			base_message += '\n' + self.message
		with Grid(id='quit_dialog_grid', classes='terminate' if self.allow_terminate else ''):
			yield Label(base_message, id='quit_dialog_question')
			yield Button('Do not quit (esc)', variant='primary', id='do_not_quit')
			if self.allow_terminate:
				yield Button('Quit and leave the process running in the background (l)', variant='warning', id='quit')
				yield Button('Terminate the process and quit (t)', variant='error', id='terminate_and_quit')
			else:
				yield Button('Quit (l)', variant='warning', id='quit')
			yield Label('', id='extra_info')

	class ExitRequest(Message):
		def __init__(self, exit_first_policy: str):
			self.exit_first_policy = exit_first_policy
			super().__init__()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == 'do_not_quit':
			self.app.pop_screen()
		else:
			policy = 'terminate' if event.button.id == 'terminate_and_quit' else ''
			self.exit(policy)

	def on_key(self, event: Key) -> None:
		buttons = {
			'escape': '#do_not_quit',
			'l': '#quit',
		}
		if self.allow_terminate:
			buttons['t'] = '#terminate_and_quit'
		if button_id := buttons.get(event.key.lower()):
			self.query_one(button_id, Button).action_press()

	def exit(self, policy: str) -> None:
		self.post_message(self.ExitRequest(policy))

	def new_quit_request(self) -> None:
		self.quit_request_count += 1
		if self.allow_terminate:
			if self.quit_request_count == 2:
				self.query_one('#quit').focus()
			elif self.quit_request_count == 3:
				x = self.query_one('#extra_info', Label)
				x.update('Hitting Ctrl+c again will terminate the process and quit.')
				self.query_one('#terminate_and_quit').focus()
			elif self.quit_request_count > 3:
				self.exit('terminate')
		else:
			if self.quit_request_count == 2:
				x = self.query_one('#extra_info', Label)
				x.update('Hitting Ctrl+c again will quit.')
				self.query_one('#quit').focus()
			elif self.quit_request_count == 3:
				self.exit('leave')

	DEFAULT_CSS = """
		QuitDialog {
			align: center middle;
			background: $surface 60%;
			& Button {
				width: 100%;
			}
		}
		#do_not_quit {
			background: $secondary;
		}

		#quit_dialog_grid {
			grid-size: 1 4;
			grid-gutter: 1 2;
			grid-rows: 1fr 1fr 1fr 1;
			padding: 0 1;
			width: 65;
			height: 15;
			border: thick $surface;
			background: $background;
			&.terminate { /* 1 extra button */
				grid-size: 1 5;
				grid-rows: 1fr 1fr 1fr 1fr 1;
				height: 19;
			}
		}

		#quit_dialog_question, #extra_info {
			height: 1fr;
			width: 100%;
			content-align: center middle;
		}
	"""

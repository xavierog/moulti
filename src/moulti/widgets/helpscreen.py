from textual.app import ComposeResult
from textual.events import Key, Click
from textual.screen import ModalScreen
from textual.widgets import Label

class HelpScreen(ModalScreen):
	"""
	Modal screen presenting the various keybindings available in Moulti.
	"""

	TEXT = """[u]Documentation[/]:
  https://github.com/xavierog/moulti/blob/master/Documentation.md

[u]Keybindings[/]:
  [key]tab[/], [key]shift+tab[/]: next/previous step/component
  [key]ctrl+y[/], [key]ctrl+t[/]: next/previous unanswered question
  [key]enter[/]: collapse/expand the current step
         submit the current input field
  [key]home[/], [key]pgup[/], [key]up[/], [key]down[/], [key]pgdn[/], [key]end[/]: vertical scroll
  [key]ctrl+pgup[/], [key]left[/], [key]right[/], [key]ctrl+pgdn[/]: horizontal scroll
  [key]l[/]: lock scroll: ignore programmatic scrolling
  [key]s[/]: save the current state to the filesystem
  [key]f[/]: maximize the focused log / exit maximized mode
  [key]z[/]: show/hide the console
  [key]o[/], [key]x[/]: collapse/expand existing steps
  [key]O[/], [key]X[/]: collapse/expand new steps
  [key]ctrl+o[/], [key]ctrl+x[/]: collapse/expand both existing and new steps
  [key]d[/]: switch between dark and light modes
  [key]c[/]: copy the contents of the current step
  [key]w[/]: same + preserve colors/include metadata (e.g. the question)
  [key]/[/], [key]?[/]: forward/backward text search
  [key]n[/], [key]N[/]: next/previous text search
  [key]q[/], [key]ctrl+c[/]: quit""".replace('[key]', '[bold #679cff on black]')

	def compose(self) -> ComposeResult:
		label = Label(self.TEXT, id='main_text')
		label.border_title = 'Moulti: help'
		label.border_subtitle = 'Press any key to dismiss this dialog'
		yield label

	def on_key(self, event: Key) -> None:
		"""
		Dismiss this screen if users press any key.
		"""
		event.stop()
		self.dismiss_if_active()

	def on_click(self, event: Click) -> None:
		"""
		Dismiss this screen if users click outside the panel.
		"""
		clicked_widget = self.get_widget_at(event.screen_x, event.screen_y)[0]
		if clicked_widget == self:
			event.stop()
			self.dismiss_if_active()

	def dismiss_if_active(self) -> None:
		if self.is_active:
			self.dismiss()

	DEFAULT_CSS = """
		HelpScreen {
			align: center middle;
			background: $surface 60%;
		}
		#main_text {
			padding: 1;
			background: $surface;
			border: panel $primary;
			border-title-color: #ffffff;
			border-title-align: center;
			border-subtitle-color: $text-muted;
		}
	"""

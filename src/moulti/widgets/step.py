from textual.widgets import Static, RichLog, Collapsible
from rich.text import Text

class Step(Static):
	"""
	This widget represents a step in a script, program or process.
	Visually speaking, it is essentially a collapsible text area surrounded
	with optional text lines.
	"""
	def __init__(self, id, **kwargs):
		self.collapsible = Collapsible(title=id)
		self.top_label = Static('', classes='top_text')
		self.log_widget = RichLog(highlight=False)
		self.bottom_label = Static('', classes='bottom_text')

		self.top_text = ''
		self.min_height = 1
		self.max_height = 25
		self.bottom_text = ''

		self.init_kwargs = kwargs
		# This attribute is meant to prevent deletion of a step while content
		# is being appended to it:
		self.prevent_deletion = 0
		super().__init__(id='step_' + id, classes=kwargs.get('classes', ''))

	def compose(self):
		with self.collapsible:
			yield self.top_label
			yield self.log_widget
			yield self.bottom_label

	def on_mount(self):
		self.update(self.init_kwargs)

	def update(self, kwargs):
		if 'classes' in kwargs:
			self.classes = kwargs['classes']
		if 'title' in kwargs:
			self.collapsible.title = kwargs['title'] if kwargs['title'] else self.id[5:]
		if 'collapsed' in kwargs:
			self.collapsible.collapsed = bool(kwargs['collapsed'])
		if 'top_text' in kwargs:
			self.top_text = kwargs['top_text']
			self.top_label.update(self.top_text)
		self.top_label.styles.display = 'block' if self.top_text else 'none'
		if 'bottom_text' in kwargs:
			self.bottom_text = kwargs['bottom_text']
			self.bottom_label.update(self.bottom_text)
		self.bottom_label.styles.display = 'block' if self.bottom_text else 'none'
		if 'text' in kwargs:
			self.clear()
			self.append(kwargs['text'])
		if 'min_height' in kwargs:
			self.min_height = int(kwargs['min_height'])
		if 'max_height' in kwargs:
			self.max_height = int(kwargs['max_height'])
		self.log_widget.styles.min_height = self.min_height
		self.log_widget.styles.max_height = self.max_height if self.max_height > 0 else None

	def clear(self, unused=None):
		self.log_widget.clear()

	def append(self, text):
		if text and text[-1] == '\n':
			text = text[:-1]
		if '\x1b' in text:
			text = Text.from_ansi(text)
		self.log_widget.write(text)

	DEFAULT_CSS = """
	$step_default: $primary;
	$step_success: ansi_bright_green;
	$step_warning: orange;
	$step_error: tomato;
	$step_debug: $accent;

	Step {
		/* If we do not specify "auto" here, each step will take 100% of the viewport: */
		height: auto;
		background: $step_default;
		color: auto;
		& RichLog {
			height: auto;
			scrollbar-corner-color: $step_default;
		}
		&.success {
			background: $step_success;
			& RichLog { scrollbar-corner-color: $step_success; }
		}
		&.warning {
			background: $step_warning;
			& RichLog { scrollbar-corner-color: $step_warning; }
		}
		&.error {
			background: $step_error;
			& RichLog { scrollbar-corner-color: $step_error; }
		}
		&.debug {
			background: $step_debug;
			& RichLog { scrollbar-corner-color: $step_debug; }
		}
		/* Compact design: no padding, no margins, no borders: */
		& Collapsible {
			padding: 0;
			margin: 0;
			border: none;
		}
		/* Collapsible contents: */
		& Contents {
			/* Leave some space on each side of the contents: */
			padding-left: 2 !important;
			padding-right: 1 !important;
		}
	}
	"""

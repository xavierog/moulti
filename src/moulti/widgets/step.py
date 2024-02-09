from textual.app import ComposeResult
from textual.widgets import Static, Collapsible
from rich.text import Text
from .moultilog import MoultiLog

ANSI_ESCAPE_SEQUENCE = '\x1b'

class Step(Static):
	"""
	This widget represents a step in a script, program or process.
	Visually speaking, it is essentially a collapsible text area surrounded
	with optional text lines.
	"""
	def __init__(self, id: str, **kwargs: str|int|bool): # pylint: disable=redefined-builtin
		self.collapsible = Collapsible(title=id)
		self.top_label = Static('', classes='top_text')
		self.log_widget = MoultiLog(highlight=False)
		self.bottom_label = Static('', classes='bottom_text')

		self.top_text = ''
		self.min_height = 1
		self.max_height = 25
		self.bottom_text = ''

		self.init_kwargs = kwargs
		# This attribute is meant to prevent deletion of a step while content
		# is being appended to it:
		self.prevent_deletion = 0

		step_classes = str(kwargs.get('classes', ''))
		super().__init__(id='step_' + id, classes=step_classes)

		self.color = ''

	def compose(self) -> ComposeResult:
		with self.collapsible:
			yield self.top_label
			yield self.log_widget
			yield self.bottom_label

	def on_mount(self) -> None:
		self.update_properties(self.init_kwargs)

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		if 'classes' in kwargs:
			self.set_classes(str(kwargs['classes']))
		if 'title' in kwargs:
			self.collapsible.title = str(kwargs['title']) if kwargs['title'] else str(self.id)[5:]
		if 'collapsed' in kwargs:
			self.collapsible.collapsed = bool(kwargs['collapsed'])
		if 'top_text' in kwargs:
			self.top_text = str(kwargs['top_text'])
			self.top_label.update(self.top_text)
		self.top_label.styles.display = 'block' if self.top_text else 'none'
		if 'bottom_text' in kwargs:
			self.bottom_text = str(kwargs['bottom_text'])
			self.bottom_label.update(self.bottom_text)
		self.bottom_label.styles.display = 'block' if self.bottom_text else 'none'
		if 'text' in kwargs:
			self.clear()
			self.append(str(kwargs['text']))
		if 'min_height' in kwargs:
			self.min_height = int(kwargs['min_height'])
		if 'max_height' in kwargs:
			self.max_height = int(kwargs['max_height'])
		self.log_widget.styles.min_height = self.min_height
		self.log_widget.styles.max_height = self.max_height if self.max_height > 0 else None

	def clear(self) -> None:
		self.log_widget.clear()
		self.color = ''

	def append(self, text: str) -> None:
		# RichLog does not handle partial lines and thus always adds a trailing \n; therefore, we must strip one (and
		# only one) trailing \n, if present:
		if text and text[-1] == '\n':
			text = text[:-1]
		# If necessary, prepend the ANSI escape code for the color inherited from the last line:
		if self.color:
			text = self.color + text
		# Deal with colored text; the text_to_write variable is made necessary by mypy.
		text_to_write: str | Text = text
		if ANSI_ESCAPE_SEQUENCE in text:
			text_to_write = Text.from_ansi(text)
			self.color = Step.next_line_color(text, text_to_write)
		self.log_widget.write(text_to_write)

	@classmethod
	def next_line_color(cls, string: str, text: Text) -> str:
		return '' if string.endswith('\x1b[0m') else Step.last_character_color(text)

	@classmethod
	def last_character_color(cls, text: Text) -> str:
		# If the last span (if any) covers the last character...
		if text.spans and text.spans[-1].end == len(text):
			# ... return the ANSI escape code for its color:
			style = text.spans[-1].style
			assert not isinstance(style, str) # prevent calling render() on str
			return style.render('_').split('_')[0]
		return ''

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
		& MoultiLog {
			scrollbar-corner-color: $step_default;
		}
		&.success {
			background: $step_success;
			& MoultiLog { scrollbar-corner-color: $step_success; }
		}
		&.warning {
			background: $step_warning;
			& MoultiLog { scrollbar-corner-color: $step_warning; }
		}
		&.error {
			background: $step_error;
			& MoultiLog { scrollbar-corner-color: $step_error; }
		}
		&.debug {
			background: $step_debug;
			& MoultiLog { scrollbar-corner-color: $step_debug; }
		}
		/* Compact design: no padding, no margins, no borders: */
		& Collapsible {
			padding: 0;
			margin: 0;
			border: none;
		}
		& CollapsibleTitle {
			padding: 0;
			width: 100%;
		}
		& CollapsibleTitle:hover {
			background: $foreground 80%;
		}
		& CollapsibleTitle:focus {
			background: initial;
		}
		/* Collapsible contents: */
		& Contents {
			/* Leave some space on each side of the contents: */
			padding-left: 2 !important;
			padding-right: 1 !important;
		}
	}
	Step:focus, Step:focus-within {
		& CollapsibleTitle {
			text-style: bold;
		}
	}
	"""

import errno
import os
import selectors
from queue import Queue, Empty
from time import monotonic_ns
from typing import Any, Callable, Iterable, Sequence
from textual import work
from textual.app import ComposeResult
from textual.strip import Strip
from textual.worker import get_current_worker
from rich.ansi import re_ansi
from rich.text import Text
from rich.cells import get_character_cell_size
from moulti.helpers import ANSI_ESCAPE_SEQUENCE_BYTES, ANSI_RESET_SEQUENCES_BYTES, TAB_SPACES_BYTES, clean_selector
from moulti.search import TextSearch
from . import MOULTI_PASS_DEFAULT_READ_SIZE
from ..collapsiblestep.tui import CollapsibleStep, SEARCH_SUBWIDGETS
from ..moultilog import MoultiLog

class ThrottledAppender:
	"""
	This class uses Textual's call_from_thread() to schedule calls to "step.append_lines()" inside Textual's asyncio
	event loop in a thread-safe manner. These calls are throttled so as not to flood the event loop.
	"""
	def __init__(self, step: 'Step', delay_ms: int):
		self.step = step
		self.call_from_thread = step.app.call_from_thread
		self.delay_ns = delay_ms * 1_000_000
		self.lines: list[str|Text] = []
		self.max_cell_len = -1
		self.last_append = 0

	def new_data(self, lines: Iterable[str|Text], max_cell_len: int, force: bool = False) -> None:
		self.lines.extend(lines)
		if max_cell_len > self.max_cell_len: # pylint: disable=consider-using-max-builtin
			self.max_cell_len = max_cell_len
		self.append(force)

	def append(self, force: bool = False) ->  None:
		if self.lines:
			now = monotonic_ns()
			if force or (now - self.last_append >= self.delay_ns):
				self.call_from_thread(self.step.append_lines, self.lines, self.max_cell_len)
				self.lines = []
				self.max_cell_len = -1
				self.last_append = now

class Step(CollapsibleStep):
	"""
	This widget represents a step in a script, program or process.
	Visually speaking, it is essentially a collapsible text area surrounded
	with optional text lines.
	"""

	BINDINGS = [
		("c", "to_clipboard(False)", "Copy"),
		("w", "to_clipboard(True)", "With colors"),
	]

	def __init__(self, id: str, **kwargs: str|int|bool): # pylint: disable=redefined-builtin
		self.log_widget = MoultiLog()

		self.min_height = 1
		self.max_height = 25

		super().__init__(id=id, **kwargs)

		self.color = ''

	def cli_action_append(self, kwargs: dict[str, Any], helpers: dict[str, Any]) -> tuple:
		if 'text' not in kwargs:
			helpers['reply'](done=False, error='missing text for append operation')
			return ()
		return self.append, '\n'.join(kwargs['text'])

	def cli_action_clear(self, _kwargs: dict[str, str|int|bool], _helpers: dict[str, Any]) -> tuple:
		return self.clear, # pylint: disable=trailing-comma-tuple

	def subcompose(self) -> ComposeResult:
		yield self.log_widget

	def subsearch(self, search: TextSearch) -> bool:
		if found := self.log_widget.search(search):
			# We found a match inside the log widget:
			if self.collapsible.collapsed:
				self.ensure_expanded()
			self.show_search_highlight()
		return found

	def search_maximized(self, search: TextSearch) -> bool:
		if self.screen.maximized != self.log_widget:
			return False
		if found := self.log_widget.search(search):
			# A match was found inside the maximized widget:
			# 1 - ensure no other part is highlighted:
			if self.search_cursor != SEARCH_SUBWIDGETS:
				self.search(TextSearch.make_reset())
			# 2 - update the search cursor so as to resume search from it:
			self.search_cursor = SEARCH_SUBWIDGETS
			self.log_widget.scroll_to_search_highlight()
		return found

	def ensure_expanded(self, expanded: bool = True) -> None:
		self.collapsible.collapsed = not expanded
		# Collapsible rely on CSS: this step is not actually expanded until CSS is refreshed:
		self.app.refresh_css(animate=False)

	def show_search_highlight(self) -> None:
		region_spacing = self.log_widget.scroll_to_search_highlight()
		# To make scrolling more convenient, give the focus to the log widget if and only if it can be scrolled:
		if self.log_widget.max_scroll_x or self.log_widget.max_scroll_y:
			self.log_widget.focus(False)
		else: # otherwise, focus the step, thus enabling scrolling the StepContainer:
			self.focus(False)
		if region_spacing is not None:
			region, _ = region_spacing # relative to the MoultiLog widget
			log_widget_offset = self.log_widget.region.offset - self.region.offset
			region = region.translate(log_widget_offset) # relative to this Step widget
			self.post_message(self.ScrollRequest(self, region, center=True, animate=False))

	def update_properties(self, kwargs: dict[str, str|int|bool]) -> None:
		super().update_properties(kwargs)
		if 'auto_scroll' in kwargs:
			self.log_widget.auto_scroll = self.log_widget.default_auto_scroll = bool(kwargs['auto_scroll'])
		if 'text' in kwargs:
			self.clear()
			self.append(str(kwargs['text']))
		if 'min_height' in kwargs:
			self.min_height = int(kwargs['min_height'])
		if 'max_height' in kwargs:
			self.max_height = int(kwargs['max_height'])
		self.log_widget.styles.min_height = self.min_height
		self.log_widget.set_max_height(self.max_height)

	def export_properties(self) -> dict[str, Any]:
		prop = super().export_properties()
		prop['auto_scroll'] = self.log_widget.default_auto_scroll
		prop['min_height'] = self.min_height
		prop['max_height'] = self.max_height
		return prop

	def save(self, opener: Callable[[str, int], int], filename: str, extra_properties: dict[str, Any]) -> None:
		super().save(opener, filename, extra_properties)
		filename = filename + '.contents.log'
		with open(filename, 'w', encoding='utf-8', errors='surrogateescape', opener=opener) as contents_filedesc:
			self.log_widget.to_file(contents_filedesc)

	@CollapsibleStep.copy_to_clipboard
	def action_to_clipboard(self, keep_styles: bool = True) -> tuple[bool, str, str]:
		lines = list(self.log_widget.to_lines(keep_styles))
		lines_count = len(lines)
		lines.append('') # add an extra \n
		data = '\n'.join(lines)
		return True, data, f'copied {lines_count} lines, {len(data)} characters to clipboard'

	def clear(self) -> None:
		self.log_widget.clear()
		self.color = ''

	def append(self, text: str) -> None:
		if not text:
			return
		if text[-1] != '\n':
			text += '\n'
		# This looks silly, but our main ingestion function takes bytes, not strings:
		text_bytes = text.encode('utf-8')
		lines, max_cell_len, _, _ = Step.bytes_to_lines(text_bytes, b'', 'utf-8')
		self.append_lines(lines, max_cell_len)

	def append_lines(self, lines: Iterable[str|Text|Strip], max_cell_len: int) -> None:
		self.log_widget.write_lines(lines, max_cell_len)
		self.activity()

	@classmethod
	def last_character_color(cls, text: Text) -> str:
		# If the last span (if any) covers the last character...
		if text.spans and text.spans[-1].end == len(text):
			# ... return the ANSI escape code for its color:
			style = text.spans[-1].style
			assert not isinstance(style, str) # prevent calling render() on str
			return style.render('_').split('_')[0]
		return ''

	def cli_action_pass(self, kwargs: dict[str, str|int|bool], helpers: dict[str, Any]) -> tuple:
		if not helpers['file_descriptors']:
			helpers['reply'](done=False, error='missing file descriptor for pass operation')
			return ()
		# Set up a queue between two workers:
		# - one that reads data from the file descriptor and replies to the client;
		# - one that appends lines to the step.
		queue: Queue = Queue()
		self.append_from_queue(queue, helpers)
		self.append_from_file_descriptor_to_queue(queue, kwargs, helpers)
		return ()

	@work(thread=True, group='step-ingestion', name='fd-to-queue')
	async def append_from_file_descriptor_to_queue(
		self,
		queue: Queue,
		kwargs: dict[str, Any],
		helpers: dict[str, Any],
	) -> None:
		current_worker = get_current_worker()
		error = None
		original_file_descriptor = None
		output_selector = None
		try:
			original_file_descriptor = helpers['file_descriptors'][0]
			if isinstance(original_file_descriptor, int):
				file_descriptor = original_file_descriptor
			else:
				file_descriptor = original_file_descriptor.fileno()
			# Although this thread is dedicated to reading from a single file descriptor, it should:
			# - not block indefinitely on a read()
			# - check is_cancelled at regular intervals
			# This ensures Moulti exits correctly.
			# To this end, use non-blocking mode along with a select()-like interface:
			os.set_blocking(file_descriptor, False)
			output_selector = selectors.DefaultSelector()
			try:
				output_selector.register(file_descriptor, selectors.EVENT_READ)
				def can_read() -> bool:
					return bool(output_selector.select(0.5))
			except Exception:
				# register() may fail: for instance, on Linux, epoll() does not support regular files and returns EPERM.
				def can_read() -> bool:
					return True
			# Read binary data from the given file descriptor using a FileIO (raw binary stream whose methods only make
			# one system call):
			with os.fdopen(file_descriptor, mode='rb', buffering=0) as binary_stream:
				read_size = int(kwargs.get('read_size', MOULTI_PASS_DEFAULT_READ_SIZE))
				if read_size <= 0:
					read_size = MOULTI_PASS_DEFAULT_READ_SIZE
				end_of_file = False
				# Outer loop: check for worker cancellation and rely on select() to detect activity:
				while not current_worker.is_cancelled and not end_of_file:
					if can_read():
						# Inner loop: read data until it would block, keep checking for worker cancellation:
						# "If the object is in non-blocking mode and no bytes are available, None is returned."
						while (data := binary_stream.read(read_size)) is not None:
							# "If 0 bytes are returned, and size was not 0, this indicates end of file."
							if not data:
								end_of_file = True
								break
							queue.put_nowait(data)
							if current_worker.is_cancelled:
								break
				queue.put_nowait(None)
		except Exception as exc:
			error = str(exc)
			helpers['debug'](f'pass: {error}')
		finally:
			try:
				clean_selector(output_selector, close_fds=False, close=True)
				if original_file_descriptor is not None and not isinstance(original_file_descriptor, int):
					# The file descriptor passed to this method is an object, and its fileno() was extracted to
					# instantiate a second fileobject (binary_stream), leading to TWO objects referencing the same
					# underlying file descriptor, which was typically closed upon exiting the with statement above.
					# Ideally, we should prevent the first fileobject from calling close() (or any equivalent private
					# method) because that double-close could strike another file descriptor opened in the meantime,
					# leading to one hell of a troubleshooting session.
					# This is particularly relevant whenever the Python process keeps running after the Moulti App has
					# finished running and garbage collection is not immediate.
					# In practice, we can simply call close() right now and handle the errno=EBADF that typically
					# ensues.
					try:
						original_file_descriptor.close()
					except OSError as ose:
						if ose.errno != errno.EBADF: # Bad file descriptor
							raise
			except Exception as exc:
				error = str(exc)
				helpers['debug'](f'pass: cleanup: unexpected error: {error}')
		helpers['reply'](done=error is None, error=error)

	@classmethod
	def bytes_to_lines(
		cls,
		data: bytes,
		color: bytes = b'',
		encoding: str = 'utf-8'
	) -> tuple[Sequence[str|Text], int, bytes, bytes]:
		lines: list[str|Text] = []
		max_cell_len: int = -1
		leftover: bytes = b''
		if data:
			# Deal only with lines ending with a line feed (lf, \n) and return leftover bytes:
			if data[-1] != b'\n':
				last_lf_index = data.rfind(b'\n')
				leftover = data[last_lf_index+1:]
				data = data[:last_lf_index]
			if data:
				# At this stage, all lines end with \n.
				for line_bytes in data.split(b'\n'):
					# Expand tabs into spaces: both Rich and Textual provide frighteningly
					# complex methods to do it the right way. But Text.expand_tabs()
					# dramatically and negatively affects performance.
					line_bytes = line_bytes.replace(b'\t', TAB_SPACES_BYTES)

					if ANSI_ESCAPE_SEQUENCE_BYTES in line_bytes:
						if Step.ends_with_ansi_reset(line_bytes):
							# Simple case: the last ANSI sequence in the line resets all styles:
							line_bytes = color + line_bytes
							line_str = line_bytes.decode(encoding, errors='surrogateescape')
							line_plain = re_ansi.sub('', line_str)
							lines.append(line_str)
							color = b''
						else:
							# The trailing underscore will determine the next line's color:
							line_bytes = color + line_bytes + b'_'
							line_str = line_bytes.decode(encoding, errors='surrogateescape')
							# ANSI sequences can be tricky: better call Text.from_ansi() even if it is expensive:
							line_text = Text.from_ansi(line_str)
							line_plain = line_text.plain
							color = cls.last_character_color(line_text).encode('ascii') # analyse the trailing underscore
							line_text.right_crop(1) # remove the trailing underscore
							lines.append(line_text)
					else:
						line_str = line_bytes.decode(encoding, errors='surrogateescape')
						line_plain = line_str
						if color:
							line_str = color.decode('ascii') + line_str
						lines.append(line_str)

					max_cell_len = Step.update_max_cell_len(max_cell_len, line_plain)
		return lines, max_cell_len, leftover, color

	@classmethod
	def ends_with_ansi_reset(cls, line: bytes) -> bool:
		index = line.rfind(ANSI_ESCAPE_SEQUENCE_BYTES)
		rest_of_line = line[index:]
		for reset_seq in ANSI_RESET_SEQUENCES_BYTES:
			if rest_of_line.startswith(reset_seq):
				return True
		return False


	@classmethod
	def update_max_cell_len(cls, max_cell_len: int, line_plain: str) -> int:
		line_plain_char_len = len(line_plain)
		# Worst-case: each character takes two cells:
		if (2 * line_plain_char_len) > max_cell_len:
			current_cell_len = 0
			for position, char in enumerate(line_plain):
				# Every 10 characters, evaluate the worst-case scenario again:
				if (position % 10) == 0 and position:
					if (current_cell_len + 2 * (line_plain_char_len - position)) <= max_cell_len:
						break
				current_cell_len += get_character_cell_size(char)
			else:
				if current_cell_len > max_cell_len: # pylint: disable=consider-using-max-builtin
					max_cell_len = current_cell_len
		return max_cell_len

	@work(thread=True, group='step-ingestion', name='queue-to-step')
	async def append_from_queue(self, queue: Queue, helpers: dict[str, Any]) -> None:
		current_worker = get_current_worker()
		self.prevent_deletion += 1
		color = b''
		try:
			throttling_ms = 25
			throttling_s = throttling_ms / 1000
			appender = ThrottledAppender(self, throttling_ms)
			buffer = []
			while True:
				if current_worker.is_cancelled:
					break
				try:
					data = queue.get(block=True, timeout=throttling_s)
					if data is not None:
						buffer.append(data)
						all_data = b''.join(buffer)
						lines, max_cell_len, leftover, color = Step.bytes_to_lines(all_data, color)
						if lines:
							appender.new_data(lines, max_cell_len)
						buffer.clear()
						if leftover:
							buffer.append(leftover)
					else: # Reached EOF: flush buffer and exit:
						if buffer:
							buffer.append(b'\n')
							all_data = b''.join(buffer)
							lines, max_cell_len, _, _ = Step.bytes_to_lines(all_data, color)
							appender.new_data(lines, max_cell_len)
						appender.append(True)
						break
				except Empty:
					# No data: there may be data left in the appender's buffer:
					appender.append(True)
		except Exception as exc:
			helpers['debug'](f'append_from_queue: {exc}')
		finally:
			self.prevent_deletion -= 1

	DEFAULT_CSS = CollapsibleStep.DEFAULT_CSS + """
	Step {
		& MoultiLog {
			scrollbar-corner-color: $step_default;
		}
		&.success {
			& MoultiLog { scrollbar-corner-color: $step_success; }
		}
		&.warning {
			& MoultiLog { scrollbar-corner-color: $step_warning; }
		}
		&.error {
			& MoultiLog { scrollbar-corner-color: $step_error; }
		}
		&.inactive {
			& MoultiLog { scrollbar-corner-color: $step_inactive; }
		}
	}
	"""
MoultiWidgetClass = Step

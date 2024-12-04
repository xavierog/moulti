import re
from collections import deque
from dataclasses import dataclass
from typing import Any
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.validation import Function
from textual.widgets import Input, Label, Static
from moulti.search import TextSearch

def regex_is_valid(regex: str) -> bool:
	try:
		re.compile(regex)
		return True
	except re.error:
		return False

REGEX_VALIDATOR = Function(regex_is_valid)
SEARCH_HISTORY_SIZE = 500 # The search history is not persisted so this should be plenty.

class SearchInput(Input):
	class CancelSearch(Message):
		pass

	@dataclass
	class HistoryMove(Message):
		move: int

	BINDINGS = [
		Binding('escape', 'exit', 'Cancel', priority=True),
		Binding('up', 'history(-1)', 'Previous', priority=True),
		Binding('down', 'history(+1)', 'Next', priority=True),
	]

	def action_exit(self) -> None:
		self.post_message(self.CancelSearch())

	def action_delete_left(self) -> None:
		"""
		Hitting backspace when the input is empty cancels the search.
		"""
		if self.value:
			super().action_delete_left()
		else:
			self.action_exit()

	async def action_submit(self) -> None:
		"""
		Hitting enter when the input is empty cancels the search.
		"""
		if self.value:
			await super().action_submit()
		else:
			self.action_exit()

	def action_history(self, move: int) -> None:
		self.post_message(self.HistoryMove(move))

	DEFAULT_CSS = """
	SearchInput {
		background: $boost;
		color: $text;
		padding: 0;
		border: none;
		width: 1fr;
		height: 1;
	}
	SearchInput:focus {
		border: none;
	}
	SearchInput.-invalid {
		border: none;
		color: $error;
	}
	SearchInput.-invalid:focus {
		border: none;
		color: $error;
	}
	"""


class SearchInputWidget(Static):
	class NewSearch(Message):
		def __init__(self, search: TextSearch):
			super().__init__()
			self.search = search

	LABELS = {
		(True, True): 'REGEX',
		(True, False): 'Regex',
		(False, True): 'PLAIN',
		(False, False): 'Plain',
	}
	TOOLTIPS = {
		(True, True): 'Case-insensitive Python regular expression pattern',
		(True, False): 'Case-sensitive Python regular expression pattern',
		(False, True): 'Case-insensitive plain pattern',
		(False, False): 'Case-sensitive plain pattern',
	}

	regex = reactive(True, repaint=True, bindings=True)
	case_insensitive = reactive(False, repaint=True, bindings=True)
	next_result = reactive(True, repaint=True)

	BINDINGS = [
		Binding('ctrl+r', 'toggle_regex(True)', 'Regex pattern'),
		Binding('ctrl+r', 'toggle_regex(False)', 'Plain pattern'),
		Binding('ctrl+t', 'toggle_case_insensitive(True)', 'Case-insensitive'),
		Binding('ctrl+t', 'toggle_case_insensitive(False)', 'Case-sensitive'),
	]

	def action_toggle_regex(self, new: bool) -> None:
		self.regex = new

	def action_toggle_case_insensitive(self, new: bool) -> None:
		self.case_insensitive = new

	def check_action(self, action: str, parameters: tuple[object, ...]) -> bool:
		enable = parameters[0] is True
		if action.endswith('_regex'):
			return enable ^ bool(self.regex)
		if action.endswith('_case_insensitive'):
			return enable ^ bool(self.case_insensitive)
		return True

	def update_regex_label(self) -> None:
		configuration = (self.regex, self.case_insensitive)
		self.regex_label.update(self.LABELS[configuration])
		self.regex_label.tooltip = self.TOOLTIPS[configuration]

	def watch_regex(self, _old: bool, new: bool) -> None:
		self.update_regex_label()
		self.regex_label.set_class(new, 'regex')
		self.input.validators = [REGEX_VALIDATOR] if new else []
		self.input.validate(self.input.value)

	def watch_case_insensitive(self, _old: bool, _new: bool) -> None:
		self.update_regex_label()

	def watch_next_result(self, _old: bool, new: bool) -> None:
		self.next_label.set_class(new, 'next').update('/' if new else '?')

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.input = SearchInput(id='search_input')
		self.input.valid_empty = True
		self.input.validate_on = {'changed', 'submitted'}
		self.next_label = Label('?', id='search_next_label')
		self.regex_label = Label('?????', id='search_regex_label')
		self.next_label.tooltip = '/: search forward\n?: search backward'
		self.history: deque[TextSearch] = deque(maxlen=SEARCH_HISTORY_SIZE)
		self.editable_history: deque[TextSearch] = deque(maxlen=SEARCH_HISTORY_SIZE + 1)
		self.history_index = -1

	def compose(self) -> ComposeResult:
		with Horizontal():
			yield self.regex_label
			yield self.next_label
			yield self.input

	def to_search(self) -> TextSearch:
		return TextSearch(self.input.value, self.regex, self.case_insensitive, self.next_result)

	def setup_history(self) -> None:
		# Copy the history into the editable history:
		self.editable_history.clear()
		self.editable_history.extend(entry.copy() for entry in self.history)
		# Append a new empty entry:
		self.editable_history.append(TextSearch('', self.regex, self.case_insensitive, self.next_result))
		# This new entry is at index -1:
		self.history_index = -1

	def action_pop(self, next_result: bool = True) -> None:
		self.next_result = next_result
		self.setup_history()
		self.styles.display = 'block'
		self.input.focus()

	def set_search(self, search: TextSearch) -> None:
		self.regex = search.regex
		self.case_insensitive = search.case_insensitive
		# NOT setting self.next_result.
		self.input.value = search.pattern
		self.input.validate(self.input.value)

	def set_search_by_index(self, index: int = -1) -> None:
		if index >= 0:
			return
		try:
			self.set_search(self.editable_history[index])
			self.history_index = index
		except IndexError:
			pass

	def action_exit(self) -> None:
		self.input.clear()
		self.styles.display = 'none'

	async def on_search_input_cancel_search(self, _event: SearchInput.CancelSearch) -> None:
		self.action_exit()

	def on_search_input_history_move(self, event: SearchInput.HistoryMove) -> None:
		self.editable_history[self.history_index] = self.to_search()
		self.set_search_by_index(self.history_index + event.move)

	async def on_input_submitted(self, event: Input.Submitted) -> None:
		if not event.value:
			self.action_exit()
		else:
			if event.validation_result is None or event.validation_result.is_valid:
				search = self.to_search()
				self.action_exit()
				self.post_message(self.NewSearch(search))
				self.history.append(search)

	DEFAULT_CSS = """
		#search_regex_label {
			background: $secondary-darken-2;
			color: $text-muted;
		}
		#search_regex_label.regex {
			color: $accent;
		}
		SearchInputWidget {
			display: none;
			height: 1;
		}
		SearchInputWidget:focus, SearchInputWidget:focus-within {
			display: block;
			height: 1;
		}
	"""

import re
from collections import deque
from rich.text import Text

# Default value for endpos in re.Pattern.search():
# re.Pattern.search(self, string, pos=0, endpos=9223372036854775807)
END = 2**63-1

MatchSpan = tuple[int, int]|None

class TextSearch:
	def __init__(self, pattern: str, regex: bool, case_insensitive: bool, next_result: bool, reset: bool = False) -> None:
		self.pattern = pattern
		self.regex = regex
		self.case_insensitive = case_insensitive
		self.next_result = next_result
		self.is_reset = reset
		if self.regex:
			re_flags = re.IGNORECASE if self.case_insensitive else 0
			self._pattern = re.compile(self.pattern, re_flags)
		elif self.case_insensitive:
			self._casefold_pattern = self.pattern.casefold()

	def __str__(self) -> str:
		if self.is_reset:
			return 'reset text search'
		pattern_type = 'regex' if self.regex else 'basic'
		cs_type = 'case-insensitive' if self.case_insensitive else 'case-sensitive'
		direction = 'Forward' if self.next_result else 'Backward'
		return f'{direction} text search: {pattern_type} pattern "{self.pattern}", {cs_type}'

	def __repr__(self) -> str:
		return self.__str__()

	def copy(self) -> 'TextSearch':
		return TextSearch(self.pattern, self.regex, self.case_insensitive, self.next_result)

	@classmethod
	def make_reset(cls) -> 'TextSearch':
		return cls('', False, False, False, True)

	def reset(self) -> bool:
		return self.is_reset

	def search(self, plain_text: str, highlight: MatchSpan) -> MatchSpan:
		if not plain_text or self.is_reset:
			return None
		if self.regex:
			return self.regex_search(plain_text, highlight)
		return self.simple_search(plain_text, highlight)

	def regex_search(self, plain_text: str, highlight: MatchSpan) -> MatchSpan:
		start, end = (None, None) if highlight is None else highlight
		rem = None
		if self.next_result:
			# First match after the end of the highlighted part:
			rem = self._pattern.search(plain_text, end or 0)
		else:
			# Last match before the start of the highlighted part:
			matches = self._pattern.finditer(plain_text, 0, END if start is None else start)
			if last_match := deque(matches, maxlen=1):
				rem = last_match.pop()
		if rem:
			return rem.span()
		return None

	def simple_search(self, plain_text: str, highlight: MatchSpan) -> MatchSpan:
		pattern = self.pattern
		start, end = (None, None) if highlight is None else highlight
		if self.case_insensitive:
			plain_text = plain_text.casefold()
			pattern = self._casefold_pattern
		if self.next_result:
			start = plain_text.find(pattern, end)
		else:
			start = plain_text.rfind(pattern, 0, start)
		if start != -1:
			return (start, start + len(pattern))
		return None

	def highlight(self, text: Text, start: int, end: int) -> Text:
		text.stylize('reverse', start, end)
		return text

from typing import Any, Generator
from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from moulti.helpers import ANSI_ESCAPE_SEQUENCE_STR

class ToLinesMixin:

	def line_to_strip(self, y: int, store: bool = False) -> Strip:
		line = self.lines[y] # type: ignore
		changed = False
		if isinstance(line, str):
			line = Text.from_ansi(line) if ANSI_ESCAPE_SEQUENCE_STR in line else Text(line)
		if isinstance(line, Text):
			line = Strip(line.render(self.app.console)) # type: ignore
			changed = True
		# At this stage, line is a Strip.
		if changed and store:
			self.lines[y] = line # type: ignore
		return line

	def to_lines(self, keep_styles: bool = True) -> Generator:
		"""
		Our own variant of Strip.render() that does NOT forget to output unstyled segments.
		"""
		color_system = Console()._color_system # pylint: disable=protected-access
		style_render = Style.render
		if keep_styles:
			for index, _ in enumerate(self.lines): # type: ignore
				strip = self.line_to_strip(index)
				yield ''.join([
					text
					if style is None
					else style_render(style, text, color_system=color_system)
					for text, style, _ in strip._segments # pylint: disable=protected-access
				])
		else:
			for index, _ in enumerate(self.lines): # type: ignore
				yield self.line_to_strip(index).text

	def to_file(self, file_descriptor: Any) -> None:
		for line in self.to_lines():
			file_descriptor.write(line)
			file_descriptor.write('\n')

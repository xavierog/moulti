from typing import Any, Generator
from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from moulti.helpers import ANSI_ESCAPE_SEQUENCE_STR

class ToLinesMixin:
	def str_to_text(self, string: str) -> Text:
		return Text.from_ansi(string) if ANSI_ESCAPE_SEQUENCE_STR in string else Text(string)

	def text_to_strip(self, text: Text) -> Strip:
		return Strip(text.render(self.app.console)) # type: ignore

	def strip_to_text(self, strip: Strip) -> Text:
		parts: list[str|tuple[str, Style]] = [
			text if style is None else (text, style)
			for text, style, _ in strip
		]
		return Text.assemble(*parts)

	def line_to_plain_text(self, y: int, store: bool = False) -> tuple[str, Text|None]:
		"""
		Return the requested line as plain text.
		If a Text object was instantiated to obtain the returned plain text, this Text object is returned too.
		"""
		line = self.lines[y] # type: ignore
		if isinstance(line, str):
			if ANSI_ESCAPE_SEQUENCE_STR in line:
				line = Text.from_ansi(line)
				if store:
					self.lines[y] = line # type: ignore
				return (line.plain, line)
			return (line, None)
		if isinstance(line, Text):
			return (line.plain, line)
		# At this stage, line is a Strip.
		return (line.text, None)

	def line_to_text(self, y: int, store: bool = False) -> Text:
		line = self.lines[y] # type: ignore
		if isinstance(line, Text):
			return line
		if isinstance(line, str):
			line = self.str_to_text(line)
			if store:
				self.lines[y] = line # type: ignore
			return line
		# At this stage, line is a Strip.
		return self.strip_to_text(line)

	def line_to_strip(self, y: int, store: bool = False) -> Strip:
		line = self.lines[y] # type: ignore
		changed = False
		if isinstance(line, str):
			line = self.str_to_text(line)
		if isinstance(line, Text):
			line = self.text_to_strip(line)
			changed = True
		# At this stage, line is a Strip.
		if changed and store:
			self.lines[y] = line # type: ignore
		return line

	def to_lines(self, keep_styles: bool = True) -> Generator:
		"""
		Our own variant of Strip.render() that does NOT forget to output unstyled segments.
		"""
		console = self.app.console # type: ignore
		color_system = Console()._color_system # pylint: disable=protected-access
		style_render = Style.render
		if keep_styles:
			highlighter = None
			if hasattr(self, 'highlight') and self.highlight and hasattr(self, 'highlighter'):
				highlighter = self.highlighter
			for line in self.lines: # type: ignore
				if isinstance(line, str):
					if highlighter:
						line = highlighter(Text(line))
					else:
						yield line
						continue
				if isinstance(line, Text):
					segments = line.render(console)
				else:
					# At this stage, line is a Strip.
					segments = line
				yield ''.join([
					text
					if style is None
					else style_render(style, text, color_system=color_system)
					for text, style, _ in segments
				])
		else:
			for index in range(len(self.lines)): # type: ignore
				yield self.line_to_plain_text(index)[0]

	def to_file(self, file_descriptor: Any) -> None:
		for line in self.to_lines():
			file_descriptor.write(line)
			file_descriptor.write('\n')

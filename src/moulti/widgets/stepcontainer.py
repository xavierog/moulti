from typing import Iterator, Sequence, cast
from textual.reactive import Reactive
from textual.widget import AwaitMount
from .vertscroll import VertScroll
from .abstractstep.tui import AbstractStep

class StepContainer(VertScroll):
	"""
	Vertical scrollable container for steps.
	"""
	DEFAULT_CSS = """
	/* Leave a thin space between steps and the container's vertical scrollbar: */
	StepContainer.vertical_scrollbar_visible > Widget {
		margin-right: 1;
	}
	StepContainer.bottom {
		align-vertical: bottom;
	}
	"""

	layout_direction_is_down = Reactive(True)

	def watch_layout_direction_is_down(self, _was_down: bool, is_down: bool) -> None:
		self.sort_children(key=None, reverse=not is_down)

	def ordered_steps(self) -> Iterator[AbstractStep]:
		steps = cast(Sequence[AbstractStep], self.children)
		if self.layout_direction_is_down:
			yield from steps
		else:
			yield from reversed(steps)

	def add_step(self, step: AbstractStep) -> AwaitMount:
		return self.mount(step, before=None if self.layout_direction_is_down else 0)

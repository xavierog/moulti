from typing import Any, Iterator, Sequence, cast
from textual import on
from textual.geometry import Region
from textual.reactive import Reactive
from textual.widget import AwaitMount
from .vertscroll import VertScroll
from .abstractstep.tui import AbstractStep

class StepContainer(VertScroll):
	"""
	Vertical scrollable container for steps.
	"""
	BINDINGS = [
		('l', 'toggle_scrolling', 'Lock scroll')
	]

	DEFAULT_CSS = """
	/* Leave a thin space between steps and the container's vertical scrollbar: */
	StepContainer.vertical_scrollbar_visible > Widget {
		margin-right: 1;
	}
	$scrollbar_green: #18b218;
	StepContainer.prevent_programmatic_scrolling {
		scrollbar-color: $scrollbar_green;
		scrollbar-color-active: $scrollbar_green;
		scrollbar-color-hover: $scrollbar_green;
	}
	StepContainer.bottom {
		align-vertical: bottom;
	}
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		super().__init__(*args, **kwargs)
		self.prevent_programmatic_scrolling = False

	def action_toggle_scrolling(self) -> None:
		# Actual toggle:
		self.prevent_programmatic_scrolling = not self.prevent_programmatic_scrolling
		# Visual toggle:
		self.set_class(self.prevent_programmatic_scrolling, 'prevent_programmatic_scrolling')
		# Workaround for the scrollbar to change color immediately:
		scrollbar = self.vertical_scrollbar
		value = scrollbar.mouse_over
		scrollbar.mouse_over = not value
		scrollbar.mouse_over = value

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

	def scroll_to_step(self, step: AbstractStep, where: bool|int = True) -> None:
		if self.prevent_programmatic_scrolling or where is False:
			return
		if where is True:
			self.scroll_to_widget(step, origin_visible=True)
			return
		step_region = step.virtual_region
		line = (step_region.bottom if where < 0 else step_region.y) + where
		target_region = Region(step_region.x, line, step_region.width, 1)
		self.scroll_to_region(target_region)

	@on(AbstractStep.StepActivity)
	def on_step_activity(self, activity: AbstractStep.StepActivity) -> None:
		# Consume the event:
		activity.prevent_default()
		activity.stop()
		# Extract step and its scroll policy:
		step = activity.step
		scroll_on_activity = step.scroll_on_activity
		# Delay the actual scrolling:
		if scroll_on_activity is not False:
			def do_scroll() -> None:
				self.scroll_to_step(step, scroll_on_activity)
			self.set_timer(0.05, do_scroll)

from typing import Any, Iterator, Sequence, cast
from textual import on
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.geometry import Region
from textual.reactive import Reactive
from textual.widget import AwaitMount
from .vertscroll import VertScroll
from .abstractstep.tui import AbstractStep
from .abstractquestion.tui import AbstractQuestion

class StepContainer(VertScroll):
	"""
	Vertical scrollable container for steps.
	"""
	BINDINGS = [
		Binding('l', 'toggle_scrolling(True)', 'Lock scroll'),
		Binding('l', 'toggle_scrolling(False)', 'Unlock scroll'),
		Binding("ctrl+t", "focus_question(True, False)", "Previous unanswered question", show=False),
		Binding("ctrl+y", "focus_question(False, False)", "Next unanswered question", show=False),
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

	def action_toggle_scrolling(self, prevent: bool) -> None:
		# Actual toggle:
		self.prevent_programmatic_scrolling = prevent
		# Visual toggle:
		self.refresh_bindings()
		self.set_class(self.prevent_programmatic_scrolling, 'prevent_programmatic_scrolling')

	def check_action(self, action: str, parameters: tuple[object, ...]) -> bool:
		if action == 'toggle_scrolling':
			return parameters[0] != self.prevent_programmatic_scrolling
		return True

	layout_direction_is_down = Reactive(True)

	def watch_layout_direction_is_down(self, _was_down: bool, is_down: bool) -> None:
		self.sort_children(key=None, reverse=not is_down)

	def ordered_steps(self) -> Iterator[AbstractStep]:
		steps = cast(Sequence[AbstractStep], self.children)
		if self.layout_direction_is_down:
			yield from steps
		else:
			yield from reversed(steps)

	def focus_step(self) -> AbstractStep|None:
		try:
			return self.query_one('AbstractStep:focus-within', AbstractStep)
		except NoMatches:
			return None

	def get_question(self, backward: bool = False, answered: bool|None = False) -> AbstractQuestion|None:
		steps = list(self.ordered_steps())
		if backward:
			steps = list(reversed(steps))
		if current := self.focus_step():
			try:
				index = steps.index(current)
				steps = steps[index+1:] + steps[:index]
			except ValueError:
				pass
		for step in steps:
			if isinstance(step, AbstractQuestion):
				if answered is None or answered == step.answered():
					return step
		return None

	def action_focus_question(self, backward: bool = False, answered: bool|None = False) -> None:
		question = self.get_question(backward=backward, answered=answered)
		if question is not None:
			question.focus_input_widget()

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

from typing import Any, Iterator, Sequence, cast
from textual import on
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.geometry import Region
from textual.reactive import Reactive
from textual.dom import DOMNode
from textual.widget import AwaitMount, AwaitRemove
from moulti.search import TextSearch
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
		self.search_cursor = -1
		"""
		Index of the widget that last returned a positive search result.
		"""

	def action_toggle_scrolling(self, prevent: bool) -> None:
		# Actual toggle:
		self.prevent_programmatic_scrolling = prevent
		# Visual toggle:
		self.refresh_bindings()
		self.set_class(self.prevent_programmatic_scrolling, 'prevent_programmatic_scrolling')

	def check_action(self, action: str, parameters: tuple[object, ...]) -> bool:
		if self.screen.maximized:
			return False
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

	def ordered_index(self, step: AbstractStep) -> int:
		try:
			if self.layout_direction_is_down:
				return self.children.index(step)
			return len(self.children) - 1 - self.children.index(step)
		except ValueError:
			return -1

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

	def remove_step(self, step: AbstractStep) -> AwaitRemove|None:
		deleted_index = self.ordered_index(step)
		if deleted_index != -1:
			removal = step.remove()
			if deleted_index <= self.search_cursor:
				self.search_cursor -= 1
			return removal
		return None

	def parent_step(self, widget: DOMNode|None) -> AbstractStep|None:
		while widget is not None and not isinstance(widget, AbstractStep):
			widget = widget.parent
		return widget

	def search_maximized(self, search: TextSearch) -> bool:
		# Is there a maximized widget?
		maximized_widget = self.screen.maximized
		if not maximized_widget:
			return False
		# Does the maximized widget belong to a step?
		step = self.parent_step(maximized_widget)
		if step is None:
			return False
		# Does that step belong to this container?
		if step.parent != self:
			return False
		# Can this step handle the matter?
		if hasattr(step, 'search_maximized') and step.search_maximized(search):
			# A match was found inside the maximized widget:
			# 1 - discard the previously highlighted match, if any:
			step_index = self.ordered_index(step)
			if self.search_cursor not in (-1, step_index):
				steps = list(self.ordered_steps())
				current_step = steps[self.search_cursor]
				if hasattr(current_step, 'search'):
					current_step.search(TextSearch.make_reset())
			# 2 - update the search cursor so as to resume search from the maximized widget's parent step:
			self.search_cursor = step_index
			return True
		return False

	def search(self, search: TextSearch) -> bool:
		if self.screen.maximized:
			return self.search_maximized(search)
		steps = list(enumerate(self.ordered_steps()))
		if self.search_cursor != -1:
			steps = steps[self.search_cursor:] if search.next_result else steps[:self.search_cursor+1]
		iter_steps = iter(steps) if search.next_result else reversed(steps)
		for index, widget in iter_steps:
			if not hasattr(widget, 'search'):
				continue
			if widget.search(search):
				self.search_cursor = index
				return True
		self.search_cursor = -1
		return False

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

	@on(AbstractStep.ScrollRequest)
	def on_scroll_request(self, request: AbstractStep.ScrollRequest) -> None:
		# Consume the event:
		request.prevent_default()
		request.stop()
		if isinstance(request.target, Region):
			# The provided region must be mapped to this container's coordinates:
			region = request.target # relative to the AbstractStep widget
			region = region.translate(request.step.virtual_region.offset) # relative to this StepContainer
			self.scroll_to_region(region, **request.scroll_kwargs)
			return
		target_widget = request.step if request.target is None else request.target
		self.scroll_to_widget(target_widget, **request.scroll_kwargs)

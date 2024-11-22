from .common import moulti_test, moulti_test_steps, wait_script, wait_script_start, wait_script_end
assert moulti_test

def test_programmatic_scrolling(moulti_test):
	"""
	Run most commands from the documentation's "Programmatically scrolling through steps" section.
	"""
	moulti_test_steps(moulti_test, 'prog-scrolling-through-steps.bash', 7)

def test_lock_scroll(moulti_test):
	# No scroll lock: do not wait, let it scroll:
	assert moulti_test(command=['manual-scrolling-through-steps.bash', '0'])
	# Scroll lock:
	async def scroll_lock(pilot):
		await pilot.press('l') # enable scroll lock
		await wait_script(pilot)
	assert moulti_test(command=['manual-scrolling-through-steps.bash'], run_before=scroll_lock)

def test_auto_scrolling(moulti_test):
	async def interrupt_auto_scroll(pilot):
		await wait_script_start(pilot)
		await pilot.pause(0.5)
		await pilot.press('tab', 'tab', 'home') # focus the first step, focus its log, hit the 'home' key
		await wait_script_end(pilot)
	assert moulti_test(command=['scrolling-inside-steps.bash'], run_before=interrupt_auto_scroll)

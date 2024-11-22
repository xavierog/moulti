from .common import moulti_test, wait_script_start, wait_script_end
assert moulti_test

def test_buttonquestion(moulti_test):
	command = ['buttonquestion.bash']
	async def run_before(pilot):
		await wait_script_start(pilot)
		await pilot.pause(.5)
		await pilot.press('ctrl+y') # next unanswered question
		await pilot.pause(.1)
		await pilot.press('tab', 'tab', 'enter') # hit 3rd button
		await wait_script_end(pilot)
	assert moulti_test(command=command, run_before=run_before)

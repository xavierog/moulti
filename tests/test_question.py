from .common import moulti_test, wait_script_start
assert moulti_test

def test_question(moulti_test):
	command = ['question.bash']
	async def run_before(pilot):
		await wait_script_start(pilot)
		await pilot.pause(.5)
		await pilot.press('ctrl+y') # next unanswered question
		await pilot.pause(.1)
		await pilot.press(*'Luka', 'tab', 'tab', 'tab', 'enter')
	assert moulti_test(command=command, run_before=run_before)

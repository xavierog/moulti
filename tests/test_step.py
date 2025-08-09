from moulti.widgets.step.tui import Step

def test_bytes_to_lines():
	# No data at all, no lines:
	assert Step.bytes_to_lines(b'') == ([], -1, b'', b'')

	# Empty line:
	assert Step.bytes_to_lines(b'\n') == ([''], 0, b'', b'')
	# One regular line:
	assert Step.bytes_to_lines(b'data\n') == (['data'], 4, b'', b'')
	# Multiple regular lines:
	assert Step.bytes_to_lines(b'data1\ndata02\n') == (['data1', 'data02'], 6, b'', b'')
	# Alternating regular and empty lines:
	assert Step.bytes_to_lines(b'data1\n\ndata02\n\ndata3\n') == (['data1', '', 'data02', '', 'data3'], 6, b'', b'')

	# Leftover only, no lines:
	assert Step.bytes_to_lines(b'leftover') == ([], -1, b'leftover', b'')
	# Empty line with leftover:
	assert Step.bytes_to_lines(b'\nleftover') == ([''], 0, b'leftover', b'')
	# One line with leftover:
	assert Step.bytes_to_lines(b'data\nleftover') == (['data'], 4, b'leftover', b'')
	# Multiple lines with leftover:
	assert Step.bytes_to_lines(b'data1\ndata02\nleftover') == (['data1', 'data02'], 6, b'leftover', b'')
	# Alternating regular and empty lines with leftover:
	assert Step.bytes_to_lines(b'data1\n\ndata02\n\ndata03\nleftover') == (['data1', '', 'data02', '', 'data03'], 6, b'leftover', b'')

from moulti.helpers import abridge_dict, abridge_string

def test_abridge_string():
	assert abridge_string('too small, not abridged') == 'too small, not abridged'
	assert abridge_string('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', 40) == 'ABCDEFGHIJKL...Zabcdefghij...z0123456789'
	assert abridge_string('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', 40, '.....') == 'ABCDEFGHIJ.....abcdefghij.....0123456789'

def test_abridge_dict():
	original_dict = {
		'foo': 'too small, not abridged',
		'bar': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
		'int': 1,
		'float': 1.1,
		'bool': True,
		'array': [
			'recursive? no, this function is not expected to work recursively',
		],
		'dict': {},
	}
	expected_dict = {
		'foo': 'too small, not abridged',
		'bar': 'ABCDEFGHIJKL...Zabcdefghij...z0123456789',
		'int': 1,
		'float': 1.1,
		'bool': True,
		'array': [
			'recursive? no, this function is not expected to work recursively',
		],
		'dict': {},
	}
	assert abridge_dict(original_dict, 40) == expected_dict

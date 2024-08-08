# List of moulti.widgets.* modules that provide non-abstract widgets that can be shown in Moulti.
WIDGET_MODULES = [
	'step',
	'buttonquestion',
	'inputquestion',
	'question',
	'divider',
]

class MoultiWidgetException(Exception):
	"""
	Generic exception that widgets may raise.
	"""

class MoultiWidgetInvalidPropertyException(MoultiWidgetException):
	"""
	Exception widgets may raise to indicate they were passed an invalid property.
	"""

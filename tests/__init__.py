from os import environ as environment_variables

# Remove MOULTI_* environment variables so as not to disrupt tests.
# For instance, MOULTI_CUSTOM_CSS can dramatically alter the resulting snapshots.
for variable_name in environment_variables:
	if variable_name.startswith('MOULTI_'):
		environment_variables.pop(variable_name)

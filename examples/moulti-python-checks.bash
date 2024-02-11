#!/usr/bin/env bash
export MOULTI_INSTANCE='moulti-python-checks'
source examples/moulti-functions.bash
[ "${MOULTI_RUN}" ] || exec moulti run "$0" "$@"

moulti step add versions --title='Versions' --bottom-text=' '
{
	ruff --version
	echo --
	mypy --version
	echo --
	pylint --version
} | moulti pass versions

moulti_exec ruff check setup.py src/moulti

moulti_exec mypy src/moulti/

function pylint {
	disable=(
		broad-exception-caught
		missing-{function,class,module}-docstring
		too-many-{instance-attributes,arguments,branches,public-methods,statements}
	)
	local IFS=,
	command pylint \
		--disable="${disable[*]}" \
		--indent-string='	' \
		--max-line-length=120 \
		--ignore-long-lines='add_argument' \
		src/moulti
}

moulti_exec pylint

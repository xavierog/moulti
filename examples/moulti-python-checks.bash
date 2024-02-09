#!/usr/bin/env bash
export MOULTI_SOCKET_PATH="@moulti-$(whoami)-moulti-python-checks.socket"
source examples/moulti-functions.bash
[ "${MOULTI_RUN}" ] || exec moulti run "$0" "$@"

moulti_exec ruff check setup.py src/moulti

moulti_exec mypy src/moulti/

function pylint {
	disable=(
		broad-exception-caught
		missing-{function,class,module}-docstring
		too-many-{instance-attributes,arguments,branches,public-methods}
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

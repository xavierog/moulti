#!/usr/bin/env bash
export MOULTI_INSTANCE='moulti-python-checks'
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

source moulti-functions.bash
moulti_check_requirements ruff mypy pylint

moulti step add versions --title='Versions' --bottom-text=' '
{
	ruff --version
	echo --
	mypy --version
	echo --
	pylint --version
	echo --
	pytest --version
} 2>&1 | moulti pass versions

moulti_exec ruff check src
moulti_exec mypy src
moulti_exec pylint src
moulti_exec pytest

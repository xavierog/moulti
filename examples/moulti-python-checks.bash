#!/usr/bin/env bash
export MOULTI_INSTANCE='moulti-python-checks'
source examples/moulti-functions.bash
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

moulti step add versions --title='Versions' --bottom-text=' '
{
	ruff --version
	echo --
	mypy --version
	echo --
	pylint --version
} | moulti pass versions

moulti_exec ruff check setup.py src
moulti_exec mypy src
moulti_exec pylint src

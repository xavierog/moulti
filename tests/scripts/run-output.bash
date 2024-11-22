#!/usr/bin/env bash

if [ "$1" == '--create-step' ]; then
	moulti step add moulti_run_output --class='warning' --title='Moulti unexpected output' --bottom-text=' '
fi

echo '[stdout] Unexpected output'
echo '[stderr] Unexpected output' > /dev/stderr


if [ "$1" == '--create-step' ]; then
	# The "moulti_run_output" step is locked upon reception of the first bytes
	# written on stdout or stderr, which is not instantaneous.
	sleep .5
	# This step cannot be deleted while the script is running, therefore this
	# should emit an error message... which should end up in that very step.
	moulti step delete moulti_run_output 2>&1
fi

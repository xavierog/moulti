#!/usr/bin/env bash

# Optionally create/destroy a beacon file that reflects whether this process is
# still running:
if [ "${MOULTI_TEST_BEACON}" ]; then
	touch "${MOULTI_TEST_BEACON}"
	function cleanup {
		unlink "${MOULTI_TEST_BEACON}"
	}
	trap cleanup EXIT
fi
sleep "$1"

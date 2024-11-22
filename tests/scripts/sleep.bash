#!/usr/bin/env bash

# Optionally create/destroy a beacon file that reflects whether this process is
# still running:
BEACON_PATH="${2}"
if [ "${BEACON_PATH}" ]; then
	touch "${BEACON_PATH}"
	function cleanup {
		unlink "${BEACON_PATH}"
	}
	trap cleanup EXIT
fi
sleep "$1"

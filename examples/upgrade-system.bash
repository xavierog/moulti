#!/usr/bin/env bash

export TERM=xterm-256color
[ "${MOULTI_RUN}" ] || exec moulti run "$0" "$@"

# We could use apt-get BUT there is no equivalent to apt list --upgradable.
function apt {
	local rc
	command apt "$@" 2>&1 | grep --line-buffered -vP '^(?:WARNING: apt does not have a stable CLI|$)' || true
	rc="${PIPESTATUS[0]}"
	return $rc
}

source moulti-functions.bash

export DEBIAN_FRONTEND=noninteractive
set -e
moulti wait --max-attempts=120
moulti_type set --title 'Moulti demo: Debian upgrade'
sleep 0.5

STEP_COLLAPSE_ON_SUCCESS=2
moulti_exec apt update
STEP_UPDATE_ARGS=(--classes=warning); STEP_COLLAPSE_ON_SUCCESS=5 moulti_exec apt list --upgradable
unset STEP_UPDATE_ARGS
moulti_exec apt full-upgrade -y
moulti_exec apt autoremove --purge
moulti_exec apt clean

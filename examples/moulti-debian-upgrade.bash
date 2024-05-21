#!/usr/bin/env bash

export TERM=xterm-256color
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

source moulti-functions.bash
moulti_check_requirements apt

# We could use apt-get BUT there is no equivalent to apt list --upgradable.
function apt {
	local rc
	command apt "$@" 2>&1 | grep --line-buffered -vP '^(?:WARNING: apt does not have a stable CLI|$)' || true
	rc="${PIPESTATUS[0]}"
	return "$rc"
}


export DEBIAN_FRONTEND=noninteractive
set -e
moulti_type set --title 'Moulti demo: Debian upgrade'
sleep 0.5

STEP_COLLAPSE_ON_SUCCESS=
STEP_ID=apt_update moulti_exec apt update

# Display the list of upgradable packages:
STEP_ID=apt_list   moulti_exec apt list --upgradable

# Get user confirmation:
moulti buttonquestion add confirmation --bottom-text=' ' \
	--title='Proceed with system upgrade?' \
	--button yes success 'Yes, upgrade' \
	--button no  error   'No, abort'
answer=$(moulti buttonquestion get-answer confirmation --wait)

# Stop there unless we explicitly get the green light:
if [ "${answer}" != 'yes' ]; then
	moulti buttonquestion update confirmation --bottom-text='Upgrade aborted.'
	exit 1
fi

# We got the greenlight: reflect it on the question itself and (slowly) collapse all previous steps:
moulti buttonquestion update confirmation --class=success
sleep 0.3
moulti step update apt_update --collapsed
sleep 0.3
moulti step update apt_list   --collapsed
sleep 0.3
moulti buttonquestion update confirmation --collapsed

# Finally proceed with the upgrade itself:
STEP_COLLAPSE_ON_SUCCESS=2 moulti_exec apt full-upgrade -y
STEP_COLLAPSE_ON_SUCCESS=1
moulti_exec apt autoremove --purge
moulti_exec apt clean

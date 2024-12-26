#!/usr/bin/env bash

# This example script leverages MOULTI_CUSTOM_CSS to implement a scoreboard
# with two steps next to each other despite Moulti NOT offering this feature in
# the first place.

# Usage:
# 1 - in a first terminal, run this script: ./moulti-scoreboard.bash
# 2 - in a second terminal, source this script: source ./moulti-scoreboard.bash
# This provides a bunch of bash functions to control the scoreboard:
# - scoreboard_timer_pause, scoreboard_timer_resume and scoreboard_timer_reset
#   pause, resume and reset the timer, respectively.
# - scoreboard_score_inc <team> <toilet_args> increments the selected team's score:
#     scoreboard_score_inc 1  # increment the home team's score
#     scoreboard_score_inc 2 --metal # increment the guest team's score
# - scoreboard_score_set_val <team> <score> <toilet_args> sets the selected team's score:
#     scoreboard_score_set_val 1 12 --metal # set the home team's score to 12
# - scoreboard_score_set_val <team> <text> <toilet_args> shows any arbitrary
#   text inside the selected team's display:
#     scoreboard_score_set_val 1 WIN --metal # display "WIN" instead of home team's score

# Part 1: variables and functions users should source to control the scoreboard:

export MOULTI_INSTANCE="scoreboard-${SCOREBOARD_INSTANCE:-default}"
export SCOREBOARD_CONTROL_PATH="${SCOREBOARD_CONTROL_PATH:-/tmp/scoreboard-control}"
declare -a SCOREBOARD_SCORES=('' 0 0)

function scoreboard_score_inc {
	local team="${1}"; shift
	local score
	((score=++SCOREBOARD_SCORES[$team]))
	scoreboard_score_set_val "${team}" "${score}" "$@"
}

function scoreboard_score_set_val {
	local team="${1}"; shift
	local score="${1}"; shift
	SCOREBOARD_SCORES[$team]="${score}"
	scoreboard_score_set_text "${team}" "${score}" "$@"
}

function scoreboard_score_set_text {
	local team="team${1}"; shift
	toilet --font mono12 --filter=crop "$@" | moulti pass "${team}"
}

function scoreboard_timer_reset {
	touch "${SCOREBOARD_CONTROL_PATH}-timer-reset"
}

function scoreboard_timer_pause {
	touch "${SCOREBOARD_CONTROL_PATH}-timer-pause"
}

function scoreboard_timer_resume {
	rm -f "${SCOREBOARD_CONTROL_PATH}-timer-pause"
}

[ "$0" != "${BASH_SOURCE[0]}" ] && return 0

# Part 2: spawn a new Moulti instance:

if [ -z "${MOULTI_RUN}" ]; then
	export MOULTI_QUIT_POLICY='default=quit;running=terminate'
	export MOULTI_RUN_OUTPUT='harvest'

	# This script embeds a custom TCSS file for Moulti:
	MOULTI_CUSTOM_CSS=$(mktemp)
	sed '1,/<<SCOREBOARD_CSS$/ d' "$0" > "${MOULTI_CUSTOM_CSS}"
	export MOULTI_CUSTOM_CSS

	# Like all Textual applications, Moulti obeys $COLUMNS and $LINES:
	[ "${SCOREBOARD_COLUMNS}" ] && export COLUMNS="${SCOREBOARD_COLUMNS}"
	[ "${SCOREBOARD_LINES}" ] && export LINES="${SCOREBOARD_LINES}"

	exec moulti run -- "$0" "$@"
fi

# Part 3: driver script:

rm -f "${MOULTI_CUSTOM_CSS}"

source moulti-functions.bash
moulti_check_requirements 'toilet' 'stdbuf' ||\
	moulti buttonquestion delete moulti_check_requirements

moulti step add team1 --bottom-text=' ' --title='HOME' --collapsed
moulti step add team2 --bottom-text=' ' --title='GUEST' --collapsed
moulti step add timer --bottom-text=' ' --title='Time'
scoreboard_score_set_val 1 0 --metal
scoreboard_score_set_val 2 0 --metal
moulti step update team1 --no-collapsed
moulti step update team2 --no-collapsed

if [ $(uname) == 'OpenBSD' ]; then
	# On OpenBSD, "unbuffer simply exits when it encounters an EOF from [...] its input".
	# Therefore, the while-sleep loop below must exit when Moulti exits.
	function sleep {
		command sleep "$@" && moulti wait --max-attempts=1
	}
fi

{
	FORMAT="${SCOREBOARD_TIMER_FORMAT:-%03d:%02d\n}"
	# shellcheck disable=SC2059
	printf "${FORMAT}" 0 0
	prev_mode=''
	total=0
	elapsed=0
	start=$(date +%s)
	while sleep .5; do
		# Handle reset requests:
		if [ -e "${SCOREBOARD_CONTROL_PATH}-timer-reset" ]; then
			start=$(date +%s)
			total=0
			moulti step clear timer
			# shellcheck disable=SC2059
			printf "${FORMAT}" 0 0
			rm -f "${SCOREBOARD_CONTROL_PATH}-timer-reset"
		fi
		# Handle pause/resume requests:
		[ -e "${SCOREBOARD_CONTROL_PATH}-timer-pause" ] && mode='pause' || mode=''
		if [ "${prev_mode}" != "${mode}" ]; then
			prev_mode="${mode}"
			if [ "${mode}" == "pause" ]; then
				total="${elapsed}"
			else # resume
				start=$(date +%s)
			fi
		fi
		# Update the timer display:
		if [ "${mode}" != 'pause' ]; then
			now=$(date +%s)
			# Clear the timer step every ~5 minutes
			((elapsed=total+now-start,min=elapsed/60,sec=elapsed%60,clear=elapsed%300))
			[ "${clear}" == '0' ] && moulti step clear timer
			# shellcheck disable=SC2059
			printf "${FORMAT}" "${min}" "${sec}"
		fi
	done
} | stdbuf -i0 -o0 toilet --font mono12 --filter=crop | moulti pass timer

exit 0
# Part 4: custom Textual CSS:
# shellcheck disable=all
: <<SCOREBOARD_CSS
/* Remove header, footer and tooltips: */
Tooltip, Footer, #header {
	display: none;
}

StepContainer {
	align-horizontal: center;
	align-vertical: middle;
	layers: teams time;
}

MoultiLog {
	scrollbar-background: black;
	scrollbar-color: black;
}

#step_team1 {
	background: blue;
	layer: teams;
	offset: 0 0;
	position: absolute;
	width: 50%;
}

#step_team2 {
	background: red;
	layer: teams;
	offset: 50vw 0;
	position: absolute;
	width: 50%;
}

#step_timer {
	background: white;
	width: 67;
	layer: time;
	& MoultiLog { height: 7; }
}

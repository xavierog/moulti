#!/usr/bin/env bash

function output {
	local max="${1}"; shift
	while sleep 0.1; do
		echo "$@"
	done | stdbuf --output=0 head "-${max}"
}

moulti step add 1 --min-height=10 --max-height=10 --title='Step with auto-scroll enabled by default'
moulti step add 2 --min-height=10 --max-height=10 --title='Step with auto-scroll disabled' --no-auto-scroll
moulti step add 3 --min-height=10 --max-height=10 --title='Step with auto-scroll enabled by default'
output 40 'interrupted auto-scrolling' | moulti pass 1 &
output 40 'no auto-scrolling'          | moulti pass 2 &
output 40 'auto-scrolling'             | moulti pass 3 &
wait

#!/usr/bin/env bash
moulti set --title='git show ba89966c1984'
export MOULTI_DIFF_NO_TITLE=yes
export MOULTI_DIFF_VERBOSE=yes
first_step=$(moulti diff parse tests/data/linux-kernel-ba89966c1984.patch | head -1 | sed 's/[a-z]* //')
moulti step update "${first_step}" --max-height=7

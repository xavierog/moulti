#!/usr/bin/env bash

# Force bash to populate $LINES:
shopt -s checkwinsize
:|:
export LINES

export MOULTI_INSTANCE='needle-haystack'
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

set -e
source moulti-functions.bash
moulti_check_requirements 'seq'

factor="${FACTOR:-1000}"
((before=11*factor))
((middle=11*factor))
((after=11*factor))
((last_line=before+middle+after))

haystack_x1=' haystack'
needle_x1=' needle  '
printf -v haystack_x10 "%.0s${haystack_x1}" {1..10}
haystack_format="%6.f${haystack_x10}${haystack_x10}${haystack_x10}${haystack_x1}"
needle_format="%6d${haystack_x10}${haystack_x10}${needle_x1}${haystack_x10}\n"

function needle_in_haystack {
	local needle_line_number
	((needle_line_number=before+RANDOM%middle))
	seq -f "${haystack_format}" 1 "${needle_line_number}"
	((needle_line_number++))
	# shellcheck disable=SC2059
	printf "${needle_format}" "${needle_line_number}"
	((needle_line_number++))
	seq -f "${haystack_format}" "${needle_line_number}" "${last_line}"
}

lines="${LINES:-30}"
((lines=(lines-3)/2))

moulti set --title='Find needles inside the haystacks'
for i in {1..5}; do
	moulti step add "haystack${i}" --title="Haystack #${i}" --max-height="${lines}"
done
needle_in_haystack | moulti pass "haystack1" &
needle_in_haystack | moulti pass "haystack2" &
wait
needle_in_haystack | moulti pass "haystack3" &
needle_in_haystack | moulti pass "haystack4" &
wait
needle_in_haystack | moulti pass "haystack5"

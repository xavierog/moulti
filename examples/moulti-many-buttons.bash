#!/usr/bin/env bash

export MOULTI_INSTANCE='many-buttons'
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

moulti set --title='So I heard you love buttons...'

CLASSES=('default' 'success' 'warning' 'error' 'primary')
CITIES=(
	'Bangkok'
	'Paris'
	'London'
	'Dubai'
	'Singapore'
	'Hong Kong'
	'New York'
	'Istanbul'
	'Kuala Lumpur'
	'Seoul'
	'Edinburgh'
	'Tokyo'
	'Barcelona'
	'Amsterdam'
	'Rome'
	'Shanghai'
	'Y'
	'Los Angeles'
	'Prague'
	'Miami'
	'Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch'
	'Dublin'
	'San Francisco'
	'Taipei'
	'Sydney'
	'Lisbon'
	'Madrid'
	'Vienna'
	'Munich'
	'Toronto'
	'Buenos Aires'
	'Rio de Janeiro'
	'Moscow'
	'Athens'
	'Cairo'
	'Cancun'
	'Lima'
	'Santiago'
)
for city in "${CITIES[@]}"; do
	((idx=RANDOM%5))
	class="${CLASSES[$idx]}"
	printf -- '--button\0%s\0%s\0%s\0' "${city}" "${class}" "${city}"
done | xargs --null -- moulti buttonquestion add city \
	--title='Let'\''s start with a simple question' \
	--top-text='Ok, maybe not that simple...' \
	--bottom-text='Your ad here! Call 1-800-555-0199' \
	--text='What is your favorite city?'

STRINGS=(
	'1'
	'21'
	'ABC'
	'ABCD'
	'ABCDEFG'
	'ABCDEFGHIJKLMNO'
	'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg'
	'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/*-+='
)
num_strings="${#STRINGS[@]}"
for ((i=1; i<=7; ++i)); do
	for class in primary success warning error default; do
		((idx=RANDOM%num_strings))
		echo '--button' "${i}-${class}" "${class}" "${STRINGS[$idx]}"
	done
done | xargs -- moulti buttonquestion add button \
	--title='Ok, it works but...' \
	--top-text='We need more chaotic names to test the layout feature' \
	--bottom-text='This script was written while petting my cat' \
	--text='What is your favorite button?' \
	--classes='warning'

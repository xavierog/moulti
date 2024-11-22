#!/usr/bin/env bash
MAX="$1"
function run {
	((STEP >= MAX)) && exit 0
	"$@"
	((++STEP))
}
title=$'This text is simply displayed.\nMulti-line is possible. So is [i]rich formatting[/]'
run moulti divider add my_first_divider --title="${title}"
run moulti divider update my_first_divider --classes=warning
run moulti divider delete my_first_divider

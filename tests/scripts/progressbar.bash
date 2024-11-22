#!/usr/bin/env bash
MAX="$1"
function run {
	((STEP >= MAX)) && exit 0
	"$@"
	((++STEP))
}
run moulti set --progress-bar --progress=20 --progress-target=100 # used to be 1138/5555 but liable to bring floating point subtleties and rounding issues
run moulti set --progress 80 --progress-target 100
run moulti set --progress +20
run moulti set --progress -5

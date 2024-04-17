function moulti_python {
	if command -v python3 > /dev/null; then
		python3 "$@"
	else
		python "$@"
	fi
}

function moulti_duration {
	ts_start="$(date -d "$1" "+%s%N")"
	ts_end="$(date -d "$2" "+%s%N")"
	moulti_python -c '
from sys import argv
delta = int(argv[2]) - int(argv[1]) # delta is in nanoseconds
figures = []
for x in (60*10**9, 60, 24): # seconds, hours, days
	figures.insert(0, delta % x)
	delta //= x
figures.insert(0, int(delta))
figures[-1] /= 10**9
print(" ".join((f"{value}{unit}" for value, unit in zip(figures, "dhms") if value > 0)))
' "${ts_start}" "${ts_end}"
}

# Examples:
# moulti_exec find . -type f -name '*.py' -ls
# moulti_exec other_bash_function arg1 arg2
# STEP_ADD_ARGS=(--max-height=0); STEP_ID=my_step ip -color address
# STEP_PASS_ARGS=(--read-size=64); STEP_UPDATE_ARGS=(--collapse); ping example.org
function moulti_exec {
	local id rc result
	# Generate a random step id if none was provided:
	id="${STEP_ID:-${RANDOM}${RANDOM}}"
	# Create a step; set the STEP_ADD_ARGS array to customise it:
	timestamp_start="$(date --iso-8601=ns)"
	moulti step add "${id}" --title="$*" --top-text="Started ${timestamp_start}" --bottom-text="still running..." --scroll-on-activity=-1 "${STEP_ADD_ARGS[@]}"
	# Run the given command and pipe its output to Moulti; set the STEP_PASS_ARGS array to fine-tune the piping (e.g. read size):
	"$@" < /dev/null 2>&1 | moulti pass "${id}" "${STEP_PASS_ARGS[@]}"
	# Harvest the command's return code and the time it ended:
	rc="${PIPESTATUS[0]}"
	timestamp_end="$(date --iso-8601=ns)"
	# Determine the new step color based on the return code:
	[ "${rc}" == 0 ] && result='success' || result='error'
	# Update the step; set the STEP_UPDATE_ARGS array to further customise it:
	duration=$(moulti_duration "${timestamp_start}" "${timestamp_end}")
	moulti step update "${id}" --bottom-text="Exited  ${timestamp_end} with RC ${rc} after ${duration}" --classes="${result}" --scroll-on-activity=false "${STEP_UPDATE_ARGS[@]}"
	[ "${rc}" == 0 ] && [ "${STEP_COLLAPSE_ON_SUCCESS}" ] && { moulti_delayed_collapse "${id}" "${STEP_COLLAPSE_ON_SUCCESS}" & }
	# Exit with the same return code as the given command:
	return "${rc}"
}

function moulti_delayed_collapse {
	sleep "${2:-5}"
	moulti step update "${1}" --collapsed
}

function moulti_type {
	local string="${@: -1}" # last argument
	string_length="${#string}"
	for (( i=1; i <= string_length; i++ )); do
		moulti "${@:1:$#-1}" "${string:0:i}" # all arguments but the last one, followed by the partial string
		# No sleep because this hack is already inefficient enough.
	done
}

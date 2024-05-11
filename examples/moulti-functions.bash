function moulti_python {
	# This will not age well:
	for name in python3 python3.{10..13} python; do
		if command -v "${name}" > /dev/null; then
			"${name}" "$@"
			break
		fi
	done
}

function moulti_iso_date {
	# This Perl one-liner is about 10 times slower than GNU date but Perl is
	# more ubiquitous than GNU date.
	perl -MPOSIX -MTime::HiRes -e '
		($s, $us) = Time::HiRes::gettimeofday();
		@lt = localtime($s);
		$dt = strftime(q[%FT%T], @lt);
		$tz = strftime(q[%z], @lt);
		printf(qq[%s.%03d%s\n], $dt, $us / 1000, $tz);'
}

function moulti_duration {
	moulti_python -c '
from sys import argv
from datetime import datetime
date1 = datetime.strptime(argv[1], "%Y-%m-%dT%H:%M:%S.%f%z")
date2 = datetime.strptime(argv[2], "%Y-%m-%dT%H:%M:%S.%f%z")
duration  = str(date2 - date1)
print(duration[:-3])
' "$@"
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
	timestamp_start="$(moulti_iso_date)"
	moulti step add "${id}" --title="$*" --top-text="Started ${timestamp_start}" --bottom-text="still running..." --scroll-on-activity=-1 "${STEP_ADD_ARGS[@]}"
	# Run the given command and pipe its output to Moulti; set the STEP_PASS_ARGS array to fine-tune the piping (e.g. read size):
	"$@" < /dev/null 2>&1 | moulti pass "${id}" "${STEP_PASS_ARGS[@]}"
	# Harvest the command's return code and the time it ended:
	rc="${PIPESTATUS[0]}"
	timestamp_end="$(moulti_iso_date)"
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

MOULTI_NEW_STEP_PATTERN='^([-=#@]+)(\s*)(.+?)\2\1$'

function moulti_process_lines {
	exec {original_stdout}>&1
	local step_counter=0
	local step_id
	IFS=''
	while read -r line; do
		if [[ "${line}" =~ ${MOULTI_NEW_STEP_PATTERN} ]]; then
			((++step_counter))
			local prev_id="${step_id}"
			local next_id="$$_step_${step_counter}"
			step_id=$(moulti_make_step "${prev_id}" "${next_id}" "${line}" "${BASH_REMATCH[@]}" < /dev/null)
			if [ "${step_id}" ] && [ "${step_id}" != "${prev_id}" ]; then
				# Redirect stdout to `moulti pass our_new_step`
				exec > >(moulti pass "${step_id}")
			else
				step_id="${prev_id}"
			fi
		fi
		moulti_inspect_line "${line}" "${step_id}" < /dev/null
	done
	exec 1>&${original_stdout}
}

# Arguments:
# 1: previous step id
# 2: next step id (suggestion)
# 3: current line (complete, no CR/LF)
# 4: matched substring
# 5: capture #1
# 6: capture #2, etc.
# This function MUST output the id of the created step.
function moulti_make_step {
	# Default implementation: use the complete line as title:
	moulti step add "$2" --title="$3" --bottom-text=' ' --scroll-on-activity=-1 && echo "$2"
}

# Arguments:
# 1: current line (complete, no CR/LF)
# 2: current step id
function moulti_inspect_line {
	# Default implementation: systematically output the line:
	printf '%s\n' "$1"
}

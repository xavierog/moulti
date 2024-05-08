#!/usr/bin/env bash

export TERM=xterm-256color
export MOULTI_INSTANCE='generate-ssh-keys'
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

set -e
source moulti-functions.bash

# Run moulti_exec with stdbuf and a simplified ssh-keygen command in the title:
function ssh_keygen {
	local filepath="${1}"
	STEP_ADD_ARGS=( --title="ssh-keygen -t rsa -f ${filepath}" )
	STEP_COLLAPSE_ON_SUCCESS=2
	moulti_exec stdbuf -o0 ssh-keygen -t rsa -b 6144 -N '' -f "${filepath}"
}

# Remove our useless keys (I mean, RSA? In 2024?)
function cleanup {
	cd "${tmp_dir}"
	rm -rf "${working_dir:?nope}"
}

tmp_dir="${TMPDIR:-/tmp}"
working_dir=$(mktemp -p "${tmp_dir}" -d "${MOULTI_INSTANCE}.$(date '+%s').XXXXXXXXXX")
trap cleanup EXIT
cd "${working_dir}"

moulti wait --max-attempts=120

max_keys=10
printf -v title $'Moulti demo: progress bar\nGenerating [b]%d[/b] SSH keys\nin [i]%s[/i]' "${max_keys}" "${working_dir}"
moulti set --title="${title}" --progress-bar --progress-target="${max_keys}"
for ((i=1; i <= max_keys; ++i)); do
	ssh_keygen "./${i}"
	moulti set --progress +1
done

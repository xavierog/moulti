#!/usr/bin/env bash
export MOULTI_INSTANCE='pass-concurrency'
export MOULTI_PASS_CONCURRENCY="${MOULTI_PASS_CONCURRENCY:-8}"
step_height=7
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"
source moulti-functions.bash
moulti_check_requirements ping
for (( i=1; i<=MOULTI_PASS_CONCURRENCY; i++ )); do
	moulti step add "${i}" --title="Ping #${i}" --bottom-text=' ' --min-height="${step_height}" --max-height="${step_height}"
done
for (( i=1; i<=MOULTI_PASS_CONCURRENCY; i++ )); do
	ping localhost | moulti pass "${i}" &
done
wait

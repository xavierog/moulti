#!/usr/bin/env bash
export MOULTI_INSTANCE='pass-concurrency'
export MOULTI_PASS_CONCURRENCY="${MOULTI_PASS_CONCURRENCY:-8}"
step_height=7
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"
moulti wait
for i in $(seq 1 "${MOULTI_PASS_CONCURRENCY}"); do
	moulti step add "${i}" --title="Ping #${i}" --bottom-text=' ' --min-height="${step_height}" --max-height="${step_height}"
done
for i in $(seq 1 "${MOULTI_PASS_CONCURRENCY}"); do
	ping localhost | moulti pass "${i}" &
done
wait

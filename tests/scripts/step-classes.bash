#!/usr/bin/env bash
for class in warning error inactive standard customstate; do
    moulti step add "${class}_example" \
        --classes="${class}" \
        --title="$(tr '[:lower:]' '[:upper:]' <<< ${class:0:1})${class:1} step" \
        --text="This is a step with class '${class}'." \
        --bottom-text=' '
done

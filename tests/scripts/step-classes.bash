#!/usr/bin/env bash
for class in warning error inactive standard customstate; do
    moulti step add "${class}_example" \
        --classes="${class}" \
        --title="${class^} step" \
        --text="This is a step with class '${class}'." \
        --bottom-text=' '
done

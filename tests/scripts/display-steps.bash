#!/usr/bin/env bash
moulti set "$@"
echo {1..10} | xargs -n 1 moulti step add

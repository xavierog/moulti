#!/usr/bin/env bash
debian='docker.io/library/debian'
image="xavierong/moulti-demo"
# The latest stable image may not need any package to upgrade, so use the previous one:
penultimate_stable=$(podman search --list-tags "${debian}" --limit=20000 --no-trunc --format='{{.Tag}}' | grep -P '^stable-\d{8}-slim$' | tail -2 | head -1)
exec podman build --tag "${image}:latest" --tag "${image}:$(date '+%Y%m%d')" --squash --from="${debian}:${penultimate_stable}" --file=container/demo/Dockerfile ../../

#!/usr/bin/env bash
debian='docker.io/library/debian'
image="xavierong/moulti-demo"

echo "Looking for the latest ${debian}:stable-YYYYMMDD-slim image that has upgradable packages:"
upgradable_command='apt update &> /dev/null && apt list --upgradable 2> /dev/null | grep --quiet /'
while read -r tag; do
	echo -n "${debian}:${tag}..."
	podman run --rm "${debian}:${tag}" /usr/bin/bash -c "${upgradable_command}" && break
	echo -e "\b\b\b: no upgradable packages"
done < <(podman search --list-tags "${debian}" --limit=20000 --no-trunc --format='{{.Tag}}' | grep -P '^stable-\d{8}-slim$' | tac)
echo -e "\b\b\b: ok"

exec podman build --tag "${image}:latest" --tag "${image}:$(date '+%Y%m%d')" --squash --from="${debian}:${tag}" --file=container/demo/Dockerfile ../../

#!/usr/bin/env bash
# Convert Gogh themes (YAML) to MOULTI_ANSI_THEME_* environment variables.
# Launched without any argument: get the Gogh Git repository and convert all its themes.
# Launched with at least one argument: assume all arguments are filepaths and attempt to convert them.

function extract {
	grep -o -P "${1}"':.*#[0-9A-Fa-f]{6}' "${2}"
}

function just_the_color_please {
	grep -o -P '[0-9A-Fa-f]{6}$'
}

function gogh_theme_yaml_to_moulti_env_var {
	local file name bg fg colors
	file="${1}"
	name=$(basename "${file}" '.yml' | sed 's/[^A-Za-z0-9_]/_/g')
	bg=$(extract 'background' "${file}" | just_the_color_please)
	fg=$(extract 'foreground' "${file}" | just_the_color_please)
	readarray -t colors < <(extract 'color_(0[1-9]|1[0-6])' "${file}" | sort | just_the_color_please)
	local IFS=':'
	printf 'export MOULTI_ANSI_THEME_%s=bg=%s,fg=%s,ansi=%s\n' "${name}" "${bg}" "${fg}" "${colors[*]}"
}

function gogh_theme_yaml_to_moulti_env_var_loop {
	for file in "$@"; do
		gogh_theme_yaml_to_moulti_env_var "${file}"
	done
}

function gogh2moulti_main {
	[ -d gogh ] || git clone https://github.com/Gogh-Co/Gogh.git gogh
	gogh_theme_yaml_to_moulti_env_var_loop gogh/themes/*.yml
}

# Sourcing this file? Stop here.
return 2> /dev/null

set -e
if [ $# -eq 0 ]; then
	gogh2moulti_main
else
	gogh_theme_yaml_to_moulti_env_var_loop "$@"
fi

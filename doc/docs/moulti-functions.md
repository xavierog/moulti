# Shell functions

Moulti offers a library of bash helpers named [moulti-functions.bash](https://github.com/xavierog/moulti/blob/master/examples/moulti-functions.bash), which should be available through `$PATH`.

Usage: `source moulti-functions.bash`

## Functions

### moulti_tool_is_available

Usage: `moulti_tool_is_available command_name`

Return whether the given command name is available (either in `$PATH` or as a shell built-in).

!!! example

    ```bash
    if moulti_tool_is_available rg; then
        echo "ripgrep is available"
    fi
    ```

### moulti_any_tool_is_available

Usage: `moulti_any_tool_is_available "cmd_name_1|cmd_name_2|...|cmd_name_n"`

Return whether any of the given command names is available (either in `$PATH` or as a shell built-in).

!!! example

    ```bash
    if moulti_any_tool_is_available 'ack|hgrep|rg'; then
        echo "at least one of ack, hgrep or rg is available"
    fi
    ```

### moulti_check_requirements

Usage: `moulti_check_requirements req_1 req_2 ... req_n`

`moulti_check_requirements` checks all given requirements and displays a `buttonquestion` step if any is missing.
This is often needed when writing portable shell scripts.

![moulti_check_requirements](assets/images/moulti-check-requirements.svg)

If the end user clicks "No", this function calls `exit 1`, thus ending the calling script.
Otherwise, it returns whether all requirements are met.

There are three ways to specify a requirement:

- stating a single command name
- stating multiple alternative command names separated with pipe characters
- stating a command to run along with its expected return code:

    `ret:expected-return-code:arbitrary-shell-command`

!!! example

    ```bash
    moulti_check_requirements 'grep' 'qemu-system-arm64' 'rg|hgrep|ack' \
        'ret:0:qemu-img --help | grep -w bitmap'
    ```

    This ensures that:

    - `grep` is available
    - `qemu-system-arm64` is available
    - `rg`, `hgrep` or `ack` is available
    - `qemu-img` features the "bitmap" subcommand

### moulti_python

Usage: `moulti_python python_arguments`

Depending on the underlying operating system, calling `python` may not work: some OS offer Python as `python3`, others as e.g. `python3.12`.

`moulti_python` tries:

- `python3`
- `python3.10`, `python3.11`, `python3.12`, etc.
- `python`

!!! example

    ```console
    $ source moulti-functions.bash
    $ moulti_python --version
    Python 3.13.2
    ```

### moulti_iso_date

Usage: `moulti_iso_date`

`moulti_iso_date` outputs the current date, time and timezone, with millisecond precision.

!!! example

    ```console
    $ source moulti-functions.bash
    $ moulti_iso_date
    2025-02-27T16:36:09.758+01:00
    ```

Under the hood, `moulti_iso_date` tries:

- date --iso-8601=ns
- gdate --iso-8601=ns
- Perl module Time::HiRes
- Python module datetime

### moulti_duration

Usage: `moulti_duration timestamp1 timestamp2`

`moulti_duration` prints the amount of time elapsed between the given timestamps, with millisecond precision.
Both timestamps should use the same format as [`moulti_iso_date`](#moulti_iso_date).

!!! example

    ```console
    $ source moulti-functions.bash
    $ moulti_duration '2025-02-27T16:36:09.758+01:00' '2025-02-28T19:38:50.312+01:00'
    1 day, 3:02:40.554
    ```

### moulti_exec

Usage: `moulti_exec command`

`moulti_exec` makes it easy to turn a command (or shell function) into a dedicated Moulti step with various bells and whistles.

Specifically, `moulti_exec`:

- creates a Moulti step using the given command as title, the current date and time as top text and "still running..." as bottom text;
- runs the given command with both stdout and stderr passed to that step, with scroll-on-activity enabled;
- waits until the command has finished running;
- updates the bottom text to reflect the current date and time, the return code and the amount of time the command took;
- sets the `success` or `error` class depending on the given command's return code;
- disables scroll-on-activity;
- collapses the step after `STEP_COLLAPSE_ON_SUCCESS` seconds if the return code is 0 and `STEP_COLLAPSE_ON_SUCCESS` is set;
- returns the same return code as the command.

This behavior can be further controlled by setting the following variables before calling `moulti_exec`:

- `STEP_ID`: id of the step to create; defaults to a pseudo-random number.
- `STEP_ADD_ARGS`: array of extra arguments passed to `moulti step add` when creating the step
- `STEP_PASS_ARGS`: array of extra arguments passed to `moulti pass` when running the command
- `STEP_UPDATE_ARGS`: array of extra arguments passed to `moulti step update` after the command has finished running
- `STEP_COLLAPSE_ON_SUCCESS`: how many seconds to wait before collapsing the step if the command succeeded

!!! example

    ```bash
    moulti_exec true
    moulti_exec false
    moulti_exec rsync -av moulti/doc/ remote:/moulti-doc/
    ```

    ![moulti-exec](assets/images/moulti-exec.svg)

### moulti_delayed_collapse

Usage: `moulti_delayed_collapse step_id [duration]`

Collapse the given step after the given duration (expressed in seconds), which defaults to 5 seconds.
This function is synchronous, so you may want to use `&` to run it in the background.

!!! example

    ```bash
    moulti_delayed_collapse my_step 3 &
    ```

### moulti_type

Usage: `moulti_type moulti_arguments string`

!!! Example

    ```bash
    moulti_type moulti step update example --title "This text appears one character at a time"
    ```

<div id="asciicast-demo-moulti-type" style="z-index: 1; position: relative; max-width: 100%;"></div>
<script>
function setup_demo_moulti_type() {
	const player = AsciinemaPlayer.create(
		'../assets/asciicasts/demo-moulti-type.cast',
		document.getElementById('asciicast-demo-moulti-type'),
		{ autoPlay: true, cols: 100, controls: false, preload: true, rows: 5, }
	);
	/* Prevent a visual glitch by looping between the first marker ("ready") and the end: */
	player.addEventListener('ended', () => {
		player.seek({ marker: 0 }).then(() => { player.play(); });
	});
}
try {
	asc_player = AsciinemaPlayer; /* may throw ReferenceError */
	setup_demo_moulti_type();
} catch (ReferenceError) {
	/* The Asciinema JS file has not loaded yet: defer setup until after the page has loaded: */
	addEventListener('load', (event) => { setup_demo_moulti_type(); });
}
</script>


!!! danger "Do not use `moulti_type` with `add` commands like `moulti step add`."
!!! danger "Do not use syntax `--moulti-argument=string`."
!!! success "Use syntax `--moulti-argument string` instead."

### stdbuf

Usage: `stdbuf command`

`stdbuf` is a [polyfill](https://en.wikipedia.org/wiki/Polyfill_(programming)) function.
It attempts to provide a counterpart to [GNU coreutils' stdbuf](https://www.man7.org/linux/man-pages/man1/stdbuf.1.html) on operating systems that do not offer it out of the box.

!!! info

    This function is provided only on:

    - NetBSD
    - OpenBSD, but only if `unbuffer` is available

    It is advised to ensure `stdbuf` is actually available using [moulti_tool_is_available](#moulti_tool_is_available) or [moulti_check_requirements](#moulti_check_requirements).


### moulti_process_lines

Usage: `moulti_process_lines`

moulti_process_lines turns arbitrary text input into Moulti steps.
To this end, it reads lines from stdin and matches them against [MOULTI_NEW_STEP_PATTERN](#moulti_new_step_pattern).
If a line matches, it is passed to [moulti_make_step](#moulti_make_step), else it is passed to [moulti_inspect_line](#moulti_inspect_line).

!!! info "See [Migrating existing scripts](existing-scripts.md) for detailed explanations."

### moulti_make_step

Usage: `moulti_make_step previous_step_id suggested_next_step_id current_line matched_substring [capture ...]`

!!! info "You should not call this function but rather implement your own variant."
    See [Migrating existing scripts](existing-scripts.md), specifically the [Create Steps](existing-scripts.md#create-steps) section.

`moulti_make_step` is called each time [moulti_process_lines()](#moulti_process_lines) encounters an input line that matches [MOULTI_NEW_STEP_PATTERN](#moulti_new_step_pattern).
Its numerous arguments are meant to provide enough context to create a new step:

- `$1`: previous_step_id: id of the previous step, or empty string if this function should create the first one
- `$2`: suggested_next_step_id: suggested step id
- `$3`: current_line: complete input line, without trailing CR/LF, that matched [MOULTI_NEW_STEP_PATTERN](#moulti_new_step_pattern) and triggered the function call
- `$4`: matched_substring: subset of the input line that matched [MOULTI_NEW_STEP_PATTERN](#moulti_new_step_pattern)
- `$5, $6, ...`: capture: 0 to n substrings resulting from [MOULTI_NEW_STEP_PATTERN](#moulti_new_step_pattern) capturing groups

!!! danger "This function does not have to create a new step but, if it does, it MUST print the created step id on stdout."

### moulti_inspect_line

Usage: `moulti_inspect_line current_line current_step_id`

!!! info "You should not call this function but rather implement your own variant."
    See [Migrating existing scripts](existing-scripts.md), specifically the [Pass content](existing-scripts.md#pass-content) section.

`moulti_inspect line` is called each time [moulti_process_lines()](#moulti_process_lines) encounters an input line that should be passed to the current step.

`moulti_inspect_line` may:

- keep the line untouched: `printf '%s\n' "$1"`
- adjust the line: `printf '%s\n' "foo ${1//bar/} baz"` -- it is also possible to output multiple lines
- discard the line: `return`

## Variables

### MOULTI_NEW_STEP_PATTERN

Default value: `^([-=#@]+)(\s*)(.+?)\2\1$`

This [POSIX extended regex](https://en.wikibooks.org/wiki/Regular_Expressions/POSIX-Extended_Regular_Expressions) is meant to match lines that should be turned into steps.
The matching itself is done by [moulti_process_lines](#moulti_process_lines).
Regex captures are passed to [moulti_make_step](#moulti_make_step).

The default pattern matches lines surrounded with an equal number of `-`, `=`, `#` or `@` characters:

- `------ Title ------`
- `===== Title =====`
- `#### Title ####`
- `@@@ Title @@@`

Whitespace between the title and these characters is optional but must remain symmetric:

- `------Title------`
- `===== Title =====`
- `####  Title  ####`
- `@@@   Title   @@@`

Capturing groups:

1. `-`, `=`, `#` or `@` characters
2. whitespace between these characters and the title
3. title

!!! info "See [Migrating existing scripts](existing-scripts.md), specifically the [Match titles](existing-scripts.md#match-titles) section."

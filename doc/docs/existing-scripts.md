# Migrating existing scripts

The previous section explained how to write new scripts that spawn and drive a Moulti instance.
But what about pre-existing scripts? Theoretically, it is always possible to rewrite an existing script so it leverages Moulti.
But in practice, rewriting can be time-consuming, error-prone and, overall, expensive.
In that case, another approach is to write a wrapper that runs the existing script, creates Moulti steps on the fly and dispatches its output.

To this end, [Moulti shell functions](moulti-functions.md) provide a function named `moulti_process_lines` that:

1. reads lines from the standard input
2. matches these lines against the pattern found in variable `$MOULTI_NEW_STEP_PATTERN`
3. creates a new Moulti step by calling `moulti_make_step()` each time it stumbles upon this pattern
4. sends all lines to the latest created step by calling `moulti_inspect_line()`.

## Example
`first-lines` is an existing tool that no one wants to modify.
Its output is:

```console
$ first-lines dickens --limit=3
==== A Christmas Carol ====

Marley was dead: to begin with. There is no doubt whatever about that. The
register of his burial was signed by the clergyman, the clerk, the undertaker,
and the chief mourner. Scrooge signed it: and Scrooge's name was good upon
'Change, for anything he chose to put his hand to. Old Marley was as dead as a
door-nail.

==== A Tale of Two Cities ====

It was the best of times, it was the worst of times, it was the age of wisdom,
it was the age of foolishness, it was the epoch of belief, it was the epoch of
incredulity, it was the season of Light, it was the season of Darkness, it was
the spring of hope, it was the winter of despair, we had everything before us,
we had nothing before us, we were all going direct to Heaven, we were all
going direct the other way—in short, the period was so far like the present
period, that some of its noisiest authorities insisted on its being received,
for good or for evil, in the superlative degree of comparison only.

==== David Copperfield ====

Whether I shall turn out to be the hero of my own life, or whether that station
will be held by anybody else, these pages must show. To begin my life with the
beginning of my life, I record that I was born (as I have been informed and
believe) on a Friday, at twelve o’clock at night. It was remarked that the
clock began to strike, and I began to cry, simultaneously.
```

## First try

To interface `first-lines` with Moulti, one can write `moulti-first-lines`:

```bash
#!/usr/bin/env bash

# If not done already, start a Moulti instance and have it re-execute this script:
export MOULTI_INSTANCE="moulti-first-lines"
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"

source moulti-functions.bash
# custom parsing goes here

# Instance title:
moulti set --title="First lines: $*"

# Run "first-lines" and pipe its output to moulti_process_lines():
first-lines "$@" 2>&1 | moulti_process_lines
```

Running `./moulti-first-lines dickens --limit=3` yields this:
![moulti first lines: 1st run](assets/images/first-lines-1.svg)

## Match titles

This is a pretty good start, thanks to the default value of `$MOULTI_NEW_STEP_PATTERN` matching `==== title ====`.
Although it is not strictly necessary here, it is possible to override this variable to match only that kind of titles:
```bash
MOULTI_NEW_STEP_PATTERN='^==== (.+) ====$'
```
!!! warning "Important: this is a bash regex, i.e. a [POSIX extended regex](https://en.wikibooks.org/wiki/Regular_Expressions/POSIX-Extended_Regular_Expressions)."

## Create steps

The situation can be improved by getting rid of those `=` signs in step titles. That can be achieved by overriding `moulti_make_step()`:
```bash
function moulti_make_step {
	# $2 is a suggested id for the new step.
	# $5 is the first group captured by MOULTI_NEW_STEP_PATTERN: use it as title:
	moulti step add "$2" --title="$5" --bottom-text=' ' && echo "$2"
}
```

Note that `moulti_make_step` is expected to output the id of the step it created, hence `&& echo "$2"`.

!!! info "See [Shell functions: moulti_make_step](moulti-functions.md/#moulti_make_step) for a complete list of arguments passed to `moulti_make_step()`."

## Pass content

Another issue is that title lines end up duplicated inside steps. Additionally, there are empty lines between them and actual contents.
To fix these issues, one can override `moulti_inspect_line()`.
`moulti_inspect_line()` receives a single line as first argument. It is expected to inspect it, optionally alter it and output it.
```bash
function moulti_inspect_line {
	# $1 is the line about to be passed to the current step.
	[ "${1}" ] || return # Skip empty lines
	[[ "${1}" =~ $MOULTI_NEW_STEP_PATTERN ]] && return # Do not pass title lines
	printf '%s\n' "$1" # Pass all other lines
}
```

## Result

After these changes, we get a perfect result:
![moulti first lines: 2nd run](assets/images/first-lines-2.svg)

Of course, not every output can be interfaced with Moulti by merely defining a regex and two bash functions.
But hopefully, `moulti_process_lines()` should help with most use cases.

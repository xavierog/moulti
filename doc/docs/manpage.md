# moulti manpage

Like `moulti diff`, `moulti manpage` offers two subcommands (`parse` and `run`)
that make it possible to load and read [man pages](https://en.wikipedia.org/wiki/Man_page)
in Moulti.
Specifically, it creates:

- one divider widget for the header (title and manual section)
- one step widget for each section of the man page
- one divider widget for the footer (e.g. date and version)

![man bash with Moulti](assets/images/man-bash.svg)

## How to use it?

!!! abstract "For the sake of convenience, Moulti provides `moulti-man`, a wrapper around `man`:"
    ```shell
    # Read the man page for the bash shell:
    moulti-man bash
    # Read the man page for the open() syscall:
    moulti-man 2 open
    ```

Under the hood, this wrapper essentially runs:

```shell
moulti run -- moulti manpage run -- man bash
```

i.e. `moulti run` starts a new Moulti instance then runs `moulti manpage run -- man bash`, which runs `man bash`, captures its output and turns it into a sequence of divider and step widgets.

## Encoding

By default, `moulti manpage` expects `man` to output UTF-8 text; this encoding can be
changed by setting the environment variable `MOULTI_MANPAGE_ENCODING`, e.g.
`export MOULTI_MANPAGE_ENCODING=iso-8859-1`.

## Title

By default, `moulti manpage` changes the title of the Moulti instance so that it reflects the man command (e.g. `man bash`).
Set the environment variable `MOULTI_MANPAGE_NO_TITLE` to any value to prevent that.

## Generated widgets

By default, `moulti manpage` acts like a blackbox: it reads the man page, connects to the adequate Moulti instance, adds dividers and steps, then exits.
That makes it hard (albeit not impossible) to determine the number and ids of dividers and steps added by `moulti manpage`.

If the environment variable `MOULTI_MANPAGE_VERBOSE` is set to any non-empty value, `moulti manpage` outputs the type and id of each generated widget to stdout.
Example:
```console
$ MOULTI_MANPAGE_VERBOSE=y moulti manpage run -- man true
divider manpage_766397_1
step manpage_766397_2
step manpage_766397_3
step manpage_766397_4
step manpage_766397_5
step manpage_766397_6
step manpage_766397_7
step manpage_766397_8
divider manpage_766397_9
```

That makes it possible to perform simple update/delete operations on these widgets.

## What next?

Head to [Documentation](documentation.md) for more information on various topics.

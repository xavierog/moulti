# moulti diff

`moulti diff` loads [diff](https://en.wikipedia.org/wiki/Diff) files into Moulti.
Specifically, it creates:

- a step widget to show metadata (e.g. Git commit description)
- one divider widget per altered file
- one step per chunk

!!! warning "Important: `moulti diff` only supports the [unified diff format](https://en.wikipedia.org/wiki/Diff#Unified_format)."

![Moulti diff example](assets/images/diff.svg)

## How to use it?

`moulti diff` reads diff data then acts upon an existing Moulti instance to display them:

!!! example "Terminal #1: TUI"
    ```shell
	# Launch a Moulti instance:
    moulti init
    ```

!!! example "Terminal #2: CLI"
    ```shell
    #  Example 1: load a diff file:
    moulti diff parse /path/to/example.diff
    
    # Example #2: get diff data from an external command through a pipe:
    diff -u /etc/passwd /etc/passwd- | moulti diff parse /dev/stdin
    
    #  Example #3: the same without a pipe:
    moulti diff run -- diff -u /etc/passwd /etc/passwd-
    ```

That two-terminal process can be abridged into a single command by combining `moulti diff` and `moulti run`:

```shell
# View a diff file:
moulti run -- moulti diff parse /path/to/examples.diff

# View diff data from an external command:
moulti run -- moulti diff run -- diff -u /etc/passwd /etc/passwd-
```

## Git

The ancestral wisdom from the previous section can be applied to Git:

```shell
# View the latest Git commit:
moulti run -- moulti diff run -- git -C /path/to/git/working/directory show
```

In practice, Git users can simply create a shell alias:
```bash
# Creating the alias itself:
alias moulti-git='moulti run -- moulti diff run -- git'

# Using it:
moulti-git show
moulti-git diff
moulti-git diff --cached
```

## Encoding

By default, `moulti diff` reads diff data as UTF-8 text; this encoding can be
changed by setting the environment variable `MOULTI_DIFF_ENCODING`, e.g.
`export MOULTI_DIFF_ENCODING=iso-8859-1`.

## Title

By default, `moulti diff` changes the title of the Moulti instance:

- `moulti diff parse <filename>` sets the filename as title
- `moulti diff run <command>` sets the command as title

Set the environment variable `MOULTI_DIFF_NO_TITLE` to any value to prevent that.

## Delta integration

By default, `moulti diff` tries to pass diff data to [delta](https://github.com/dandavison/delta), specifically `delta --color-only`.
This provides:

- language-specific syntax highlighting (e.g. C, Python, etc.);
- within-line difference highlighting.

If this fails (e.g. because `delta` is not available on the system), Moulti resorts to simpler colors: red for removed lines, green for added lines.

If that attempt to run `delta --color-only` somehow proves undesirable, set the environment variable `MOULTI_DIFF_NO_DELTA` to any value to prevent it.

## Generated widgets

By default, `moulti diff` acts like a blackbox: it reads diff data, connects to the adequate Moulti instance, adds dividers and steps, then exits.
That makes it hard (albeit not impossible) to determine the number and ids of dividers and steps added by `moulti diff`.

If the environment variable `MOULTI_DIFF_VERBOSE` is set to any non-empty value, `moulti diff` outputs the type and id of each generated widget to stdout.
Example:
```console
$ MOULTI_DIFF_VERBOSE=y moulti diff run -- git show
step diff_352404_1
divider diff_352404_2
step diff_352404_3
```

That makes it possible to perform simple update/delete operations on these widgets.

## What next?

Assembling a command like `moulti run -- moulti diff run -- git show` may seem complex but that complexity is quickly buried under a shell alias, function, or script.
And the exact same story happened with moulti [manpage](manpage.md).

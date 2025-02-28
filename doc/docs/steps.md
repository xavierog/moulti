# Steps

Steps are collapsible blocks meant to display arbitrary outputs.
These widgets are the bread and butter of Moulti and are best introduced by [first steps](first-steps.md), which showcases how to add, update, fill, clear and delete them.
This section expands on the matter by covering intermediate topics.

![A step](assets/images/step.svg)

## The art of filling Moulti steps

### Multiple ways to fill a step

There are multiple ways to fill a Moulti step:

- `moulti pass my_step` is the recommended way as, unlike other methods, it is not limited by the maximum amount of text you can pass through command-line arguments
- `moulti step add my_step --text=$'line1\nline2\nline3'` is suitable to fill steps as soon as they appear in Moulti
- `moulti step update my_step --text=$'line1\nline2\nline3'` is the same but applies to existing steps
- `moulti step append my_step 'line1' 'line2' 'line3'` complements `add --text` and `update --text`, which both imply to provide the output as a single argument; note: it may be necessary to `step clear` beforehand.

!!! warning "All methods above share one common limitation:"
    It is not possible to append partial lines to Moulti steps.
    Conversely, lines will not show up in Moulti until they are terminated with a line feed character (LF / `\n`).

### Input transformation

Moulti is meant to display arbitrary outputs, but it is not meant to alter or reformat them as this can usually be achieved upstream.

In particular, Moulti does not:

- number lines (use e.g. `nl -ba` or `cat -n`)
- timestamp lines (use e.g. `ts '%FT%T%z'` from the `moreutils` package)
- perform syntax highlighting (use e.g. `bat` / `batcat` or `rich`)
- wrap lines (use e.g. `fold`)
- distinguish stdout from stderr (it reads a single stream anyway; use e.g. `stderred`)
- tweak the output buffering policy of other processes:
    1. look for command-line options and environment variables that explicitly address the issue, e.g. `--line-buffered`, `PYTHONUNBUFFERED=1` or `STDBUF` (NetBSD-specific)
    2. use `LD_PRELOAD`-based tools such as `stdbuf` (from the `coreutils` package) or [cvolny/faketty](https://github.com/cvolny/faketty)
    3. use tools that allocate a [pty](https://en.wikipedia.org/wiki/Pseudoterminal), e.g. `script`, `unbuffer` (from the `expect` package) or [dtolnay/faketty](https://github.com/dtolnay/faketty):
    ```bash
    script --quiet --return --command 'your command here' /dev/null | moulti pass your_step
    ```
- trick other processes into outputting colors or emojis:
    1. look for command-line options and environment variables that explicitly address the issue, e.g. `--color=always` or `FORCE_COLOR=1`
    2. use `LD_PRELOAD`-based tools such as [cvolny/faketty](https://github.com/cvolny/faketty)
    3. use tools that allocate a pty, e.g. `script` or [dtolnay/faketty](https://github.com/dtolnay/faketty)
- strip colors from input:
    1. look for command-line options and environment variables that explicitly address the issue, e.g. `--color=never` or `NO_COLOR=1`
    2. use tools to strip ANSI escape codes, e.g. `ansi2txt` from [colorized-logs](https://github.com/kilobyte/colorized-logs)
- keep track of when your processes started, how long they ran and/or what return code they exited with... but see [Shell functions: moulti_exec](moulti-functions.md#moulti_exec) for an example of it.

!!! warning "There is, however, one notable exception:"
    Moulti expands horizontal tab characters (HT, `\t`) into a fixed number of spaces, which defaults to 8. 
    Use e.g. `MOULTI_TAB_SIZE=4` or `MOULTI_TAB_SIZE=2` to control that behavior.

### moulti pass: setting read size

As these lines are being written, Moulti's performance has room for improvement. Consequently, commands that quickly output numerous lines (e.g. `find / -ls`) will seem like they keep piping output to Moulti whereas they have exited already.

If you know in advance a command is going to output numerous lines, you can tweak the way Moulti will read them:
```shell
# The default behavior is fine when one needs to display each line as soon as possible:
ping example.org | moulti pass my_step

# This outputs 45,000+ lines, so increase read size significantly:
find /sys -ls | moulti pass my_step --read-size=131072
```

!!! info "Passing `--read-size=0` or not mentioning `--read-size` at all is equivalent to `--read-size=8192`."

### moulti pass: interactive use

The typical use of `moulti pass` is `some_command | moulti pass my_step`.
However, it is also possible to invoke `moulti pass my_step` directly.
In this case, each line you type in your terminal will end up in Moulti after you hit `Enter`,
and this is the intended behavior.

!!! danger "Beware!"
    Hitting `Ctrl+c` or `Ctrl+z` will act as expected on the moulti client process...
    BUT the Moulti instance still holds a file descriptor to your terminal's standard input
    and still reads from it.
    This essentially breaks your current terminal (with the Moulti instance eating up about half the characters you type) until you:

    1. quit the Moulti instance (just hit `q`)
    2. hit `Ctrl+d` in the affected terminal.

!!! success "Do it the right way"
    The correct way to use `moulti pass` interactively is to signal the end of file through `Ctrl+d`.
    ```console
    $ moulti pass my_step
    1st line<enter>
    2nd line<enter>
    n-th line<enter>
    last line<enter>
    <Ctrl+d>
    ```

## What next?

Moulti steps no longer have any secret for you. Head to [Questions](questions.md) to discover how Moulti can interact with end users.

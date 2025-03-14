# Threads

Under the hood, Moulti uses multiple [threads](https://en.wikipedia.org/wiki/Thread_(computing)).
This document intends to describe them.

## Main thread

Name: `moulti:main`

Moulti's main thread runs [Textual](https://textual.textualize.io/)'s
[asyncio](https://docs.python.org/3/library/asyncio.html)
[event loop](https://en.wikipedia.org/wiki/Event_loop).
Otherly put, it manages most of the TUI part.

## Textual threads

All Textual applications spawn two unnamed threads and Moulti is no exception:

- a first thread renders the user interface to stderr;
- a second thread reads events (e.g. keystrokes and mouse events) from stdin.

## Network loop

Name: `network-loop`

Once the TUI part is ready, Moulti spawns a third thread that runs the network
loop, i.e. the infinite loop that handles network events: new connections,
incoming messages, outgoing responses, etc.
This loop relies on non-blocking Unix sockets. Unlike the main thread, it does
not leverage asyncio.
Incoming messages are analyzed within this thread but actual TUI changes (e.g.
adding or removing steps) are delegated to the main thread.

## Execute command

Name: `exec-command`

When Moulti is launched through [moulti run](shell-scripting.md#moulti-run), and
once the network loop is ready, Moulti spawns a fourth thread in charge of
executing and monitoring the given command.

## moulti pass

Each `moulti pass` command results in Moulti spawning two extra threads.

### Data ingestion

Name: `|step_name`

This thread reads data from the file descriptor provided by `moulti pass`.
This file descriptor is typically a pipe, hence the `|` prefix.

### Data processing

Name: `>step_name`

This thread converts data read by the ingestion thread so they can be
added to the TUI.
The `>` prefix represents the idea that lines get written to the target step.
Unlike the `>` redirection in shell languages, this symbol does not imply creating or writing to files.

### Why do step names look weird?

Thread names cannot exceed:

- 15 characters on Linux;
- 63 characters on macOS;
- 19 characters on FreeBSD;
- 23 characters on OpenBSD;
- 15 characters on NetBSD.

Here, the first character is either `|` or `>`, leaving only:

- 14 characters on Linux;
- 62 characters on macOS;
- 18 characters on FreeBSD;
- 22 characters on OpenBSD;
- 14 characters on NetBSD.

This is why longer step names must be abridged in thread names.
This is particularly true on Linux and NetBSD where abridged names keep:

- the first 4 characters;
- the middle 5 characters;
- the last 5 characters.

!!! example "Examples"
	- `moulti pass abcdefghijklmnopqrstuvwxyz` results in threads
        `|abcdklmnovwxyz` and `>abcdklmnovwxyz`:

        ```
        abcdefghijklmnopqrstuvwxyz
        ^^^^      ^^^^^      ^^^^^
        first 4   middle 5   last 5
        ```

	- The `moulti_run_output` special step results in threads `|mouli_runutput`
	    and `>mouli_runutput`.

        ```
        moulti_run_output
        ^^^^ ^^^^^  ^^^^^
          |    |      `---- last 5
          |    `----------- middle 5
          `---------------- first 4
        ```

## Save / export contents

Name: `export-to-dir`

Through its "Save" action, Moulti is able to [export all shown contents to text
files](saving-and-loading.md/#saving-a-complete-moulti-instance) stored inside
a timestamped directory, hence the name of the thread dedicated to this operation.

## Inactive threads

Name: `thread-pool`

Threads that have finished executing are not deleted.
Instead, they remain inactive until the [thread pool](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor) decides to reuse them.

## How to inspect thread names?

The previous sections mention thread names.
But how to inpsect threads and their names in the first place?

### How to inspect thread names on Linux?

Combining `pgrep` and `pstree` (typically found in the `psmisc` package) does wonders:

```
pgrep moulti:main | xargs -n 1 pstree -napt
```

Alternatively, use `htop`: hit `H` to toggle threads.

### How to inspect thread names on FreeBSD?

```
ps Ho pid,tid,tdname,command
```

Thread names are shown in the `TDNAME` column.

### How to inspect thread names on OpenBSD?

```
ps Ho pid,tid,command
```

Thread names are shown at the end of the `COMMAND` column, between parens, after
the `/` character.

### How to inspect thread names on NetBSD?

```
top -t -c -U $(whoami)
```

Thread names are shown in the `NAME` column, which is unfortunately truncated
to 9 characters.

### How to inspect thread names on macOS?

On macOS, listing threads requires root privileges:

```
sudo htop -t -u $(whoami)
```

## How to turn off thread names?

If you suspect naming threads triggers issues (e.g. crash on some niche
operating system), you can disable it by setting the
[`MOULTI_NAME_THREADS`](environment-variables.md/#moulti_name_threads)
environment variable to `no`:

```bash
export MOULTI_NAME_THREADS=no
```

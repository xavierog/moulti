# Saving and loading

## Saving a complete Moulti instance

Click `Save` or hit `s` in Moulti to export (almost) all shown contents to text files.
Specifically, Moulti creates a new directory named after the instance (`MOULTI_INSTANCE` environment variable) and the current date and time.
This export directory is created in the directory specified by the `MOULTI_SAVE_PATH` environment variable or, alternatively, in Moulti's current working directory.

The format is straightforward:

- each step is exported as a JSON file reflecting its properties and a log file reflecting its contents;
- an extra JSON file stores instance properties.

```console
$ ls -al social-preview-2024-02-23T18-52-10.883600/
-rw-r--r-- 1 user group   61 2024-02-23 18:52:10 0-instance.properties.json
-rw-r--r-- 1 user group 1.8K 2024-02-23 18:52:10 1-title.contents.log
-rw-r--r-- 1 user group  394 2024-02-23 18:52:10 1-title.properties.json
-rw-r--r-- 1 user group  554 2024-02-23 18:52:10 2-step_ping.contents.log
-rw-r--r-- 1 user group  376 2024-02-23 18:52:10 2-step_ping.properties.json
-rw-r--r-- 1 user group   34 2024-02-23 18:52:10 3-collapsed.contents.log
-rw-r--r-- 1 user group  310 2024-02-23 18:52:10 3-collapsed.properties.json
-rw-r--r-- 1 user group 9.3K 2024-02-23 18:52:10 4-script.contents.log
-rw-r--r-- 1 user group  273 2024-02-23 18:52:10 4-script.properties.json
-rw-r--r-- 1 user group  567 2024-02-23 18:52:10 5-poll.properties.json
```

!!! warning "Limitations"

    - If a `question` or `inputquestion` widget was configured with `--password`, then its value gets exported as a series of `*` characters.
    - Moulti does not tinker with file permissions; therefore, the resulting files have default ownership and permissions; if necessary, use e.g. `umask` or `newgrp` to alter this behavior.

## Saving a single Moulti step

Hit `c` to copy the contents of the currently focused step to the clipboard. Hit `w` to do the same while preserving styles and colors (as ANSI escape codes).
Moulti emits a notification reflecting whether the copy operation succeeded.
Copy operations typically fail due to environment-related causes. The pyperclip documentation states most of the technical requirements:

- [Pyperclip documentation: Not Implemented Error](https://pyperclip.readthedocs.io/en/latest/#not-implemented-error)
- [Pyperclip on PyPI](https://pypi.org/project/pyperclip/)

If pyperclip fails, Moulti tries again using OSC 52, a special escape sequence terminals understand as "please push these data into the local clipboard".
This has the side-effect of making copy work over SSH but your terminal may or may not support OSC 52.

This behavior can be controlled through environment variable `MOULTI_CLIPBOARD_COPY`:

- `MOULTI_CLIPBOARD_COPY=pyperclip`: Moulti shall use only pyperclip;
- `MOULTI_CLIPBOARD_COPY=terminal-osc-52`: Moulti shall use only OSC 52;
- any other value: Moulti first tries pyperclip; if it fails, it tries OSC 52.

## Loading / restoring

Here is the typical way to restore a Moulti instance:
```shell
moulti run moulti load social-preview-2024-02-23T18-52-10.883600/
```

Explanations: `moulti run moulti load` is NOT a typo. The command above:

1. starts a new Moulti instance
2. `run` asks the instance to run a command; here, this command is not a script but...
3. `moulti load path/to/saved/directory`, i.e. a Moulti CLI command that reads the contents of the given directory and
   loads it into the Moulti instance.

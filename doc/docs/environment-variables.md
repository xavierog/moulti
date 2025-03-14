# Environment variables

## Environment variables you may set

### MOULTI_ALLOWED_GID

!!! warning "Abstract sockets (i.e. Linux) only!"
By default, Moulti only accepts commands from the user (uid) that launched the Moulti instance; setting this environment variable beforehand makes it accept arbitrary gids.
!!! example
    ```shell
    export MOULTI_ALLOWED_GID=141
    moulti init
    ```

### MOULTI_ALLOWED_UID

!!! warning "Abstract sockets (i.e. Linux) only!"
By default, Moulti only accepts commands from the user (uid) that launched the Moulti instance; setting this environment variable beforehand makes it accept arbitrary uids.
!!! example
    ```shell
    export MOULTI_ALLOWED_UID="1001,1002,5000,$(id -u alice),$(id -u bob)"
    moulti init
    ```

### MOULTI_ANSI

Define whether and how Moulti alters the 16 standard ANSI colors. There are three available policies:

- `verbatim`: (default value since v1.5.0) ANSI colors appear the same way inside Moulti as outside Moulti.
  However, Moulti does not try to guess the background and foreground colors of your terminal. That may affect readability.
  If needed, you can specify them using this syntax:
  ```shell
  MOULTI_ANSI=verbatim:darkbg=000000,darkfg=e6e6e6,lightbg=ffaaff,lightfg=000000
  # darkbg: background color in dark mode; default value: #0c0c0c
  # darkfg: foreground color in dark mode; default value: #d9d9d9
  # lightbg: background color in light mode; default value: #f7f7f7
  # lightfg: foreground color in light mode; default value: #000000
  ```
  The order of these attributes does not matter and you do not have to specify all of them unless actually needed.
  Therefore, `MOULTI_ANSI=verbatim` and `MOULTI_ANSI=verbatim:` work fine.

- `theme:dark=theme_name1,light=theme_name2`: define what ANSI themes to use in dark and light modes;
  specifying one theme for each mode is usually enough; if needed, specify multiple themes separated by `:` so that Moulti picks the first one it knows about.

    Built-in themes include: `DEFAULT_TERMINAL_THEME`, `MONOKAI`, `ALABASTER`

- `textual_default`: let the Textual framework handle ANSI colors (default behavior before v1.5.0).
    In practice, Textual uses built-in themes:

    - [MONOKAI](https://github.com/Textualize/textual/blob/main/src/textual/_ansi_theme.py#L22) in dark mode
    - [ALABASTER](https://github.com/Textualize/textual/blob/main/src/textual/_ansi_theme.py#L47) in light mode

    Therefore, `MOULTI_ANSI=textual_default` means the same as `MOULTI_ANSI=theme:dark=MONOKAI,light=ALABASTER`.

!!! info "About colors in `MOULTI_ANSI*`"
    - colors may be prefixed with `#`;
    - hexadecimal digits may be specified as lower or uppercase;
    - there must be exactly 6 digits.

### MOULTI_ANSI_THEME_*
Define your own ANSI themes.
!!! example
    ```shell
    # 16-color theme:
    MOULTI_ANSI_THEME_Kibble=bg=0E100A,fg=F7F7F7,ansi=4D4D4D:C70031:29CF13:D8E30E:3449D1:8400FF:0798AB:E2D1E3:5A5A5A:F01578:6CE05C:F3F79E:97A4F7:C495F0:68F2E0:FFFFFF
    # 8-color theme: specified colors are used as both regular and bright colors:
    MOULTI_ANSI_THEME_halfvga=bg=000000,fg=AAAAAA,ansi=000000:AA0000:00AA00:AA5500:0000AA:AA00AA:00AAAA:AAAAAA
    ```

Manually defining `MOULTI_ANSI_THEME_*` can be painful. So have a look at this helper script that turns [Gogh themes](https://gogh-co.github.io/Gogh/) into such variables:
```shell
tools/gogh2moulti.bash
```

!!! warning "Important"

    - Setting `MOULTI_ANSI_THEME_*` _defines_ a Moulti theme but does not _use_ it; to use it, set `MOULTI_ANSI`.
    - Theme names are case-sensitive: if you define `MOULTI_ANSI_THEME_AlphaBeta`, be sure to mention e.g. `MOULTI_ANSI=dark=AlphaBeta`, not `MOULTI_ANSI=dark=ALPHABETA`.

### MOULTI_ANSIBLE_COLLAPSE

Comma-separated list of Ansible parts that should appear collapsed, e.g. `MOULTI_ANSIBLE_COLLAPSE=prompt,recap,task`

### MOULTI_ANSIBLE_NO_TITLE

Prevent the Ansible plugin from changing the title of the Moulti instance

### MOULTI_ANSIBLE_WRITE_MODE

Define how the Ansible plugin should pass data to Moulti:

- `pass` uses `moulti pass` (default behavior)
- `append` uses `moulti step append`

### MOULTI_ASKPASS_DEFAULT_PROMPT

Prompt shown by `moulti-askpass` if none was passed on the command line; defaults to `askpass`

### MOULTI_CLIPBOARD_COPY

See [Saving a single Moulti step](saving-and-loading.md#saving-a-single-moulti-step)

### MOULTI_CUSTOM_CSS

Absolute filepath to a custom TCSS file; see [Custom classes](classes.md#custom-classes).

### MOULTI_DIFF_ENCODING

See [moulti diff: encoding](diff.md#encoding)

### MOULTI_DIFF_NO_DELTA

See [moulti diff: Delta integration](diff.md#delta-integration)

### MOULTI_DIFF_NO_TITLE

Prevent `moulti diff` from changing the title of the Moulti instance

### MOULTI_DIFF_VERBOSE

See [moulti diff: generated widgets](diff.md#generated-widgets)

### MOULTI_ENFORCE_COLLAPSIBLE

Enforce the way new collapsible widgets are displayed and prevent client tools from collapsing or expanding existing widgets:

- `collapse`: always collapse new collapsible widgets
- `expand`: always expand new collapsible widgets

### MOULTI_INSTANCE

Name of your Moulti instance; defaults to `default`; `moulti init` keeps this value untouched; since v1.30.0, `moulti run` appends its process id (e.g. `default-1234`) to prevent conflicts; taken into account by the instance to compute the default value of `MOULTI_SOCKET_PATH`.

### MOULTI_MANPAGE_ENCODING

Same as `MOULTI_DIFF_ENCODING` for `moulti manpage`

### MOULTI_MANPAGE_NO_TITLE

Prevent `moulti manpage` from changing the title of the Moulti instance

### MOULTI_MANPAGE_VERBOSE

Same as `MOULTI_DIFF_VERBOSE` for `moulti manpage`

### MOULTI_MODE

`light` to start Moulti in light mode, `dark` to start Moulti in dark mode; defaults to `dark`.

### MOULTI_NAME_THREADS

By default, Moulti assigns names to its [system threads](threads.md).
Setting `MOULTI_NAME_THREADS=no` disables this behavior.

### MOULTI_PASS_CONCURRENCY

Define how many concurrent "moulti pass" commands is acceptable; defaults to 20.

### MOULTI_QUIT_POLICY

`MOULTI_QUIT_POLICY` defines how Moulti should behave upon quitting.
Moulti considers two modes:

- `running`: when the command launched by `moulti run` is still running;
- `default`: any other situation.

Each mode is assigned a "quit policy" among these:

- `ask`: a modal dialog appears and asks end users whether they actually want to quit and whether it should kill the running script, if any;
- `quit`: simply quit -- default mode only;
- `leave`: leave the running script untouched and quit -- running mode only;
- `terminate`: terminate the script (SIGTERM) and quit -- running mode only.

Examples:
```shell
# Default policy:
export MOULTI_QUIT_POLICY='running=ask;default=quit'
# Always ask before quitting:
export MOULTI_QUIT_POLICY='running=ask;default=ask'
# Never ask, leave running processes untouched:
export MOULTI_QUIT_POLICY='running=leave;default=quit'
# Never ask, always kill:
export MOULTI_QUIT_POLICY='running=terminate;default=quit'
```

### MOULTI_RUN_NO_SUFFIX

If non-empty, instruct `moulti run` not to append its process id to the instance name; setting this environment variable is equivalent to running `moulti run --no-suffix`.

### MOULTI_RUN_OUTPUT

See [Shell scripting: standard streams](shell-scripting.md#standard-streams)

### MOULTI_SAVE_PATH

Base path under which export directories are created when saving a Moulti instance; defaults to `.` i.e. the instance's current working directory.

### MOULTI_SOCKET_PATH

Path to the network socket that Moulti should listen/connect to; taken into account by both the instance and the CLI; if not specified, Moulti defaults to a platform-specific value that reflects your username and `MOULTI_INSTANCE`; examples: `@moulti-bob-test-instance.socket`, `/run/user/1000/moulti-bob-test-instance.socket`.

### MOULTI_TAB_SIZE

When passing text to steps, tab characters are expanded into a fixed number of spaces, which defaults to 8.
Use e.g. `MOULTI_TAB_SIZE=4` or `MOULTI_TAB_SIZE=2` to control that behavior.

## Environment variables set by the Moulti instance

When a Moulti instance runs a script (e.g. `moulti run -- my_script.bash`), it sets various environment variables.
Some are meant for the script itself (their name typically starts with `MOULTI_`), some are meant so other tools integrate into Moulti (their name typically starts with that tool).

Such variables may or may not be set depending on criteria like existing environment variables or the command-line.
If you feel confused and want to investigate the matter, run `moulti run --print-env -- your command here`.
!!! example
    ```console
    $ moulti run --print-env -- true
    MOULTI_RUN=moulti
    MOULTI_SOCKET_PATH=@moulti-username-default.socket
    MOULTI_INSTANCE_PID=271828
    SSH_ASKPASS=moulti-askpass
    SSH_ASKPASS_REQUIRE=force
    SUDO_ASKPASS=/usr/local/bin/moulti-askpass
    ```

### ANSIBLE_STDOUT_CALLBACK

See [Ansible: under the hood](ansible.md#under-the-hood).

### ANSIBLE_CALLBACK_PLUGINS

See [Ansible: under the hood](ansible.md#under-the-hood).

### ANSIBLE_FORCE_COLOR

See [Ansible: under the hood](ansible.md#under-the-hood).

### MOULTI_INSTANCE_PID

Process id of the Moulti instance, in case your script needs to act upon the Moulti process itself.

### MOULTI_RUN

Its value is irrelevant but its mere presence means your script should NOT try to spawn a new Moulti instance.

### MOULTI_SOCKET_PATH

Described in the [previous section](#moulti_socket_path); the Moulti instance explicitly sets this variable to ensure your script can connect to it.

### SSH_ASKPASS

See [Shell scripting: ssh](shell-scripting.md#ssh)

### SSH_ASKPASS_REQUIRE

See [Shell scripting: ssh](shell-scripting.md#ssh)

### SUDO_ASKPASS

See [Shell scripting: sudo](shell-scripting.md#sudo)

## Other environment variables

Moulti is based on the Textual framework and is thus liable to react to all environment variables that Textual recognizes.

### COLUMNS

Use a fixed number of columns to render Moulti.

### LINES

Use a fixed number of lines to render Moulti.

### NO_COLOR

If present, convert the application to monochrome.

### TERM, COLORTERM

Used to expose terminal capabilities, starting with the ability to handle 24-bit colors.
Your mileage may vary but this frequently fixes the situation:
```shell
export TERM=xterm-256color COLORTERM=truecolor
```

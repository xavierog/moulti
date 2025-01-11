# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for its CLI (Command-Line Interface), i.e. for the `moulti` command.
Although Moulti's Python packages, modules and functions are obviously available, they do not constitute a public API yet.

## Unreleased

### Changed

- console: abridge message strings longer than 100 characters

### Fixed

- diff, load, manpage, step delete: improve pipelining so as to prevent deadlocks
- server-side networking: use non-blocking methods to deal with non-blocking sockets
- `moulti run path/to/non_executable_script` used to crash

## [1.28.0] - 2024-12-29

### Changed

- Moulti now requires Textual 1.0.x
- When searching text, the `[esc] Cancel` keybinding, which used to be shown in 1st position in the footer, is now shown in 3rd position
- `Ctrl+c` no longer exits Moulti: use `Ctrl+q` instead; `q` still works
- Input fields now support:
  - text selection through mouse or Shift+left/right; Ctrl+Shift+left/right works too
  - copy/paste through Ctrl+x/c/v

## [1.27.0] - 2024-12-28

### Changed

- Moulti now requires Textual 0.89.1

## [1.26.0] - 2024-12-27

### Changed

- Moulti now requires Textual 0.88.1

## [1.25.0] - 2024-12-26

### Added

- `MOULTI_CUSTOM_CSS` users: combined with `offset`, `position: absolute` enables various interesting hacks (e.g. multiple steps per row)
- New example script: `moulti-scoreboard.bash`

### Changed

- Moulti now requires Textual 0.87.1

## [1.24.0] - 2024-12-19

### Changed

- Moulti now requires Textual 0.86.3
- Minor color changes: input fields, buttons, progress bar, some texts in light mode.
- `MOULTI_CUSTOM_CSS` users: specify `& CollapsibleTitle { color: ...; }` to alter the default step title color; an example is available in the documentation.

## [1.23.2] - 2024-12-17

### Fixed

- Fixed a double-close issue liable to affect any file descriptor inside a given Python process after a Moulti instance exited.
- Introduced snapshot testing and continuous integration.

## [1.23.1] - 2024-11-17

### Fixed

- `moulti init` now exits with a non-zero return code when it cannot listen to clients.
- Ansible callback plugin: fix `unexpected keyword argument 'caplevel'` warning

## [1.23.0] - 2024-10-31

### Changed

- Moulti now requires Textual == 0.83.0

### Fixed

- Focus indicators: fix rendering issue induced by Textual 0.84.0

## [1.22.0] - 2024-10-27

### Changed

- Moulti now requires Textual >= 0.83.0

### Fixed

- `moulti init` used to crash with Textual >= 0.83.0:
  ```
  Screen.ALLOW_IN_MAXIMIZED_VIEW = '#header,SearchInputWidget,' + Screen.ALLOW_IN_MAXIMIZED_VIEW
                                   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  TypeError: can only concatenate str (not "NoneType") to str
  ```

## [1.21.0] - 2024-09-29

### Changed

- `moulti run` now sets `ANSIBLE_FORCE_COLOR=yes` when Ansible is detected, thus generating colors in "PLAY RECAP" and diff (`-D` command-line option)

### Fixed

- The console is now based on Textual's `Log` widget instead of `RichLog`; this prevents a
  [bug introduced in Textual 0.80.0](https://github.com/Textualize/textual/issues/5024) that affects the console when
  it becomes visible for the first time.

## [1.20.0] - 2024-09-22

### Added

- `moulti diff` lists generated widgets if the environment variable `MOULTI_DIFF_VERBOSE` is set
- `moulti manpage` lists generated widgets if the environment variable `MOULTI_MANPAGE_VERBOSE` is set
- the environment variable `MOULTI_QUIT_POLICY` defines how Moulti should behave upon quitting
- steps can now be assigned the `inactive` class, which turns them gray

### Changed

- Ansible callback plugin: steps with "skipping" and "included" lines are affected the new `inactive` class

## [1.19.0] - 2024-09-15

### Added

- `moulti diff`: [delta](https://github.com/dandavison/delta) integration
- `moulti diff`: display number of added (+) and removed (-) lines for each hunk
- `delete` commands now accept multiple ids, e.g. `moulti step delete step_1 step_2 step_3`
- Pressing `f` maximizes the currently focused step log (similar to zoom pane in tmux)

### Changed

- Moulti now requires Textual >= 0.79.0
- pipeline() now writes errors on stderr; this affects moulti `load`, `diff` and `manpage` commands.

## [1.18.1] - 2024-09-09

### Fixed

- `moulti-man` and `moulti manpage` used to ignore the last section of all manpages.

## [1.18.0] - 2024-09-08

### Added

- Text search: it is now possible to search steps (+ the title) for a given pattern (plain or regex, case-sensitive or not).
- The search widget offers an in-memory, non-persistent history.

### Changed

- The console is now shown or hidden using `z` instead of `n`.
- The console now grabs the focus, which makes it easier to scroll.

### Fixed

- Help screen: mention `ctrl+pgup` and `ctrl+pgdn`.

## [1.17.0] - 2024-08-25

### Added

- the environment variable `MOULTI_ASKPASS_DEFAULT_PROMPT` defines the prompt shown by `moulti-askpass` if none was passed on the command line
- Ansible-specific variants of `moulti-askpass`:
  - `moulti-askpass-become-password`
  - `moulti-askpass-connection-password`
  - `moulti-askpass-vault-client`

### Fixed

- Ansible callback plugin: override these `ansible-playbook` command-line options to prevent it from reading passwords through the current tty:
  - `-k`, `-ask-pass`
  - `-K`, `--ask-become-pass`
  - `-J`, `--ask-vault-pass`, `--ask-vault-password`

## [1.16.0] - 2024-08-23

### Added

- `moulti step`: add options `--auto-scroll` and `--no-auto-scroll` to control inner auto-scrolling
- `moulti pass`: significant performance improvements
- the environment variable `MOULTI_TAB_SIZE` controls the expansion of tab characters passed to steps

### Fixed

- Steps with a horizontal scrollbar had an extra line above it

## [1.15.0] - 2024-08-11

### Added

- `Ctrl+t` / `Ctrl+y` jumps to the previous/next unanswered question
- `O` / `X` collapses/expands new steps
- the environment variable `MOULTI_ENFORCE_COLLAPSIBLE` does the same as soon as Moulti starts
- `Ctrl+o` / `Ctrl+x` collapses/expands both existing and new steps
- Ansible callback plugin: the environment variable `MOULTI_ANSIBLE_COLLAPSE` specifies parts that should appear collapsed

### Changed

- Moulti now requires Textual >= 0.76.0
- Footer: the `Dark/Light` keybinding now displays either "Dark" or "Light"
- Footer: the `Lock scroll` keybinding now displays either "Lock scroll" or "Unlock scroll"

### Fixed

- `moulti question add id --button value invalid_style label` now returns an error

## [1.14.0] - 2024-08-04

### Added

- CLI command `moulti question {add,update,get-answer,delete}`
- Ansible callback plugin: support `prompt_until()` and the `pause` module
- quit dialog: buttons now feature keyboard accelerators

### Changed

- `moulti pass --read-size` now defaults to `8192`.
- `moulti run`: hitting `Ctrl+c` multiple times now navigates through the quit dialog and eventually terminates the process before exiting.

### Fixed

- `moulti run`: `MOULTI_RUN_OUTPUT=harvest moulti run -- bash -c 'echo a; sleep 3600'` would block upon selecting "Quit and leave the process running in the background".

## [1.13.0] - 2024-07-21

### Added

- help screen (`h`)
- Ansible callback plugin: handle `vars_prompt` using inputquestion widgets.

### Changed

- the quit dialog is now more keyboard-friendly

### Fixed

- ensure only one instance of the quit dialog is shown at any time.
- Ansible callback plugin: do not try to pass text to a divider.

## [1.12.1] - 2024-06-27

### Fixed

- Ansible callback plugin: handle Ansible >= 2.17

## [1.12.0] - 2024-06-23

### Added

- `moulti-man`, `moulti manpage`: load man pages into Moulti.

### Fixed

- `moulti_process_lines()`: prevent `moulti pass` processes from piling on.

## [1.11.0] - 2024-06-11

### Added

- copy to clipboard: support OSC 52 and introduce the environment variable `MOULTI_CLIPBOARD_COPY`.

### Changed

- in some situations (e.g. SSH and terminal lacking support for OSC 52), Moulti may fail to copy data to the clipboard AND fail to detect and report that failure.

### Fixed

- footer: fix key text color in light mode.

## [1.10.0] - 2024-05-26

### Changed

- performance: throttle calls to step.append(buffer).

### Fixed

- footer: restore the usual look'n feel for Textual >= 0.63.0

## [1.9.0] - 2024-05-19

### Added

- bash functions:
  - `moulti_process_lines()` helps to turn arbitrary output into Moulti steps
  - `moulti_check_requirements()` helps to ensure required commands are available
  - `stdbuf()` replaces the `stdbuf` utility on NetBSD and OpenBSD

### Changed

- bash functions:
  - pip/pipx deploys `moulti-functions.bash`
  - `moulti_iso_date()` leverages either GNU date, Perl or Python

## [1.8.1] - 2024-05-12

### Fixed

- moulti no longer systematically loads the `unidiff` module
- bash functions:
  - detect "python3.x" executables
  - no longer depend on GNU date.
  - stick to short, non-GNU mktemp command-line options

## [1.8.0] - 2024-05-05

### Added

- Ansible callback plugin: `ansible/moulti.py`
- `moulti run` sets the adequate environment variables to enable the Ansible callback plugin.
- `moulti diff`: load diff data into Moulti.

## [1.7.0] - 2024-04-28

### Added

- `moulti-askpass`, an askpass helper for Moulti
- `moulti run` automatically sets `SSH_ASKPASS`, `SSH_ASKPASS_REQUIRE` and `SUDO_ASKPASS` environment variables so as to leverage `moulti-askpass`.
- `moulti run --print-env` outputs all environment variables set by `moulti run`.
- `moulti run`: the environment variable `MOULTI_RUN_OUTPUT` provides better control on unexpected output.
- dividers: non-collapsible steps that simply display text.

## [1.6.0] - 2024-04-18

### Added

- `moulti set --step-position=bottom`
- `moulti set --step-direction=up`
- Programmatic scrolling:
  - `moulti scroll step_id offset`
  - `moulti step add --scroll-on-actvity=-1`
  - `moulti step update --scroll-on-actvity=false`
  - "Lock scroll" action to prevent programmatic scrolling

### Fixed

- The "Save" feature now exports the progress bar.

## [1.5.1] - 2024-03-31

### Fixed

- Fix a pipelining issue causing `moulti load` to emit a traceback.

## [1.5.0] - 2024-03-18

### Added

- Environment variables `MOULTI_ANSI` and `MOULTI_ANSI_THEME_*` provide full control over ANSI color themes.
- `tools/gogh2moulti.bash` converts [Gogh themes](https://gogh-co.github.io/Gogh/) into `MOULTI_ANSI_THEME_*` variables.
- Shell completion based on the argcomplete library.
- Bash functions: moulti_exec(): compute and display step duration.
- Tooltips on the Moulti header and step titles.
- Progress bar: `moulti set --progress-bar --progress-target=100 --progress=80`

### Changed

- By default, Moulti no longer alters ANSI colors; the previous behavior can be restored by setting `MOULTI_ANSI=textual_default`.
- Use non-ANSI colors in the console.
- Moulti requires textual >= 0.53.

### Fixed

- Fix "next line color" heuristic for step widgets.
- Fix detection of markup errors.
- New layout for button questions: there should no longer be any hidden/unreachable button.
- `MOULTI_CUSTOM_CSS= moulti init/run` no longer results in a traceback.

### Removed

- Textual Command Palette (never advertised and offered very little).

## [1.4.0] - 2024-03-03

### Added

- Ability to copy step/question/console contents to clipboard, with or without colors/styles.
- Focus indicators, i.e. visual hints reflecting what part of the UI currently holds focus.
- Highlighting in the console.

### Changed

- Windows: show explanatory message instead of crashing at startup.
- The key binding to toggle the console is now `n` instead of `c` (which now means "Copy").
- Make it easier to scroll around answered `buttonquestion` widgets.
- Revamp the console by making it a proper widget, as opposed to a refurbished step.

### Fixed

- Handle Rich Markup errors and return a suitable error message to clients.
- Fix `moulti pass` on FreeBSD and NetBSD.

## [1.3.0] - 2024-02-25

### Added

- TUI action "Save" that exports step properties and logs to files.
- CLI command `moulti load` that imports step properties and logs from files.
- Environment variable `MOULTI_SAVE_PATH` defines where Moulti (TUI) saves files.
- Show a modal dialog when users attempt to quit Moulti while the process launched by `moulti run` is still running.
  This dialog allows users to terminate the process or leave it running in the background.
- Environment variable `MOULTI_MODE=light` starts Moulti with dark mode disabled.
- `moulti run` now sets environment variable `MOULTI_INSTANCE_PID`.
- CLI command `moulti --version`
- Documentation: add section "moulti run: dealing with stdin, stdout, stderr"

### Changed

- Examples: improve `moulti run` commands by using `--`.
- Update documentation.

## [1.2.0] - 2024-02-18

### Added

- CLI command `moulti buttonquestion {add,update,get-answer,delete}`
- CLI command `moulti inputquestion {add,update,get-answer,delete}`

### Changed

- `moulti` (CLI) now writes error messages on stderr, not stdout.
- Examples: upgrade-system.bash now showcases buttonquestion.
- Update documentation.


## [1.1.0] - 2024-02-12

### Added

- `MOULTI_INSTANCE` environment variable.
- `MOULTI_PASS_CONCURRENCY` environment variable.
- `moulti-pass-concurrency.bash` example script.

### Changed

- `moulti wait` now sends a "ping" command.
- Update documentation.
- Examples: use `MOULTI_INSTANCE` instead of `MOULTI_SOCKET_PATH`.

### Fixed

- Improve behavior on platforms that do not support abstract Unix sockets (e.g. MacOS).
- Improve behavior on hosts with few CPUs.


## [1.0.0] - 2024-02-10

### Added

- CLI command `moulti init`
- CLI command `moulti run`
- CLI command `moulti wait --verbose --delay --max-attempts`
- CLI command `moulti set --title`
- CLI command `moulti step {add,update,delete,clear,append}`
- CLI command `moulti pass --append --read-size`
- `moulti` considers environment variables `MOULTI_SOCKET_PATH`, `MOULTI_ALLOWED_UID`, `MOULTI_ALLOWED_GID` and
  `MOULTI_CUSTOM_CSS`
- `moulti run` sets environment variables `MOULTI_RUN` and `MOULTI_SOCKET_PATH`
- Documentation
- Examples

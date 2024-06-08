# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for its CLI (Command-Line Interface), i.e. for the `moulti` command.
Although Moulti's Python packages, modules and functions are obviously available, they do not constitute a public API yet.

## Unreleased

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

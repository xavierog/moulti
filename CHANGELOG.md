# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for its CLI (Command-Line Interface), i.e. for the `moulti` command. 
Although Moulti's Python packages, modules and functions are obviously available, they do not constitute a public API yet.

## [1.3.0] - 2024-02-25

### Added

- TUI action "Save" that exports step properties and logs to files.
- CLI command `moulti load` that imports step properties and logs from files.
- Environment variable `MOULTI_SAVE_PATH` defines where Moulti (TUI) saves files.
- Show a modal dialog when users attempt to quit Moulti while the process launched by `moulti run` is still running.
  This dialog allow users to terminate the process or leave it running in the background.
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

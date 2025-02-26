# Design

This section exposes various reflections that contributed to the architectural design of Moulti.

## Components

Moulti is a CLI-driven TUI. This implies that a (relatively) long-running process takes care of maintaining and updating
the TUI while (relatively) short-running processes send instructions about what to update.
To this end, CLI processes need a protocol to communicate with the TUI instance.

In the end, Moulti is architected around 5 components:

- the CLI part (moulti.cli), used to drive the instance but also used to initialize it (`moulti init`, `moulti run`)
- the client part (moulti.client)
- the protocol (moulti.protocol)
- the server part (moulti.server)
- the TUI part (moulti.app)

## Why Unix sockets?

The protocol does not neeed to work across network hosts, it simply needs to work across processes on a single host.
At this stage, all IPC techniques remain available.

Enter another requirement: it should be possible to fill Moulti steps by piping the output of a command to the CLI,
e.g.:
```shell
some_command --with arguments 2>&1 | moulti pass step_name
```

In a naive scenario, the CLI acts like a proxy:

1. the command writes to the pipe
2. the CLI reads from the pipe
3. the CLI writes to the instance
4. the instance reads from the CLI
5. the instance updates the step

A more straightforward approach is to pass the file descriptor the CLI would read from to the instance. This way:

1. the command writes to the pipe
2. the instance reads from the file descriptor
3. the instance updates the step

This can be achieved with Unix Domain Sockets (AF_UNIX) and SCM_RIGHTS ancillary data.

## Security

### Who can connect?

Unix Domain Sockets are available on all Unix and Unix-like operating systems, and even on Windows.
However, they bring security constraints:

- on most platforms, Unix sockets are materialized by special files that appear on regular filesystems and file
  permissions determine what processes may or may not interact with the server.
- in addition to this file-based mechanism, Linux also supports abstract sockets, the entry points of which no longer
  rely upon file permissions.

In almost all cases, the CLI and TUI components run as the exact same user and should never interact with any other
user. However, it remains relevant to accept instructions from a whitelist of other users for specific use-cases.

With regular file-based Unix sockets, it is necessary to cautiously pick:

- the permissions of the socket file; by default, they are derived from the user's umask, which cannot be predicted.
- the directory that hosts the socket file:
    - /tmp is very exposed and thus risky
    - /run/user/<uid> is known to be protected and thus a perfect choice
    - directories under $HOME are typically (but not systematically) protected from other users and are therefore a
    suitable failover whenever /run/user is not available.

With abstract sockets, it is necessary to check the "credentials" of each incoming connection; here, "credentials"
simply means "uid and gid".
It is also possible to check those credentials with file-based Unix sockets but the mechanisms to do so suffer from
portability issues.

Moulti:

- defaults to abstract sockets with credentials check on Linux;
- stores file-based Unix sockets in:
  - `$XDG_RUNTIME_DIR` (if this environment variable is set)
  - `$XDG_CACHE_HOME/moulti` (if this environment variable is set)
  - `~/Library/Caches/moulti` (if `~/Library/Caches` exists)
  - `~/.cache/moulti`

Therefore, even with a particularly permissive umask value (e.g. `umask 0`), Moulti sockets should remain out of reach
of other users.

Explicitly sharing a Moulti instance with other users remains possible:

- Linux users simply need to stick with abstract sockets and set `MOULTI_ALLOWED_UID` and/or `MOULTI_ALLOWED_GID`.
- Other users need to pick a suitable `umask` and a suitable path through `MOULTI_SOCKET_PATH`.

### Write-only model

Additionally, operations feasible through the socket are essentially write-only.
Consequently, a malicious user able to establish a connection with a Moulti instance that does not belong to them could:

- send "ping" commands
- change the title displayed by the instance
- add new steps with arbitrary contents (possibly consuming large amounts of memory)
- alter or erase existing steps, but only if they can guess their names
- read answers to questions (this is the only command that may actually leak sensitive information)

... but they cannot:

- list existing steps (bruteforce attacks remain possible though)
- read properties of existing steps
- read contents of existing steps
- dump all current steps to disk (possibly filling the underlying storage)
- copy any step to the clipboard
- change appearance settings (TCSS, ANSI theme, dark/light mode)
- execute any command

### Command execution

Moulti clients being unable to execute any command is crucial: precisely
because it listens on a network socket (even a strictly local one), Moulti does
not provide any mechanism that could run a command passed through that socket.
It does offer the ability to run a single command on startup but this command
comes from command-line arguments passed to `moulti run` and thus from the
rightful TUI owner.

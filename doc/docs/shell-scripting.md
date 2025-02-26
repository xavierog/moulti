# Shell scripting

The key takeaway from the previous sections is that Moulti starts as an empty shell that is meant to be controlled and filled through the `moulti` CLI tool.
Controlling a Moulti instance by typing individual commands is occasionally useful but, most of the time, Moulti is driven by a shell script.
To this end, a new subcommand proves helpful: `moulti run`.


## moulti run

`moulti run` is essentially the same as `moulti init` but it runs a command right after the startup phase.

That command inherits [various environment variables](environment-variables.md#environment-variables-set-by-the-moulti-instance); among them:

- `MOULTI_RUN`: if this variable is set to a non-empty value, the Moulti instance is already running and there is no need to launch it;
- `MOULTI_SOCKET_PATH`: this variable ensures all subsequent `moulti` commands connect to the right Moulti instance.

!!! abstract "The one principle that powers Moulti"
    `moulti run <command>` enables a command to drive the Moulti instance by setting, adding, updating, filling, clearing and/or deleting almost anything in Moulti.

In practice, a simple Moulti-based bash script looks like this:

```bash
#!/usr/bin/env bash

# Good practice: name the Moulti instance:
export MOULTI_INSTANCE='my-first-script-with-moulti'
# If not done already, start a Moulti instance and have it re-execute this script:
[ "${MOULTI_RUN}" ] || exec moulti run -- "$0" "$@"
moulti step add step_1 --title='First step'
{
   echo "$(date --iso-8601=ns) Starting combobulating things and stuff..."
   # your stuff here
} 2>&1 | moulti pass step_1
moulti step add step_2 --title='Second step'
{
   echo "$(date --iso-8601=ns) Ensure things and stuff were properly combobulated..."
   # more stuff there
} 2>&1 | moulti pass step_2
```

In real life, it makes sense to heavily leverage shell functions, such as those available in [moulti-functions.bash](https://github.com/xavierog/moulti/examples/moulti-functions.bash).

## Standard streams

### Principle

In principle, scripts that leverage Moulti:

- should not try to `read` from stdin;
- should either refrain from writing to stdout/stderr or...
- should redirect stdout/stderr to a suitable destination.

!!! info "stdin, stdout and stderr are [standard streams](https://en.wikipedia.org/wiki/Standard_streams)."

### Application with bash

Possible implementations of those priciples, in bash:

```bash
# Discard stdout and stderr entirely:
exec > /dev/null 2>&1

# Log stdout and stderr to a custom log file:
exec > custom.log 2>&1

# Pass stdout and stderr to a dedicated Moulti step:
moulti step add main_script_output
exec > >(moulti pass main_script_output) 2>&1

# Pass stdout and stderr to a dedicated Moulti step but keep a copy in a custom log file:
moulti step add main_script_output
exec > >(tee --append custom.log | moulti pass main_script_output) 2>&1
```

### MOULTI_RUN_OUTPUT

Writing all this bash boilerplate is not exactly pleasant.
This is why in practice, by default, scripts launched through `moulti run`:

- have their standard input (stdin, file descriptor #0) redirected to `/dev/null`;
- have their standard and error outputs (stdout and stderr, file descriptors #1 and #2) piped to the `moulti_run_output` step.

The `moulti_run_output` step is special in that it is created upon reception of the first byte of output if it does not exist already.
It can be created beforehand, can be updated or cleared at any time and cannot be deleted while the script is running.

This behavior can be configured through the environment variable `MOULTI_RUN_OUTPUT`:

- `MOULTI_RUN_OUTPUT=harvest` or any other value: as described above;
- `MOULTI_RUN_OUTPUT=discard`: redirect stdout and stderr to /dev/null, thus discarding any unexpected output;
- `MOULTI_RUN_OUTPUT=ignore`: stdout and stderr are left untouched and their output is liable to degrade Moulti's visual display.

To illustrate all of this, we can run this demonstration script:

```bash
#!/usr/bin/env bash
[ "${MOULTI_RUN}" ] || exec moulti run "$0" "$@"
for i in {1..10}; do
    moulti step add $i --title "$(date '+%H:%M:%S'): step #${i}" --collapsed
    echo "$(date '+%H:%M:%S') This output is not passed to any step; where will it end?"
    sleep 1
done
```

!!! example "Result with MOULTI_RUN_OUTPUT=harvest (default behavior)"

    ![Result](assets/images/moulti-run-output-harvest.svg)

    Observations:

    - the `moulti_run_output` step was created between steps #1 and #2, because this is when the first "not passed to any step" line was issued
    - all such lines end up in the `moulti_run_output` step, even if new steps were created in the meantime

!!! example "Result with MOULTI_RUN_OUTPUT=discard"

    ![Result](assets/images/moulti-run-output-discard.svg)

    Observations: the "not passed to any step" lines are nowhere to be found: they were discarded

!!! example "Result with MOULTI_RUN_OUTPUT=ignore"

    ![Result](assets/images/moulti-run-output-ignore.svg)

    Observations: the "not passed to any step" lines are output directly to the terminal, conflicting with Moulti's rendering.

## SSH

SSH clients and SSH-based tools (e.g. Ansible) sometimes need user input, e.g. to accept a new host key or enter a passphrase/password.
By default, these interactions happen not over stdin but rather over the current TTY... resulting in a messy conflict with Moulti.

### moulti-askpass

This issue is usually addressed by configuring SSH clients so they use a separate "askpass" program for user interactions.
Moulti provides such a program: `moulti-askpass`.

Try out `moulti-askpass` on its own:

!!! example "Terminal #1: TUI"
    ```bash
    MOULTI_INSTANCE=trying-moulti-askpass moulti init
    ```

!!! example "Terminal #2: CLI"
    ```bash
    export MOULTI_INSTANCE=trying-moulti-askpass
    moulti-askpass 'Tell me a secret:'
    MOULTI_ASKPASS_DEFAULT_PROMPT='Tell me another secret' moulti-askpass
    SSH_ASKPASS_PROMPT=confirm moulti-askpass 'If you can read this, then moulti-askpass works fine'
    SSH_ASKPASS_PROMPT=none moulti-askpass 'If you can read this, then moulti-askpass works fine'
    ```

### moulti run and SSH

The OpenSSH client can be configured to use moulti-askpass by setting two environment variables:

```bash
export SSH_ASKPASS=moulti-askpass
export SSH_ASKPASS_REQUIRE=force
```

`moulti run` automatically sets these variables **IF** `SSH_ASKPASS` is not set already.

!!! success "Consequently, SSH clients and SSH-based tools should work out of the box with `moulti run`."

### Demonstration
```bash
moulti run ssh -q -p 2220 bandit0@bandit.labs.overthewire.org head -17 /etc/motd
```

!!! example "moulti-askpass asking whether to accept the SSH server's fingerprint"
    ![ssh demo 1](assets/images/moulti-ssh-1.svg)

!!! example "moulti-askpass asking the remote user's password"
    ![ssh demo 2](assets/images/moulti-ssh-2.svg)

!!! example "Moulti harvesting the SSH server's Message Of The Day"
    ![ssh demo 3](assets/images/moulti-ssh-3.svg)

## Git

Like SSH, Git may [require user input](https://git-scm.com/docs/gitcredentials#_requesting_credentials).
Fortunately, it uses `SSH_ASKPASS` to do so.

!!! success "Consequently, Git should work out of the box with `moulti run`."

If necessary, explicitly set `GIT_ASKPASS` in your scripts to bypass the `core.askPass` configuration variable:

```bash
export GIT_ASKPASS="${SSH_ASKPASS}"
```

## sudo

Like SSH, sudo may require user input.
Like SSH, sudo supports askpass programs: it requires:

- running `sudo -A` or `sudo --askpass` instead of `sudo`
- setting a single environment variable: `export SUDO_ASKPASS=$(which moulti-askpass)`

Note that `sudo` does not perform `$PATH` lookup, so `SUDO_ASKPASS` must be a path (either absolute or relative).

`moulti run` automatically sets `SUDO_ASKPASS` **IF** it is not set already **AND** `moulti-askpass` exists in `$PATH`.

!!! success "Consequently, `sudo -A` should work out of the box with `moulti run`."

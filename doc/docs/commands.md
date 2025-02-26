# Commands

## moulti

`moulti` is Moulti's main command.
Hop to [First steps](first-steps.md) if this is new to you.

See [Subcommands](subcommands.md) for a list of all `moulti` subcommands.

Language: Python

## moulti-askpass

`moulti-askpass` is a helper that prompts Moulti end users for a password then prints it to its standard output.
This makes sense when combined with [SSH](shell-scripting.md#ssh), [Git](shell-scripting.md#git), [Ansible](ansible.md) or [sudo](shell-scripting.md#sudo).

Language: Python

## moulti-askpass-become-password

Ansible-specific variant of `moulti-askpass`, meant to ask end users for a password required to "become" another user.

Language: Python

## moulti-askpass-connection-password

Ansible-specific variant of `moulti-askpass`, meant to ask end users for a password required to connect to a remote host.

Language: Python

## moulti-askpass-vault-client

Ansible-specific variant of `moulti-askpass`, meant to ask end users for a password required to access data encrypted with Ansible Vault.

Language: Python

## moulti-functions.bash

`moulti-functions.bash` is not really a command but rather a library of bash helpers for Moulti.

```console
$ moulti-functions.bash
This file is meant to be sourced in scripts that leverage Moulti:
source ~/.local/bin/moulti-functions.bash
```

Language: Bash

## moulti-man

`moulti-man` is a bash wrapper around man.

Language: Bash

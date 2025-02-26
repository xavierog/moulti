# Ansible

[Ansible](https://www.ansible.com/) is a popular Infrastructure-as-Code tool that generates a lot of output that is often hard to follow. You can wrap your invocation of `ansible-playbook` with `moulti run` to make the output more digestible.

!!! abstract "Basic usage"
    ```console
    $ moulti run ansible-playbook your-playbook.yaml
    ```

![Moulti+Ansible](assets/images/ansible-playbook.svg)

Collapse tasks for concise output that lets you lightly monitor progress:
```console
$ MOULTI_ANSIBLE_COLLAPSE=task moulti run ansible-playbook your-playbook.yaml
```

## When not calling `ansible-playbook` directly

For Moulti to behave properly, it needs to know when it is working with Ansible output.
`moulti run` tries to be smart by checking for the string `ansible` in the command name; i.e. `ansible-playbook`, which is typical.

If you have your own script that wraps and invokes `ansible-playbook`, either name it with the string `ansible` in it or set the environment variable `MOULTI_ANSIBLE=force`.

## Configuring behavior

This table reflects the main environment variables that you can set to control Moulti's integration with Ansible:

| Environment variable        | Value     | Description                                                     |
| --------------------------- | --------- | --------------------------------------------------------------- |
| `MOULTI_ANSIBLE_COLLAPSE`   | `task`    | Collapses tasks by default, for concise output                  |
| `MOULTI_ANSIBLE_NO_TITLE`   | 1         | Disables the setting of the window title to the invoked command |
| `MOULTI_ANSIBLE`            | `force`   | Forces Moulti to expect Ansible output                          |
| `MOULTI_ANSIBLE`            | `no`      | Prevents Moulti from processing Ansible output                  |

## Under the hood

Ansible uses a [plugin architecture](https://docs.ansible.com/ansible/latest/plugins/plugins.html) to enable a rich, flexible and expandable feature set.
Moulti integrates with Ansible by providing a [stdout callback plugin](https://docs.ansible.com/ansible/latest/plugins/callback.html#types-of-callback-plugins) (known to work with ansible-core 2.16, 2.17 and 2.18).
When loaded and executed by `ansible-playbook`, this plugin runs `moulti` commands that display the results of each Ansible task in a separate Moulti step.

`moulti run` lets Ansible know about this plugin by internally setting some environment variables:

- `ANSIBLE_STDOUT_CALLBACK`: id of the stdout callback plugin to use: `moulti`
- `ANSIBLE_CALLBACK_PLUGINS`: colon-separated list of paths that Ansible searches for callback plugins.
  If this environment variable is set already, moulti simply appends its own plugin path to it.
- `ANSIBLE_FORCE_COLOR=yes`: generate colors in "PLAY RECAP" and diff (`-D` command-line option)

This integration is automatically enabled when one of the following conditions is met:

- The name of the executed program (e.g. `ansible-playbook`) contains `ansible`, unless:
    - `ANSIBLE_STDOUT_CALLBACK` is already set, or
    - the environment variable `MOULTI_ANSIBLE` is set to `no` (this is useful to override moulti's heuristics
      and disable integration)
- The environment variable `MOULTI_ANSIBLE` is set to `force` (this is useful if invoking a script that wraps Ansible
  but does not contain the string `ansible` in its name)

To illustrate, here are different scenarios where we use the `--print-env` flag to check whether Ansible integration would be enabled or disabled:

1. Moulti auto-enables Ansible integration ✅
    ```console
    $ moulti run --print-env ansible-playbook your-playbook.yaml | grep ^ANSIBLE
    ANSIBLE_CALLBACK_PLUGINS=/path/to/python/package/moulti/ansible
    ANSIBLE_STDOUT_CALLBACK=moulti
    ANSIBLE_FORCE_COLOR=yes
    ```

    or
    ```console
    $ moulti run --print-env your-ansible-wrapper.sh | grep ^ANSIBLE
    ANSIBLE_CALLBACK_PLUGINS=/path/to/python/package/moulti/ansible
    ANSIBLE_STDOUT_CALLBACK=moulti
    ANSIBLE_FORCE_COLOR=yes
    ```

2. Moulti does not auto-enable Ansible integration ❌
    ```console
    $ moulti run --print-env your-script.sh | grep ^ANSIBLE
    $
    ```

3. You override Moulti's auto-enabling of Ansible integration ❌
    ```console
    $ MOULTI_ANSIBLE=no moulti run --print-env ansible-playbook your-playbook.yaml | grep ^ANSIBLE
    $
    ```

4. You force Moulti to enable Ansible integration ✅
    ```console
    $ MOULTI_ANSIBLE=force moulti run --print-env your-script.sh | grep ^ANSIBLE
    ANSIBLE_CALLBACK_PLUGINS=/path/to/python/package/moulti/ansible
    ANSIBLE_STDOUT_CALLBACK=moulti
    ANSIBLE_FORCE_COLOR=yes
    $
    ```

## What next?

Do you need to review your changes before git-committing your latest Ansible playbook? Head to [diff](diff.md) to see how Moulti can help.

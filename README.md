# MOULTI

Moulti changes the way your shell scripts (bash, zsh, etc.) display their output in your terminal.
Moulti enables you to assign the numerous lines emitted by your scripts to "steps", i.e. visual, collapsible blocks featuring their own title and color.

Here is what [upgrading a Debian system](examples/moulti-debian-upgrade.bash) looks like with Moulti:

![Moulti demo: Debian upgrade (Animated PNG)](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-demo-debian-upgrade.png?20240218)

Interested? [Run this demo in a container using docker or podman](https://hub.docker.com/r/xavierong/moulti-demo)

Not convinced yet? What if the output of your Ansible playbooks looked like this?

![Moulti: Ansible playbook output](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-ansible.png?20240505)

Moulti is a tool meant for people who write and execute shell scripts and/or Ansible playbooks.
Specifically, if you find yourself scrolling up your terminal to ensure everything went fine while your script is still running, then Moulti is made for you.

By the way, Moulti can also display man pages and unified diff files (with colors courtesy of [delta](https://github.com/dandavison/delta)):

![Moulti: man page](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-man-bash.png?20240621)

![Moulti: unified diff output](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-diff.png?20240914)

## Installation

TL;DR: `pipx install moulti; pipx ensurepath`

More details in the [Documentation](https://moulti.run/install/)

## How?

Synopsis:

1. Start a Moulti instance: `moulti init`
2. Add a step: `moulti step add step_name --title='some clever title here'`
3. Fill it: `whatever_your_script_does | moulti pass step_name`
4. Repeat #2 and #3 until your script is done.

Learn how to leverage Moulti by jumping to its [Documentation](https://moulti.run/)

## Features

As shown in the demo, Moulti enables user interactions through **questions**:

![Moulti input question](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-input-question.png?20240218)

![Moulti button question](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-button-question.png?20240218)

Moulti also features:
- text **search**, similar to `less`: [documentation](https://moulti.run/text-search/)
- ability to maximize a single step log, similar to tmux's zoom feature
- a **progress bar**: [documentation](https://moulti.run/progressbar/)
- programmatic scrolling: [documentation](https://moulti.run/scrolling/#programmatically-scrolling-through-steps)
- an askpass helper named `moulti-askpass`: [documentation](https://moulti.run/shell-scripting/#ssh)
- support for [Ansible playbooks](https://moulti.run/ansible/), [man pages](https://moulti.run/manpage/) and [unified diff](https://moulti.run/diff/)

When it comes to look and feel, Moulti can be customised:

- through `moulti set`: define whether Moulti steps flow up or down: [documentation](https://moulti.run/direction-and-position/)
- through [Textual CSS (TCSS)](https://textual.textualize.io/guide/CSS/): [documentation](https://moulti.run/classes/#custom-classes)
- through ANSI themes: [documentation](https://moulti.run/environment-variables/#moulti_ansi)

## Implementation

Moulti is written in Python and leverages [Textual](https://textual.textualize.io/), along with [Pyperclip](https://pypi.org/project/pyperclip/),
[argcomplete](https://kislyuk.github.io/argcomplete/) and [unidiff](https://github.com/matiasb/python-unidiff).

## Inspiration

Moulti remained a mere idea for a significant time (possibly years).

The idea of driving TUI elements from scripts obviously comes from tools like
[dialog](https://invisible-island.net/dialog/dialog-figures.html) and
[whiptail](https://whiptail.readthedocs.io/en/latest/index.html).

At some point, the author stumbled upon
[multiplex](https://github.com/dankilman/multiplex), which is probably the closest thing to Moulti. multiplex was deemed
unsatisfying on multiple points (including architecture) and that prompted the development of Moulti.

[procmux](https://github.com/napisani/procmux) is also similar to Moulti but did not affect its development.

## Acknowledgments

The Textual framework helped a lot, so kudos to the Textual team, and specifically to:
- [Will McGugan](https://github.com/willmcgugan) for creating it
- [Dave Pearson](https://davep.dev/) for his regular help and feedback about Textual issues

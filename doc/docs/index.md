---
title: "Moulti, CLI-driven Terminal UI displaying arbitrary outputs"
---

# Moulti: overview

## What is Moulti?

Moulti changes the way your shell scripts (bash, zsh, etc.) display their output in your terminal.
Moulti enables you to assign the numerous lines emitted by your scripts to "steps", i.e. visual, collapsible blocks featuring their own title and color.

Here is what [upgrading a Debian system](https://github.com/xavierog/moulti/blob/master/examples/moulti-debian-upgrade.bash) looks like with Moulti:

<div id="asciicast-demo-debian-upgrade" style="z-index: 1; position: relative; max-width: 100%;"></div>
<script>
function setup_demo() {
	AsciinemaPlayer.create(
		'assets/asciicasts/demo-debian-upgrade.cast',
		document.getElementById('asciicast-demo-debian-upgrade'),
		{
			autoPlay: false,
			cols: 128,
			loop: true,
			poster: 'npt:6',
			rows: 42,
		}
	);
}
try {
	player = AsciinemaPlayer; /* may throw ReferenceError */
	setup_demo();
} catch (ReferenceError) {
	/* The Asciinema JS file has not loaded yet: defer setup until after the page has loaded: */
	addEventListener('load', (event) => { setup_demo(); });
}
</script>

Interested? [Run this demo in a container using docker or podman](https://hub.docker.com/r/xavierong/moulti-demo)

Not convinced yet? What if the output of your Ansible playbooks looked like this?

![Moulti: Ansible playbook output](assets/images/ansible-setup-base-system.svg)

Moulti is a tool meant for people who write and execute shell scripts and/or Ansible playbooks.
Specifically, if you find yourself scrolling up your terminal to ensure everything went fine while your script is still running, then Moulti is made for you.

By the way, Moulti can also display man pages and unified diff files (with colors courtesy of [delta](https://github.com/dandavison/delta)):

![Moulti: man page](assets/images/man-bash.svg)

![Moulti: unified diff output](assets/images/diff.svg)

## Installation

TL;DR: `pipx install moulti; pipx ensurepath`

More details in [Installation](install.md).

## How?

Synopsis:

1. Start a Moulti instance: `moulti init`
2. Add a step: `moulti step add step_name --title='some clever title here'`
3. Fill it: `whatever_your_script_does | moulti pass step_name`
4. Repeat #2 and #3 until your script is done.

Learn how to leverage Moulti by [taking your first steps](first-steps.md).

## Features

As shown in the demo, Moulti enables user interactions through **questions**:

![Moulti input question](assets/images/inputquestion.svg)

![Moulti button question](assets/images/buttonquestion.svg)

![Moulti question](assets/images/question.svg)

Moulti also features:

- text **search**, similar to `less`: [documentation](text-search.md)
- ability to maximize a single step log, similar to tmux's zoom feature
- a **progress bar**: [documentation](progressbar.md)
- programmatic scrolling: [documentation](scrolling.md#programmatically-scrolling-through-steps)
- an askpass helper named `moulti-askpass`: [documentation](shell-scripting.md#ssh)
- support for [Ansible playbooks](ansible.md), [man pages](manpage.md) and [unified diff](diff.md)

When it comes to look and feel, Moulti can be customised:

- through `moulti set`: define whether Moulti steps flow up or down: [documentation](direction-and-position.md)
- through [Textual CSS (TCSS)](https://textual.textualize.io/guide/CSS/): [documentation](classes.md#custom-classes)
- through ANSI themes: [documentation](environment-variables.md#moulti_ansi)

## Implementation

Moulti is written in Python and leverages [Textual](https://textual.textualize.io/), along with [Pyperclip](https://pypi.org/project/pyperclip/),
[argcomplete](https://kislyuk.github.io/argcomplete/) and [unidiff](https://github.com/matiasb/python-unidiff).

## Why Moulti?

For decades, scripts and command-line tools have resorted to various techniques to make it possible to navigate copious output.
One of these techniques is to "draw" separators using ASCII characters.

!!! example "Example"
    ```console
    $ my-huge-batch.sh
    ======== PART 1 ========
    [10,000 lines of output]
    ======== PART 2 ========
    [10,000 lines of output]
    ======== PART 3 ========
    [10,000 lines of output]
    Huge batch finished, exiting with return code 0.
    ```

Implementing such separators is straightforward, and they make it easier to spot and navigate to relevant points of the output, but as mere non-interactive markers, they remain a limited tool.
TUIs (Text User Interfaces) offer much more potential, starting with the ability to fold/collapse entire sections, yet remain costly to implement compared with CLI tools.
As a CLI-driven TUI, Moulti intends to bridge that gap by bringing specialized TUI capabilities to authors of CLI tools.

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

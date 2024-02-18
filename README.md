# MOULTI

Moulti changes the way your shell scripts (bash, zsh, etc.) display their output in your terminal.
Moulti enables you to assign the numerous lines emitted by your scripts to "steps", i.e. visual, collapsible blocks featuring their own title and color.

Here is how upgrading a Debian system looks like with Moulti:
![Ok, it is almost 5 MiB, but it is an APNG, not a GIF](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-demo-debian-upgrade.png?20240218)

Moulti is a tool meant for people who write and execute shell scripts.
Specifically, if you find yourself scrolling up your terminal to ensure everything went fine while your script is still running, then Moulti is made for you.

But, wait, does that not prevent interactivity with users? Moulti may actually enhance it through **questions**:

![Moulti input question](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-input-question.png?20240218)

![Moulti button question](https://xavier.kindwolf.org/p/moulti/doc/img/moulti-button-question.png?20240218)


Learn how to leverage Moulti by jumping to its [Documentation](Documentation.md).

## Implementation

Moulti is written in Python and leverages [Textual](https://textual.textualize.io/).

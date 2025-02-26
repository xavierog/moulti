# Subcommands

The `moulti` command is the heart of Moulti.
And yet, running `moulti` without any argument displays an error message asking for at least one subcommand.
This section lists all known subcommands along with related resources.

## buttonquestion

`moulti buttonquestion` manages [buttonquestion](questions.md#buttonquestions) widgets.

## diff

`moulti diff` loads diff data into a Moulti instance.
See [diff](diff.md) for more information.

## divider

`moulti divider` manages [divider](dividers.md) widgets.

## init

`moulti init` starts a new instance of Moulti (i.e. the TUI part of Moulti).
See [First steps](first-steps.md) if this is new to you.

## inputquestion

`moulti inputquestion` manages [inputquestion](questions.md#inputquestions) widgets.

## load

`moulti load` loads saved data into a Moulti instance.
See [Saving and loading](saving-and-loading.md) for more information.

## manpage

`moulti manpage` displays Unix man pages into a Moulti instance.
See [manpage](manpage.md) for more information.

## pass

`moulti pass` passes command/script output to a Moulti instance.
See [First steps](first-steps.md) if this is new to you, and [Steps: the art of filling Moulti steps](steps.md#the-art-of-filling-moulti-steps) to master this subcommand.

## question

`moulti question` manages [question](questions.md#questions) widgets.

## run

`moulti run` starts a new instance of Moulti (i.e. the TUI part of Moulti) then runs a command that is expected to "drive" the TUI part.
See [Shell scripting: moulti run](shell-scripting.md#moulti-run) for more information.

## scroll

`moulti scroll` programmatically scrolls the TUI so as to ensure a given widget (or a part of it) is visible.
See [Scrolling](scrolling.md) for more information.

## set

`moulti set` can configure various things in a running Moulti instance:

- [header title](first-steps.md)
- [step direction and position](direction-and-position.md)
- [progress bar](progressbar.md)

## step

`moulti step` manages step widgets.
See [First steps](first-steps.md) if this is new to you, and [Steps](steps.md) for more information.

## wait

`moulti wait` waits until the Moulti instance becomes available.
Think of it as "ping for Moulti".

# Progress bar

Moulti offers an optional progress bar, which appears at the bottom of the screen, just above the footer (and above the
console if it is visible).

![Progress bar at 20%](assets/images/progressbar.svg)

Like everything else in Moulti, the progress bar is strictly CLI-driven, which means Moulti will never set, move,
update, or configure the progress bar by itself.

## How to use the progress bar?

Moulti's progress bar being entirely optional, it is hidden by default:

```shell
# Show the progress bar:
moulti set --progress-bar
# Hide the progress bar:
moulti set --no-progress-bar
```

The progress bar displays a percentage on its right side. That percentage is computed based on **progress** and
**progress-target** values. For instance, this command results in a "20%" progress bar:

```shell
moulti set --progress=1138 --progress-target=5555
```

However, by default, none of these values are set and Moulti shows an "indeterminate" progress bar until progress-target
is set.

![Progress bar in indeterminate state](assets/images/progressbar-indeterminate.svg)


It is possible to force the display of such a progress bar by setting a negative or zero progress-target:

```shell
moulti set --progress-target=0
moulti set --progress-target=-1
moulti set --progress-target=-2.718281828459045
```

When updating the progress bar, it is possible to use either absolute or relative values:

```shell
moulti set --progress 80
moulti set --progress +1
moulti set --progress +20
# Going backward is allowed:
moulti set --progress -5
```

!!! info "Refer to [moulti-progressbar.bash](https://github.com/xavierog/moulti/blob/master/examples/moulti-progressbar.bash) for a demonstration of the typical use case."

## Is it a widget?

Moulti is based on the Textual framework, and its progress bar is definitely a _Textual widget_.
However, strictly speaking, it is not a _Moulti widget_: if it were, you could add/update/delete multiple progress bars, which would appear in the scrolling area.
From a functional perspective, the distinction between _Textual_ and _Moulti_ widgets does not matter, which explains why the progress bar is documented among Moulti widgets.

## What next?

You have discovered what Moulti is and the widgets it offers but, so far, Moulti only does what you painstakingly instruct it to do.
Hop to the [Tools](tools.md) section to explore what Moulti can do for you out of the box, without you having to explicitly script it.

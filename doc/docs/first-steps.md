# First steps

## Prerequisites

This document assumes you have [installed Moulti](install.md).

## First steps with Moulti

1. Open two terminals on the same machine/host/VM/container.

    For better visual results, these terminals should ideally support 24-bit colors and advertise it to applications.
    This typically does the trick:

    !!! example "Both terminals"
        ```shell
        export TERM=xterm-256color COLORTERM=truecolor
        ```

2. In the first terminal, launch the Moulti instance, i.e. the Terminal User Interface (TUI) itself:

    !!! example "Terminal #1: TUI"
        ```shell
        moulti init
        ```
    Upon startup, Moulti is empty: it shows nothing beyond a title bar and a footer:
    !!! example "Terminal #1: TUI"
        ![step 2](assets/images/first-steps-1.svg)

3. From now on, we will use the second terminal to issue commands to the Moulti instance through the Command-Line Interface (CLI) client.
   First, make yourself at home by setting its title:

    !!! example "Terminal #2: CLI"
        ```shell
        moulti set --title='This is MY (first) Moulti instance'
        ```
   The effect should be immediate in the first terminal:

    !!! example "Terminal #1: TUI"
        ![step 3](assets/images/first-steps-2.svg)

4. Create your first Moulti **step** with step id "my_step":

    !!! example "Terminal #2: CLI"
        ```shell
        moulti step add my_step --title='My first step'
        ```

    !!! example "Terminal #1: TUI"
        ![step 4](assets/images/first-steps-3.svg)

5. Now, fill the "log" part of your step with some content:

    !!! example "Terminal #2: CLI"
        ```shell
        ip -c a | moulti pass my_step
        ```
    Again, the effect should be immediate in the first terminal:

    !!! example "Terminal #1: TUI"
        ![step 5](assets/images/first-steps-4.svg)

6. Back to the second terminal, adjust your step:

    !!! example "Terminal #2: CLI"
        ```shell
        # Applying the "success" class turns the step green:
        moulti step update my_step --classes='success'
        # Steps have optional top and bottom texts:
        moulti step update my_step --top-text='Here is the output of [red bold]ip -color address[/]:'
        ```
    !!! example "Terminal #1: TUI"
        ![step 6](assets/images/first-steps-5.svg)

7. That syntax we used to turn the command red is called "Rich markup".
    Its BBcode-like syntax is described [here](https://rich.readthedocs.io/en/stable/markup.html#syntax), the list of available colors is [there](https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors) and styles that typically work fine in a *modern* terminal emulator are: `blink` `bold` `conceal` `italic` `overline` `reverse` `strike` `underline` `underline2`.
    Try them all at once:

    !!! example "Terminal #2: CLI"
         ```shell
         moulti step update my_step --bottom-text \
             '[blink]blink[/] [bold]bold[/] [conceal]conceal[/] [italic]italic[/] [overline]overline[/] [reverse]reverse[/] [strike]strike[/] [underline]underline[/] [underline2]underline2[/] [blue]blue[/] [on yellow1]on yellow1[/] [blue on yellow1]blue on yellow1[/]'
         ```
    !!! example "Terminal #1: TUI"
        ![step 7](assets/images/first-steps-6.svg)

    !!! warning "Important: Rich markup cannot be used in the log part of a step."

8. And of course, you can add *multiple* such steps:

    !!! example "Terminal #2: CLI"
         ```shell
         for class in warning error inactive standard; do
             moulti step add "${class}_example" \
                 --classes="${class}" \
                 --title="${class^} step" \
                 --text="This is a step with class '${class}'." \
                 --bottom-text=' '
         done
         ```
    !!! example "Terminal #1: TUI"
        ![step 8](assets/images/first-steps-7.svg)

    !!! warning "Step ids (e.g. "my_step") must remain unique in a Moulti instance."

9. If necessary, you can also clear (i.e. empty) a step:

    !!! example "Terminal #2: CLI"
        ```shell
        moulti step clear warning_example
        ```
   or simply delete it:

    !!! example "Terminal #2: CLI"
        ```shell
        moulti step delete error_example
        ```
    !!! example "Terminal #1: TUI"
        ![step 9](assets/images/first-steps-8.svg)

!!! info "Refer to the output of `moulti step add --help` for more options."

## What next?

You now know how to add, update, fill, clear and delete steps.
[Steps](steps.md) are a core feature of Moulti, but they are not the only **widgets** available: you can also leverage [questions](questions.md), [dividers](dividers.md) and the [progress bar](progressbar.md).
Or you can head straight to the [Documentation section](documentation.md) and browse its various topics, starting with [shell scripting](shell-scripting.md).

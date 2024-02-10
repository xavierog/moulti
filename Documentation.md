# Moulti documentation

## Prerequisites

This document assumes:
- you have read Moulti's README file;
- you have a vague idea of what Moulti is and how it could become useful to you;
- you are comfortable with the command line on Unix and/or Unix-like operating systems.

## Technical requirements (abridged)

Moulti requires Python ≥ 3.10 and Textual ≥ 0.47.

## Installation

Moulti is available as a Python package on PYPI and can thus be installed using `pip` or, more conveniently, `pipx`:

```shell
pipx install moulti
pipx ensurepath
```

Distribution packages are of course welcome.

## First steps with Moulti

1. Open two terminals on the same machine/host/VM/container.
2. In the first terminal, launch the Moulti instance, i.e. the Terminal User Interface (TUI) itself:
   ```shell
   TERM=xterm-256color moulti init
   ```
   Upon startup, Moulti is empty: it shows nothing beyond a title bar and a footer: ![step 2](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step02.png)
3. From now on, we will use the second terminal to issue commands to the Moulti instance through the Command-Line Interface (CLI) client.
   First, make yourself at home by setting its title:
   ```shell
   moulti set --title='This is MY (first) Moulti instance'
   ```
   The effect should be immediate in the first terminal:
   ![step 3](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step03.png)
4. Create your first Moulti **step** with step id "my_step":
   ```shell
   moulti step add my_step --title='My first step'
   ```
   ![step 4](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step04.png)
5. Now, fill the "log" part of your step with some content:
   ```shell
   ip -c a | moulti pass my_step
   ```
   Again, the effect should be immediate in the first terminal:
   ![step 5](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step05.png)
6. Back to the second terminal, adjust your step:
   ```shell
   moulti step update my_step --classes='success'
   moulti step update my_step --top-text='Here is the output of [red bold]ip -color address[/]:'
   ```
   ![step 6](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step06.png)
7. That syntax we used to turn the command red is called "Rich markup"; its BBcode-like syntax is described [here](https://rich.readthedocs.io/en/stable/markup.html#syntax), the list of available colors is [there](https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors) and styles that typically work fine in a *modern* terminal emulator are: `blink` `bold` `conceal` `italic` `overline` `reverse` `strike` `underline` `underline2`.
   Try them all at once:
   ```
   moulti step update my_step --bottom-text='[blink]blink[/] [bold]bold[/] [conceal]conceal[/] [italic]italic[/] [overline]overline[/] [reverse]reverse[/] [strike]strike[/] [underline]underline[/] [underline2]underline2[/] [blue]blue[/] [on yellow1]on yellow1[/] [blue on yellow1]blue on yellow1[/]'
   ```
   ![step 7](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step07.png)
   
   Refer to the output of `moulti step add --help` for more options.
   
   Important: Rich markup cannot be used in the log part of a step.
   
8. And of course, you can add *multiple* such steps:
   ```shell
   for class in warning error standard; do
       moulti step add "${class}_example" --classes="${class}" --title="${class^} step" --text="This is a step with class '${class}'." --bottom-text=' '
   done
   ```
   ![step 8](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step08.png)
   
   Just keep this constraint in mind: step ids (e.g. "my_step") must remain unique in a Moulti instance.
9. If necessary, you can also clear (i.e. empty) a step:
   ```shell
   moulti step clear warning_example
   ```
   or simply delete it:
   ```shell
   moulti step delete error_example
   ```
   ![step 9](https://xavier.kindwolf.org/p/moulti/doc/img/quickstart-step09.png)

## Shell scripting

The key takeaway from the previous section is that Moulti starts as an empty shell that is meant to be controlled and filled through the `moulti` CLI tool.
A simple Moulti-based bash script makes use of two new commands:

- `moulti run`: same as `moulti init` but runs a command right after the startup phase
- `moulti wait`: tries connecting to the Moulti instance; think "ping for moulti"

... and looks like this:

```bash
#!/usr/bin/env bash

# Use a specific socket to prevent conflicts:
export MOULTI_SOCKET_PATH='@my-first-script-with-moulti.socket'
# If not done already, start a Moulti instance and have it re-execute this script:
[ "${MOULTI_RUN}" ] || exec moulti run "$0" "$@"
# Ensure the Moulti instance is reachable:
moulti wait
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

In practice, it makes sense to heavily leverage shell functions, such as those available in [moulti-functions.bash](examples/moulti-functions.bash).

## Python scripting

Python scripting may be achieved by importing the `moulti.protocol` module and getting some inspiration from the `moulti.cli` module.

Example 1: create and fill a new step from a string through two separate connections:
```python
from moulti.protocol import send_to_moulti
add_step_msg = {'command': 'step', 'action': 'add', 'id': 'python', 'title': 'Step created from Python', 'collapsed': False}
send_to_moulti(add_step_msg)
generated_text = '\n'.join(['Python made this: ' + chr(i)*62 for i in range(33, 127)])
set_text_msg = {'command': 'step', 'action': 'update', 'id': 'python', 'text': generated_text}
send_to_moulti(set_text_msg)
```

Example 2: create and fill a new step through a single connection:
```python
from moulti.protocol import moulti_connect, send_json_message, recv_json_message
filepath = '/etc/passwd'
with moulti_connect() as moulti_socket:
    add_step_msg = {'command': 'step', 'action': 'add', 'id': 'python', 'title': f'{filepath}:', 'collapsed': False}
    send_json_message(moulti_socket, add_step_msg)
    recv_json_message(moulti_socket)
    with open(filepath) as filedesc:
        pass_fd_msg = {'command': 'pass', 'id': 'python'}
        send_json_message(moulti_socket, pass_fd_msg, [filedesc.fileno()])
        recv_json_message(moulti_socket)
```

Warning: Moulti is a young project and currently offers no guarantee whatsoever regarding the stability and availability of Python modules and functions.

## Multiple ways to fill a step

As you probably noticed already, there are multiple ways to fill a Moulti step:
- `moulti pass my_step` is the recommended way as, unlike other methods, it is not limited by the maximum amount of text you can pass through command-line arguments
- `moulti step add my_step --text=$'line1\nline2\nline3'` is suitable to fill steps as soon as they appear in Moulti
- `moulti step update my_step --text=$'line1\nline2\nline3'` is the same but applies to existing steps
- `moulti step append my_step 'line1' 'line2' 'line3'` complements `add --text` and `update --text`, which both imply to provide the output as a single argument; note: it may be necessary to `step clear` beforehand.

All methods above share one common limitation: it is not possible to append partial lines to Moulti steps.
Conversely, lines will not show up in Moulti until they are terminated with a line feed (LF / `\n`) character.

## Moulti does not...

Per se, Moulti does not:

- number lines (use e.g. `nl -ba` or `cat -n`)
- timestamp lines (use e.g. `ts '%FT%T%z'` from the `moreutils` package)
- strip colors from input (use e.g. `ansi2txt` from [colorized-logs](https://github.com/kilobyte/colorized-logs))
- perform syntax highlighting (use e.g. `bat` / `batcat`)
- wrap lines (use e.g. `fold`)
- distinguish stdout from stderr (it reads a single stream anyway; use e.g. `stderred`)
- tweak the buffering policy of other processes (use e.g. `stdbuf` and do not forget `grep --line-buffered`)
- keep track of when your processes started, how long they ran and/or what return code they exited with

All of this can be achieved from the controlling script.

## Moulti does not... yet

Moulti prevents interactivity: there is no way to display a question and wait for an answer from the user... at least for the time being. This feature may appear in future versions, among others such as:
- ability to export logs;
- ability to copy logs to the X11 clipboard;
- `type` feature, for animation purposes.

## moulti pass: setting read size

As these lines are being written, Moulti's performance has room for improvement. Consequently, commands that quickly output numerous lines (e.g. `find / -ls`) will seem like they keep piping output to Moulti whereas they have exited already.

If you know in advance a command is going to output numerous lines, you can tweak the way Moulti will read them:
```shell
# The default behaviour is fine when one needs to display each line as soon as possible:
ping example.org | moulti pass my_step

# This outputs 45,000+ lines, so increase read size significantly:
find /sys -ls | moulti pass my_step --read-size=131072
```

On the other hand, if you absolutely want to see the very latest line output by a process, ensure `--read-size` is not set or explicitly force it to `--read-size=1`.

## moulti pass: gotchas

The typical use of `moulti pass` is `some_command | moulti pass my_step`.
However, it is also possible to invoke `moulti pass my_step` directly. In this case, each line you type in your terminal will end up in Moulti after you hit `Enter`, and this is the expected behavior.
But beware: hitting `Ctrl+c` or `Ctrl+z` will act as expected on the moulti client process... BUT the Moulti instance still holds a file descriptor to your terminal's standard input and still reads from it. This essentially breaks your current terminal (with the Moulti instance eating up about half the characters you type) until you:
1. quit the Moulti instance (just hit `q`)
2. send `Ctrl+d` in the affected terminal.

The correct way to use `moulti pass` interactively is to signal the end of file through `Ctrl+d`.
```console
$ moulti pass my_step
1st line<enter>
2nd line<enter>
n-th line<enter>
last line<enter>
<Ctrl+d>
```

## Scrolling

By default, Moulti strives to display the latest lines it received and thus keeps scrolling down as long as lines keep coming.
This constant scrolling stops as soon as you scroll up:
- using the mouse wheel (or its laptop equivalent);
- by grabbing the scrollbar handle using the mouse pointer;
- by hitting the `Up`, `PgUp` or `Home` key.

The constant scrolling resumes when you hit the `End` key.

## Environment variables

- `MOULTI_SOCKET_PATH`: taken into account by both the instance and the CLI; defaults to @moulti-*yourusername*.socket, i.e. an abstract Unix Domain Socket named after your Unix user.
- `MOULTI_ALLOWED_UID`: by default, Moulti only accepts commands from the user (uid) that launched the Moulti instance; setting this environment variable beforehand makes it accept arbitrary uids; example:
  ```shell
  export MOULTI_ALLOWED_UID="1001,1002,5000,$(id -u alice),$(id -u bob)"
  moulti init
  ```
- `MOULTI_ALLOWED_GID`: by default, Moulti only accepts commands from the user (uid) that launched the Moulti instance; setting this environment variable beforehand makes it accept arbitrary gids; example:
  ```shell
  export MOULTI_ALLOWED_GID=141
  moulti init
  ```
- `MOULTI_CUSTOM_CSS`: filepath (either absolute or relative) to a custom TCSS file; see "How to define my own step classes ?"
- `MOULTI_RUN`: do NOT define this environment variable; it is set by the Moulti instance when it runs a script, e.g. `moulti run my_script.bash`
- `TERM`: per se, Moulti does nothing with this environment variable. However, `$TERM` has a strong influence on the behavior and visual aspect of curses applications and Moulti is no exception. Your mileage may vary but, overall, it seems `TERM=xterm-256color` frequently fix things.

## How to define my own step classes ?

Out of the box, Moulti provides four step classes:
- `standard` (blue)
- `success` (green)
- `warning` (orange)
- `error` (red)

Here, "class" is a synonym for "style" or "color" and actually refers to the notion of CSS class. Moulti is based on the Textual framework, which borrows various principles from the world of web design, starting with their own variant of CSS: Textual CSS (TCSS).

Moulti embeds its TCSS inside its Python code but allows end users to redefine whatever they see fit through a TCSS file of theirs, the path of which should be passed through the `MOULTI_CUSTOM_CSS` environment variable.

The snippets below demonstrate how to leverage this mechanism to define one's step classes and change the colors of the Moulti header.

/path/to/moulti-custom.tcss:
```css
/* Define a step class named "customstate" rendered with red text on a yellow background: */
Step.customstate {
    color: red;
    background: yellow;
    & MoultiLog { scrollbar-corner-color: yellow; }
}

/* Change the colors of the Moulti header: */
#header {
    background: red;
    color: yellow;
}
```

```shell
MOULTI_CUSTOM_CSS=/path/to/moulti-custom.tcss moulti init
```

Caution: if the `MOULTI_CUSTOM_CSS` environment variable is set, the path it indicates must exist and point to a syntactically valid TCSS file or the Moulti instance will crash.

## Technical requirements (unabridged)

Moulti requires Python ≥ 3.10 because:

- Moulti leverages Textual, which [requires Python 3.8 or later](https://textual.textualize.io/getting_started/#requirements).
- Moulti uses [send_fds and recv_fds](https://docs.python.org/3/library/socket.html#socket.send_fds), which require Python ≥ 3.9.
- Tests using Python 3.9.18 almost immediately hit blocking issues, specifically:
  - steps not reacting to keyboard/mouse events ;
  - `Task got Future <Future pending> attached to a different loop` Python exception.
- Python 3.9 [isn't receiving regular bug fixes anymore](https://www.python.org/downloads/release/python-3918/).
- Moulti type hints use PEP 604 (Allow writing union types as X | Y) syntax, which requires Python ≥ 3.10.

The minimum version of Textual required to run Moulti is 0.47.
Details:
- version 0.46.0 fails with message "Error in stylesheet"
- version 0.24.0 fails with message "ImportError: Package 'textual.widgets' has no class 'Collapsible'"
- version 0.1.13 fails with message "ImportError: cannot import name 'work' from 'textual'"

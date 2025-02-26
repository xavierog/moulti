# Technical requirements

## Operating System

Moulti requires a **Unix-friendly operating system**. Specifically, it requires an operating system that implements `AF_UNIX`+`SOCK_STREAM` local network sockets.
Microsoft Windows does implement such sockets but the Python interpreter does not expose this feature to applications yet.
Progress on this matter ought to happen through [Python issue #77589](https://github.com/python/cpython/issues/77589).
Once this issue is resolved, porting Moulti to Microsoft Windows should become possible.

## Python

Moulti requires **Python ≥ 3.10** because:

- Moulti leverages Textual, which [requires Python 3.8 or later](https://textual.textualize.io/getting_started/#requirements).
- Moulti uses [send_fds and recv_fds](https://docs.python.org/3/library/socket.html#socket.send_fds), which require Python ≥ 3.9.
- Tests using Python 3.9.18 almost immediately hit blocking issues, specifically:
    - steps not reacting to keyboard/mouse events ;
    - `Task got Future <Future pending> attached to a different loop` Python exception.
- Python 3.9 [isn't receiving regular bug fixes anymore](https://www.python.org/downloads/release/python-3918/).
- Moulti type hints use PEP 604 (Allow writing union types as X | Y) syntax, which requires Python ≥ 3.10.

## Textual

[Textual](https://textual.textualize.io/) is a _Rapid Application Development_ framework for Python.
Textual enables developers to build applications featuring sophisticated user interfaces that run in the terminal.

Moulti requires **Textual 1.0.x**. 

Details:

- version 1.0 is an important milestone for Textual-based applications: 0.x means "possible breaking changes anytime" whereas 1.x means "no breaking changes until 2.0"
- version 0.89.0 is a mere milestone on the way to Textual 1.0.0
- version 0.88.0 is a mere milestone on the way to Textual 1.0.0
- version 0.87.0 introduces the `position: absolute` TCSS property
- version 0.86.0 replaces the dark vs light modes with themes; Moulti went through this breaking change on its way to Textual 1.0.0
- version 0.84.0 introduces a rendering issue that affects focus indicators
- version 0.83.0 removes the need to override `Screen.ALLOW_IN_MAXIMIZED_VIEW`
- version 0.79.0 supports maximizing widgets
- version 0.76.0 supports dynamic keybindings
- version 0.53.0 exposes ANSI themes
- version 0.47.0 was the minimum requirement before the implementation of ANSI themes
- version 0.46.0 fails with message "Error in stylesheet"
- version 0.24.0 fails with message "ImportError: Package 'textual.widgets' has no class 'Collapsible'"
- version 0.1.13 fails with message "ImportError: cannot import name 'work' from 'textual'"

# MOULTI

Moulti is a Terminal User Interface (TUI) that displays the results of any process involving multiple steps.

## Implementation

Moulti is written in Python and leverages [Textual](https://textual.textualize.io/).

## Compatible Python versions

Moulti requires Python ≥ 3.10 because:

- Moulti leverages Textual, which [requires Python 3.8 or later](https://textual.textualize.io/getting_started/#requirements).
- Moulti uses [send_fds and recv_fds](https://docs.python.org/3/library/socket.html#socket.send_fds), which require Python ≥ 3.9.
- Tests using Python 3.9.18 almost immediately hit blocking issues, specifically:
  - steps not reacting to keyboard/mouse events ;
  - `Task got Future <Future pending> attached to a different loop` Python exception.
- Python 3.9 [isn't receiving regular bug fixes anymore](https://www.python.org/downloads/release/python-3918/).
- Moulti type hints use PEP 604 (Allow writing union types as X | Y) syntax, which requires Python ≥ 3.10.

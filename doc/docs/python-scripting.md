# Python scripting

Python scripting may be achieved by importing the `moulti.client` module.

## Main functions

- `moulti_connect()` connects to a Moulti instance;
- `send_json_message()` sends a message to a Moulti instance;
- `recv_json_message()` receives a message from a Moulti instance;
- `send_to_moulti` combines all three functions above: it connects to a Moulti instance, sends a single message, waits for a response, disconnects and returns the response.

A Moulti message is simply a Python dict reflecting `moulti` command-line arguments.

## Example 1

This example creates and fills a new step from a string through two separate connections:

```python
from moulti.client import send_to_moulti

# Create a new step:
# moulti step add python --title="Step created from Python" --no-collapsed
add_step_msg = {
	'command': 'step', 'action': 'add', 'id': 'python',
	'title': 'Step created from Python', 'collapsed': False,
}
send_to_moulti(add_step_msg)

# Generate text and update the step:
text = '\n'.join(['Python made this: ' + chr(i)*62 for i in range(33, 127)])
# moulti step update python --text="${text}"
set_text_msg = {
	'command': 'step', 'action': 'update', 'id': 'python',
	'text': text,
}
send_to_moulti(set_text_msg)
```

![Result](assets/images/python-1.svg)

## Example 2

This examples creates and fills a new step through a single connection:

```python
from moulti.client import moulti_connect, recv_json_message, send_json_message

filepath = '/etc/passwd'
with moulti_connect() as moulti_socket:
	# Create a new step:
	# moulti step add python --title="${filepath}:" --no-collapsed
    add_step_msg = {
		'command': 'step', 'action': 'add', 'id': 'python',
		'title': f'{filepath}:', 'collapsed': False,
	}
    send_json_message(moulti_socket, add_step_msg)
    recv_json_message(moulti_socket)

	# Fill that new step with the contents of a regular file: 
    with open(filepath) as filedesc:
		# moulti pass python < /etc/passwd
        pass_fd_msg = {'command': 'pass', 'id': 'python'}
        send_json_message(moulti_socket, pass_fd_msg, [filedesc.fileno()])
        recv_json_message(moulti_socket)
```

![Result](assets/images/python-2.svg)

!!! warning
    Moulti is a young project and currently offers no guarantee whatsoever regarding the stability and availability of Python modules and functions.

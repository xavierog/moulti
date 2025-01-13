"""
A simple "askpass" program for Moulti, compatible with ssh, Ansible and sudo.
"""
import re
import sys
import random
from .client import Socket, moulti_connect, send
from .environ import env

class NoAnswerException(Exception):
	pass

def generate_step_id(prefix: str = '') -> str:
	return prefix + str(random.randint(10_000_000, 99_999_999))

def get_default_prompt() -> str:
	# If moulti-askpass was invoked with a suffix, turn it into a prompt:
	if sys.argv and (rem := re.search(r'moulti-askpass-(?P<suffix>[^/]+)$', sys.argv[0])):
		return rem.group('suffix').replace('-', ' ').capitalize() + '?'
	# Otherwise, check environment variables; use a dummy prompt as a last resort:
	return env('MOULTI_ASKPASS_DEFAULT_PROMPT', 'askpass')

def get_prompt() -> tuple[str, str, bool]:
	# Assume the user is prompted for a secret value:
	ask_secret = True
	# Ideally, the prompt should be provided as first command-line argument:
	prompt = sys.argv[1] if len(sys.argv) >= 2 else get_default_prompt()
	# Ansible-specific:
	if prompt == '--vault-id' and len(sys.argv) >= 3:
		vault_id = sys.argv[2]
		prompt = f'Password for vault {vault_id}?'
	else:
		# SSH-specific: askpass is also used to accept or refuse host key fingerprints:
		ask_secret = 'fingerprint' not in prompt
	# Escape '[' characters so Textual does not interpret them as Rich tags:
	prompt = prompt.replace('[', r'\[')
	# For proper alignment, use the first line as title and the rest as top-text:
	split = prompt.split('\n', 1)
	if len(split) == 1:
		split.append('')
	return split[0], split[1], ask_secret

def get_answer(socket: Socket, step_type: str, step_id: str) -> str:
	try:
		send(socket, {'command': 'scroll', 'id': step_id})
	except Exception:
		pass

	try:
		reply = send(socket, {'command': step_type, 'action': 'get-answer', 'id': step_id, 'wait': True})
	except Exception as exc:
		raise NoAnswerException() from exc

	try:
		send(socket, {'command': step_type, 'action': 'delete', 'id': step_id})
	except Exception:
		pass

	if not reply['done'] or 'answer' not in reply:
		raise NoAnswerException()

	return reply['answer']

def main() -> None:
	try:
		prefix = 'askpass_'
		main_input_id = generate_step_id(prefix)
		title, top_text, ask_secret = get_prompt()
		common = {
			'action': 'add', 'id': main_input_id, 'classes': 'askpass', 'title': title, 'top_text': top_text,
			'bottom_text': ' ', 'collapsed': False,
		}
		ssh_askpass_prompt = env('SSH_ASKPASS_PROMPT')
		ok_button = ['ok', 'success', 'OK']
		cancel_button = ['cancel', 'error', 'Cancel']

		with moulti_connect() as moulti_socket:
			if ssh_askpass_prompt == 'none':
				send(moulti_socket, {'command': 'buttonquestion', 'button': [ok_button], **common})
				get_answer(moulti_socket, 'buttonquestion', main_input_id)
			elif ssh_askpass_prompt == 'confirm':
				send(moulti_socket, {'command': 'buttonquestion', 'button': [ok_button, cancel_button], **common})
				answer = get_answer(moulti_socket, 'buttonquestion', main_input_id)
				sys.exit(int(answer == 'cancel')) # ok => exit 0, cancel => exit 1
			else:
				send(moulti_socket, {'command': 'inputquestion', 'password': ask_secret, **common})
				answer = get_answer(moulti_socket, 'inputquestion', main_input_id)
				print(answer)
		sys.exit(0)
	except NoAnswerException:
		sys.exit(1)
	except KeyboardInterrupt:
		print('')
		sys.exit(10)
	except Exception:
		sys.exit(15)

if __name__ == '__main__':
	main()

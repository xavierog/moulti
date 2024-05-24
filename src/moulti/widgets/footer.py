from textual.app import ComposeResult
from textual.widgets import Footer as TextualFooter

class Footer(TextualFooter):
	"""
	Override the (black) Footer class so it looks like the (blue) ClassicFooter.
	"""

	def compose(self) -> ComposeResult:
		"""
		Footer <  0.63.0 is rendered, not composed, so this method has no practical effect.
		Footer >= 0.63.0 is composed, and this method prepends the description
		with an extra space to closely imitate the look of the previous Footer.
		"""
		for footer_key in super().compose():
			if hasattr(footer_key, 'description'):
				footer_key.description = ' ' + footer_key.description
			yield footer_key

	DEFAULT_CSS = """
Footer {
    background: $accent;
	/* FooterKey is specific to the new Footer and thus does not affect the previous one. */
	FooterKey {
		background: $accent;
		color: $text;
		.footer-key--key {
			background: $accent-darken-2;
			color: $text;
		}
		&:hover {
			background: $accent-darken-1;
			.footer-key--key {
				background: $secondary;
				color: white;
			}
		}
		&.-disabled {
			text-style: dim;
			background: $accent;
			&:hover {
				.footer-key--key {
					background: $accent-darken-2;
				}
			}
		}
	}
}
"""

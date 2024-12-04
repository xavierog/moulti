"""
Moulti themes.
Textual < 0.86.0 used to offer two themes: textual-dark and textual-light,
along with an App.dark reactive attribute to switch between them.
Textual 0.86.0 removed App.dark, introduced more themes, and revamped
semantics, styles and colors.
That breaking change severely affected Moulti. The themes below aim to restore
and preserve Moulti's look'n feel.
"""
from textual.theme import Theme

MOULTI_THEMES = {
	'dark': Theme(
		name="moulti-dark",
		primary="#0178D4",
		secondary="#004578",
		warning="#ffa62b",
		error="#ba3c5b",
		success="#4ebf71",
		accent="#ffa62b",
		foreground="#e0e0e0", #
		background="#1e1e1e", #
		surface="#121212",    #
		panel="#24292f",      #
		boost=None,
		dark=True,
		luminosity_spread = 0.15,
		text_alpha = 0.95,
		variables={
			"footer-key-foreground": "#ffffff",
		},
	),
	'light': Theme(
		name="moulti-light",
		primary="#0178D4",
		secondary="#004578",
		warning="#ffa62b",
		error="#ba3c5b",
		success="#4ebf71",
		accent="#ffa62b",
		foreground="#0a0a0a", #
		background="#f5f5f5", #
		surface="#efefef",    #
		panel="#dce3e8",      #
		boost=None,
		dark=False,
		luminosity_spread = 0.15,
		text_alpha = 0.95,
		variables={
			"footer-key-foreground": "#ffffff",
		},
	),
}

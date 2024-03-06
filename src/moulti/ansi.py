"""
Provide everything to deal with ANSI themes in Textual applications.
"""
import re
from os import environ
from types import ModuleType
from rich import terminal_theme
from textual.app import App as TextualApp
from textual.filter import ANSIToTruecolor, LineFilter

TerminalTheme = terminal_theme.TerminalTheme
NamedTerminalTheme = tuple[str, TerminalTheme]
TerminalThemeCollection = dict[str, TerminalTheme]

COLOR_RE = r'#?(?P<color>[0-9a-f]{6})'

def textual_supports_dark_light_ansi_themes() -> bool:
	return hasattr(TextualApp, 'ansi_theme_dark') and hasattr(TextualApp, 'ansi_theme_light')

def replace_line_filter(app: TextualApp, filter_type: type[LineFilter], new_filter: LineFilter|None) -> bool:
	if not hasattr(app, '_filters'):
		return False
	app_filters = getattr(app, '_filters')
	for index, textual_filter in enumerate(app_filters):
		if isinstance(textual_filter, filter_type):
			if new_filter is None:
				del app_filters[index]
			else:
				app_filters[index] = new_filter
			break
	else:
		if new_filter is not None:
			app_filters.insert(0, new_filter)
	return True

def ansi_themes_from_module(source: ModuleType) -> TerminalThemeCollection:
	TerminalThemeClass = TerminalTheme
	themes = {}
	for name, obj in source.__dict__.items():
		if isinstance(obj, TerminalThemeClass):
			themes[name] = obj
	return themes

def ansi_themes_from_rich() -> TerminalThemeCollection:
	return ansi_themes_from_module(terminal_theme)

def ansi_themes_from_textual() -> TerminalThemeCollection:
	try:
		textual = __import__('textual._ansi_theme')
		textual_ansi_themes = textual._ansi_theme # pylint: disable=protected-access
		return ansi_themes_from_module(textual_ansi_themes)
	except Exception:
		return {}

def color_from_string(desc: str) -> tuple[int, int, int]:
	"""
	Turn a 6-hexdigit string into three integers.
	"""
	return int(desc[0:2], 16), int(desc[2:4], 16), int(desc[4:6], 16)

def ansi_theme_from_string(description: str) -> TerminalTheme|None:
	"""
	Return a TerminalTheme object based on a complete single-line description.
	Example of an 8-color theme: bg=000000,fg=ffffff,ansi=ffffff:80ffff:ff80ff:8080ff:ffff80:80ff80:ff8080:3f3f3f
	bg and fg define background and foreground colors, respectively.
	ansi must be a colon-separated list of exactly 8 or exactly 16 colors.
	Colors may optionally start with '#'.
	"""
	background, foreground, colors = None, None, []
	for part in description.split(','):
		part = part.lower()
		if rem := re.match(f'^bg={COLOR_RE}$', part):
			background = color_from_string(rem.group('color'))
		elif rem := re.match(f'^fg={COLOR_RE}$', part):
			foreground = color_from_string(rem.group('color'))
		elif part.startswith('ansi='):
			for color_part in part[5:].split(':'):
				if rem := re.match(f'^{COLOR_RE}$', color_part):
					colors.append(color_from_string(rem.group('color')))
	if background is not None and foreground is not None and len(colors) in (8, 16):
		if len(colors) == 8:
			return TerminalTheme(background, foreground, colors)
		return TerminalTheme(background, foreground, colors[:8], colors[8:])
	return None

def ansi_themes_from_environment(environment_prefix: str = '') -> TerminalThemeCollection:
	"""
	Example of supported environment variables (without prefix):
	ANSI_THEME_8COLORS=bg=000000,fg=ffffff,ansi=ffffff:80ffff:ff80ff:8080ff:ffff80:80ff80:ff8080:3f3f3f
	bg and fg define background and foreground colors, respectively.
	ansi must be a colon-separated list of 8 or 16 colors.
	Colors may optionally start with '#'.
	"""
	themes = {}
	prefix = environment_prefix + 'ANSI_THEME_'
	for env_name, env_value in environ.items():
		if env_name.startswith(prefix):
			theme_name = env_name[len(prefix):]
			theme_obj = ansi_theme_from_string(env_value)
			if theme_obj is not None:
				themes[theme_name] = theme_obj
	return themes

def all_ansi_themes(environment_prefix: str = '') -> TerminalThemeCollection:
	themes = ansi_themes_from_textual()
	for name, theme in ansi_themes_from_rich().items():
		themes[name] = theme
	for name, theme in ansi_themes_from_environment(environment_prefix).items():
		themes[name] = theme
	return themes


class AnsiThemePolicy:
	def __init__(self, dark_theme: NamedTerminalTheme|None, light_theme: NamedTerminalTheme|None) -> None:
		self.dark_theme = dark_theme
		self.light_theme = light_theme

	def apply(self, app: TextualApp) -> bool:
		if textual_supports_dark_light_ansi_themes():
			assert hasattr(app, 'ansi_theme_dark') and hasattr(app, 'ansi_theme_light')
			if self.dark_theme is not None:
				app.ansi_theme_dark = self.dark_theme[1]
			if self.light_theme is not None:
				app.ansi_theme_light = self.light_theme[1]
		else:
			theme = self.dark_theme if app.dark else self.light_theme
			if theme is not None:
				return replace_line_filter(app, ANSIToTruecolor, ANSIToTruecolor(terminal_theme=theme[1]))
		return True

	def __repr__(self) -> str:
		dark_theme = 'None' if self.dark_theme is None else self.dark_theme[0]
		light_theme = 'None' if self.light_theme is None else self.light_theme[0]
		return f'ANSI theme policy: {dark_theme=}, {light_theme=}'

	@classmethod
	def from_string(cls, themes: TerminalThemeCollection, policy: str) -> 'AnsiThemePolicy':
		"""
		Return an AnsiThemePolicy object based on a list of known themes and a policy string.
		A policy string is a comma-separated list of options:
		- dark=THEMELIST
		- light=THEMELIST
		where THEMELIST is a colon-separated list of known theme names by decreasing order of preference.
		Example: dark=MY_DARK_THEME:DEFAULT_TERMINAL_THEME,light=NIGHT_OWLISH
		"""
		def first_known(priority_list: list[str]) -> NamedTerminalTheme|None:
			for theme_name in priority_list:
				if theme_name in themes:
					return (theme_name, themes[theme_name])
			return None

		dark_theme, light_theme = None, None
		for part in policy.split(','):
			if part.startswith('dark='):
				dark_theme = first_known(part[5:].split(':'))
			elif part.startswith('light='):
				light_theme = first_known(part[6:].split(':'))
		return AnsiThemePolicy(dark_theme, light_theme)

	@classmethod
	def from_environment(cls, environment_prefix: str = '') -> 'AnsiThemePolicy':
		"""
		Return an AnsiThemePolicy object based on (optionally prefixed) environment variables ANSI and ANSI_THEME_*.
		"""
		themes = all_ansi_themes(environment_prefix)
		env_var_name = environment_prefix + 'ANSI'
		env_var_value = environ.get(env_var_name, '')
		return cls.from_string(themes, env_var_value)

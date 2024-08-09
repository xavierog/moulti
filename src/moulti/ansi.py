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
OVERRIDE_RE = r'^(?P<name>(?:dark|light)[bf]g)=' + COLOR_RE + '$'

def dump_filters(app: TextualApp) -> str:
	if not hasattr(app, '_filters'):
		return 'App._filters no longer exists'
	app_filters = getattr(app, '_filters')
	return ', '.join((type(line_filter).__name__ for line_filter in app_filters))

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
		self.overrides: dict[str, tuple[int, int, int]] = {}
		self.verbatim = False

	def apply(self, app: TextualApp) -> bool:
		if self.dark_theme is not None:
			app.ansi_theme_dark = self.dark_theme[1]
		if self.light_theme is not None:
			app.ansi_theme_light = self.light_theme[1]
		for name, color in self.overrides.items():
			theme = app.ansi_theme_dark if name.startswith('dark') else app.ansi_theme_light
			attribute = 'background_color' if name.endswith('bg') else 'foreground_color'
			setattr(theme, attribute, color)
		if self.verbatim:
			# Verbatim: remove Textual's ANSIToTruecolor filter:
			replace_line_filter(app, ANSIToTruecolor, None)
		return True

	def __repr__(self) -> str:
		dark_theme = 'None' if self.dark_theme is None else self.dark_theme[0]
		light_theme = 'None' if self.light_theme is None else self.light_theme[0]
		verbatim = self.verbatim
		overrides = self.overrides
		return f'ANSI theme policy: {dark_theme=}, {light_theme=}, {verbatim=}, {overrides=}'

	@classmethod
	def from_string(cls, themes: TerminalThemeCollection, policy: str) -> 'AnsiThemePolicy':
		"""
		Return an AnsiThemePolicy object based on a list of known themes and a policy string.
		A policy string contains a policy ("theme" or "verbatim") followed by a colon (":") followed by a comma-separated
		list of policy-specific options.
		Options for policy "theme":
		- dark=THEMELIST
		- light=THEMELIST
		where THEMELIST is a colon-separated list of known theme names by decreasing order of preference.
		Example: theme:dark=MY_DARK_THEME:DEFAULT_TERMINAL_THEME,light=NIGHT_OWLISH
		Options for policy "verbatim":
		- darkbg=COLOR
		- darkfg=COLOR
		- lightbg=COLOR
		- lightfg=COLOR
        Example: verbatim:darkbg=000000,darkfg=e6e6e6,lightbg=ffaaff,lightfg=000000
		"verbatim" is also accepted as is.
		"""
		def first_known(priority_list: list[str]) -> NamedTerminalTheme|None:
			for theme_name in priority_list:
				if theme_name in themes:
					return (theme_name, themes[theme_name])
			return None

		if policy.startswith("theme:"):
			policy = policy[6:]
			dark_theme, light_theme = None, None
			for part in policy.split(','):
				if part.startswith('dark='):
					dark_theme = first_known(part[5:].split(':'))
				elif part.startswith('light='):
					light_theme = first_known(part[6:].split(':'))
			return AnsiThemePolicy(dark_theme, light_theme)
		verbatim_policy = AnsiThemePolicy(None, None)
		verbatim_policy.verbatim = True
		if policy.startswith("verbatim:"):
			policy = policy[9:]
			for part in policy.split(','):
				if rem := re.match(OVERRIDE_RE, part):
					verbatim_policy.overrides[rem.group('name')] = color_from_string(rem.group('color'))
		return verbatim_policy

	@classmethod
	def from_environment(cls, environment_prefix: str = '') -> 'AnsiThemePolicy':
		"""
		Return an AnsiThemePolicy object based on (optionally prefixed) environment variables ANSI and ANSI_THEME_*.
		"""
		env_var_name = environment_prefix + 'ANSI'
		env_var_value = environ.get(env_var_name, '')
		themes = all_ansi_themes(environment_prefix) if env_var_value.startswith('theme:') else {}
		return cls.from_string(themes, env_var_value)

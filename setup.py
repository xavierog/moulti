#!/usr/bin/env python3

from setuptools import setup

short_description = 'Moulti is a CLI-driven Terminal User Interface (TUI) that enables you to assign the numerous '
short_description += 'lines emitted by your scripts to visual, collapsible blocks called steps.'

with open('README.md', 'r') as readme:
	long_description = readme.read()

setup(
	name='moulti',
	version='1.4.0',
	description=short_description,
	long_description=long_description,
	long_description_content_type='text/markdown',
	author='Xavier G.',
	author_email='xavier.moulti@kindwolf.org',
	url='https://github.com/xavierog/moulti',
	packages=[
		'moulti',
		'moulti.widgets',
		'moulti.widgets.abstractstep',
		'moulti.widgets.step',
		'moulti.widgets.abstractquestion',
		'moulti.widgets.buttonquestion',
		'moulti.widgets.inputquestion',
	],
	classifiers=[
		'Environment :: Console :: Curses',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX :: Linux',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Python :: 3 :: Only',
		'Topic :: System :: Logging',
		'Topic :: Utilities',
	],
	license='MIT',
	keywords=['cli', 'tui', 'curses', 'terminal', 'multiplex', 'script', 'output', 'steps', 'textual', 'collapsible'],
	package_dir={'': 'src'},
	install_requires=['textual>=0.47', 'pyperclip'],
	entry_points={
		'console_scripts': [
			'moulti = moulti.precli:main'
		]
	},
)

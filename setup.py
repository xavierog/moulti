#!/usr/bin/env python3

from setuptools import setup

short_description = 'Moulti is a Terminal User Interface (TUI) that displays the results of any process involving'
short_description += 'multiple steps.'
with open('README.md', 'r') as readme:
	long_description = readme.read()

setup(
	name='moulti',
	version='1.0.0',
	description=short_description,
	long_description=long_description,
	long_description_content_type='text/markdown',
	author='Xavier G.',
	author_email='xavier.moulti@kindwolf.org',
	url='https://github.com/xavierog/moulti',
	packages=['moulti'],
	classifiers=[
		# Implemented and tested with Python 3.11; unlikely to run with Python < 3.9 due to socket.send_fds/recv_fds
		'Environment :: Console :: Curses',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX :: Linux', # moulti was never tested outside Linux
		'Programming Language :: Python :: 3 :: Only', 
		'Topic :: System :: Logging',
		'Topic :: Utilities',
	],
	license='MIT',
	keywords=['cli', 'tui', 'curses', 'terminal', 'multiplex', 'script', 'output', 'steps'],
	package_dir={'': 'src'},
	install_requires=['textual'],
	entry_points={
		'console_scripts': [
			'moulti = moulti.cli:main'
		]
	},
)

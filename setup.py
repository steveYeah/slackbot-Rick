#!/usr/bin/env python

from setuptools import setup


setup(
    name='slackbot-rick',
    description='I\'m a Slackbot, Dumbass',
    version='0.0.1',
    license="MIT",
    author='Steve Hutchins',
    author_email='hutchinsteve@gmail.com',
    url='https://github.com/steveYeah/slackbot-rick',
    install_requires=[
        'PyGithub>=1.35',
        'slackclient>=1.0.5',
    ],
    entry_points={
        'console_scripts': [
            'slackbot-rick=slackbot-rick.cli:main',
        ],
    },
    package_dir={'slackbot-rick': 'slackbot-rick'},
)

# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='gelo',
    version='1.0.1',
    description='podcast chapter metadata gathering tool for content creators',
    url='https://github.com/s0ph0s-2/Gelo',
    author='s0ph0s-2',
    license='GPL v2',
    packages=find_packages(),
    install_requires=[
        'yapsy',
        'requests',
        'python-twitter',
        'irc',
    ],
    entry_points={
        'console_scripts': [
            "gelo = gelo.command_line:main",
            "gelo-twitter-register = gelo.plugins.tweeter:register",
        ]
    },
    zip_safe=False
)

# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='gelo',
    version='0.1',
    description='podcast chapter metadata gathering tool for content creators',
    url='https://github.com/s0ph0s-2/Gelo',
    author='s0ph0s-2',
    license='GPL',
    packages=[ 'gelo', ],
    entry_points={
        'console_scripts': [ "gelo = gelo.command_line:main" ]
    },
    zip_safe=False
)

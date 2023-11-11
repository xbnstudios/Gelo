# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name="gelo",
    version="5.0.4",
    description="podcast chapter metadata gathering tool for content creators",
    url="https://github.com/s0ph0s-2/Gelo",
    author="s0ph0s-2",
    license="GPL v2",
    packages=["gelo", "gelo.plugins"],
    package_dir={"gelo": "gelo", "gelo.plugins": "gelo/plugins"},
    package_data={"gelo": ["plugins/*.gelo-plugin"]},
    install_requires=["yapsy>=1.12", "requests", "python-twitter", "irc", "toml"],
    entry_points={
        "console_scripts": [
            "gelo = gelo.command_line:main",
            # "gelo-twitter-register = gelo.plugins.tweeter:register",
        ]
    },
    zip_safe=False,
)

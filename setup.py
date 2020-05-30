# -*- coding: utf-8 -*-
__author__ = '@buzz'

from setuptools import find_packages, setup

setup(
    name="kuchiyose",
    version="0.1",
    description="A Web Component Recognition Tool.",
    author="@buzz",
    url="",
    platforms=["all"],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    entry_points={
        'console_scripts': [
            'kuchiyose=kuchiyose.cli:main_cmd_group'
        ],
    }
)

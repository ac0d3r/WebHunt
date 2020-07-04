# -*- coding: utf-8 -*-
__author__ = '@buzz'

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="webhunt",
    version="0.1",
    description="A Web Component Recognition Tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="@buzz",
    url="https://github.com/Buzz2d0/WebHunt",
    platforms=["all"],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    install_requires=[
        'requests',
        'pysocks',
        'click',
        'beautifulsoup4',
        'html5lib',
        'pymysql',
        'pypinyin'
    ],
    entry_points={
        'console_scripts': [
            'webhunt=webhunt.cli:main_cmd_group'
        ],
    }
)

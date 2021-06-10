# Copyright 2020 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

# Core packages
import pathlib
from setuptools import setup, find_packages

# 3rd party packages

# Project packages

# The directory containing this file
here = pathlib.Path(__file__).parent

# The text of the README file
readme = (here / "docs/src/description.rst").read_text()

# This call to setup() does all the work
setup(
    name="sierra",
    version="1.0.3",
    description="Swarm robotics end-to-end experimental pipeline automation using ARGoS",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/swarm-robotics/sierra",
    author="John Harwell",
    author_email="john.r.harwell@gmail.com",
    license="GPLv3+",
    platforms=['linux', 'osx'],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
    ],
    packages=find_packages(exclude=("projects")),
    include_package_data=True,
    data_files=[('man/man1', ['docs/_build/man/sierra-cli.1'])],
    install_requires=[
        "pyyaml",
        "pandas",
        "matplotlib",
        "sympy",

        "similaritymeasures",
        "fastdtw",
        "coloredlogs",
        "singleton_decorator",
        "implements",
        "retry"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "sierra-cli=sierra.main:__main__",
        ]
    },
)

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
import os

# 3rd party packages

# Project packages

# The directory containing this file
here = pathlib.Path(__file__).parent

# The text of the README file
readme = (here / "README.md").read_text()

# Get version
ver_ns = {}
ver_path = os.path.join('sierra', 'version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), ver_ns)

# This call to setup() does all the work
setup(
    name="sierra-research",
    version=ver_ns['__version__'],
    description="Research experimental pipeline automation for multi-agent simulations and real robots",
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
        "Environment :: Console",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],

    packages=['sierra', 'sierra.core', 'sierra.plugins'],
    package_dir={"sierra": "sierra",
                 'sierra.core': 'sierra/core',
                 'sierra.plugins': 'sierra/plugins'},
    include_package_data=True,
    data_files=[('share/man/man1', ['docs/_build/man/sierra-cli.1']),
                ('share/man/man7', ['docs/_build/man/sierra-usage.7']),
                ('share/man/man7', ['docs/_build/man/sierra-platforms.7']),
                ('share/man/man7', ['docs/_build/man/sierra-examples.7']),
                ('share/man/man7', ['docs/_build/man/sierra-glossary.7']),
                ('share/man/man7', ['docs/_build/man/sierra.7'])],

    install_requires=[
        "pyyaml",
        "pandas",
        "matplotlib",
        "sympy",
        "psutil",
        "distro",
        "netifaces",

        "coloredlogs",
        "implements",
        "retry",
    ],
    extras_require={
        "devel": [
            # type checking
            'pylint',
            'pytype',

            # Deployment packages
            'mypy',
            'build',
            'twine',

            # Sphinx packages
            "sphinx",
            "docutils==0.16",
            "sphinx-rtd-theme",
            "sphinx-argparse",
            "sphinx-tabs",
            "sphinxcontrib-napoleon",
            "sphinx-last-updated-by-git"
            "autoapi",
            "graphviz"
        ]
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "sierra-cli=sierra.main:main",
        ]
    },
)

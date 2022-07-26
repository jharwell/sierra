# Copyright 2022 John Harwell, All rights reserved.
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

# 3rd party packages
import nox

# Project packages


@nox.session(python=["3.9"])
def lint(session):
    session.install('.')  # same as 'pip3 install .'
    session.install('.[devel]')  # same as 'pip3 install .[devel]'

    session.run('flake8',
                'sierra',
                '--count',
                '--select=E9,F63,F7,F82',
                '--show-source',
                '--statistics')

    session.run('flake8',
                'sierra',
                '--count',
                '--select=C901',
                '--max-complexity=10',
                '--statistics')

    session.run('pylint', 'sierra')

    session.run('xenon',
                '--max-absolute C',
                '--max-modules B',
                '--max-average A'
                '--no-assert sierra')


# venv argument needed so the apt module can be found in the nox venv
@nox.session(python=["3.9"], venv_params=['--system-site-packages'])
def static_analysis(session):
    session.install('.')  # same as 'pip3 install .'
    session.install('.[devel]')  # same as 'pip3 install .[devel]'

    session.run('pytype',
                '-d name-error,attribute-error,invalid-annotation,pyi-error',
                'sierra')


@nox.session(python=["3.9"])
def docs(session):
    session.install('.')  # same as 'pip3 install .'
    session.install('.[devel]')  # same as 'pip3 install .[devel]'

    # Check for imperative voice
    session.run('pydocstyle',
                '--select=D401',
                'sierra')

    # Check for summary line+body
    session.run('pydocstyle',
                '--select=D205',
                'sierra')

    # Check for punctuation on summary lines
    session.run('pydocstyle',
                '--select=D400',
                'sierra')


@nox.session(python=["3.9"])
def unit_tests(session):
    session.install('.')  # same as 'pip3 install .'
    session.run("pytest")

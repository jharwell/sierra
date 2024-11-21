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
import psutil

# Project packages

versions = ['3.8', '3.9', '3.10', '3.11']


@nox.session(python=versions)
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
                '--max-average A',
                '--no-assert sierra')

    session.run("ruff",
                "check",
                "sierra")


# venv argument needed so the apt module can be found in the nox venv on linux
@nox.session(python=versions)
def analyze_pytype(session):
    session.install('.')  # same as 'pip3 install .'
    session.install('.[devel]')  # same as 'pip3 install .[devel]'

    cores = psutil.cpu_count()
    session.run('pytype',
                f'-j {cores}',
                '-k',
                '-d name-error,attribute-error,pyi-error',
                'sierra',
                external=True)


# venv argument needed so the apt module can be found in the nox venv on linux
@nox.session(python=versions)
def analyze_mypy(session):
    session.install('.')  # same as 'pip3 install .'
    session.install('.[devel]')  # same as 'pip3 install .[devel]'

    session.run('mypyrun',
                '--select',
                # No syntax errors
                'syntax',

                # All names, attributes, should be defined, and no redefinitions
                'name-defined',
                'no-redef',
                # 'attr-defined',
                # 'union-attr',
                'var-annotated',

                # All functions annotated with a non-None return type should
                # return something; don't check return value if the function is
                # marked as returning None. Also check return type
                # compatability.
                'return',
                'func-returns-value',
                'return-value',

                # Types for what is compared in assert()s must match.
                'assert-type',

                # No instantiation of abstract classes
                'abstract',

                # All types are known and valid
                'has-type',
                'valid-type',
                'type-var',
                'name-match',
                'no-untype-def',
                'redundant-cast',
                'disallow-untyped-calls',
                'check-untyped-defs',
                'disallow-untyped-defs',
                'disallow-incomplete-defs'

                # List types
                'list-item',

                # Dict types
                'typeddict-item',

                # Check override compatability
                'override',
                'call-overload',

                # Function calls
                'call-arg',
                # 'arg-type',
                'no-untyped-call',
                'no-any-return',

                # Misc.
                'misc',
                'unreachable',
                'redundant-expr',
                'truthy-bool',

                '--',
                'sierra')


@nox.session(python=versions)
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


@nox.session(python=versions)
def unit_tests(session):
    session.install('.')  # same as 'pip3 install .'
    session.install('.[devel]')  # same as 'pip3 install .[devel]'

    session.run('pytest',
                '--cov')

# 2024-11-19 [JRH]: This currently is just a paper-thin wrapper around the shell
# scripts, which were implemented a long time ago. And it works. Some/all of the
# stuff in these scripts should be migrated into python, where doing things like
# loops is way easier/better/cleaner.


@nox.session(python=versions)
def core_integration(session):
    session.install('.')  # same as 'pip3 install .'

    session.run('./scripts/core-integration-tests.sh', *session.posargs)


@nox.session(python=versions)
def plugin_argos_integration(session):
    session.install('.')  # same as 'pip3 install .'

    session.run('./scripts/argos-integration-tests.sh', *session.posargs)


@nox.session(python=versions)
def plugin_ros1gazebo_integration(session):
    session.install('.')  # same as 'pip3 install .'

    session.run('./scripts/ros1gazebo-integration-tests.sh', *session.posargs)


@nox.session(python=versions)
def plugin_ros1robot_integration(session):
    session.install('.')  # same as 'pip3 install .'

    session.run('./scripts/ros1robot-integration-tests.sh', *session.posargs)

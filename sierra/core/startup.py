# Copyright 2021 John Harwell, All rights reserved.
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
"""Startup checks performed by SIERRA.

Tests for compatibility and testing for the required packages in its
environment.

"""
# Core packages
import sys
import logging
import subprocess

# 3rd party packages

# Project packages
from sierra.core import types


kOSXPackages = types.OSPackagesSpec('darwin',
                                    'OSX',
                                    pkgs={
                                        'parallel': True,
                                        'mactex': True,
                                        'xquartz': False,
                                        'pssh': False
                                    })
"""
The required/optional Homebrew packages.
"""

kDebianPackages = types.OSPackagesSpec('linux',
                                       'debian',
                                       pkgs={
                                           'parallel': True,
                                           'cm-super': True,
                                           'texlive-fonts-recommended': True,
                                           'texlive-latex-extra': True,
                                           'dvipng': True,
                                           'pssh': False,
                                           'ffmpeg': False,
                                           'xvfb': False
                                       })
"""
The required/optional .deb packages for debian-based distributions.
"""


def startup_checks(pkg_checks: bool) -> None:
    logging.debug("Performing startup checks")

    # Check python version
    if sys.version_info < (3, 8):
        raise RuntimeError("Python >= 3.8 must be used to run SIERRA!")

    # Check packages
    if sys.platform == "linux":
        if pkg_checks:
            _linux_pkg_checks()
    elif sys.platform == 'darwin':
        if pkg_checks:
            _osx_pkg_checks()
    else:
        raise RuntimeError("SIERRA only works on Linux and OSX!")


def _linux_pkg_checks() -> None:
    """Check that all the packages required by SIERRA are installed on Linux.

    """
    import distro  # will fail on OSX

    dist = distro.id()
    os_info = distro.os_release_info()

    if os_info['id_like'] in ['debian', 'ubuntu']:
        _apt_pkg_checks(dist)
    else:
        logging.warning(("Unknown Linux distro '%s' detected: skipping package "
                         "check"),
                        dist)
        logging.warning(("If SIERRA crashes it might be because you don't have "
                         "all the required packages installed"))


def _apt_pkg_checks(dist: str) -> None:
    try:
        import apt  # pytype: disable=import-error

    except ImportError:
        logging.warning(("Cannot check for required .deb packages: 'apt' "
                         "module not found. Maybe '%s' != OS python version, "
                         "or in virtualenv?"),
                        sys.version)
        return

    cache = apt.Cache()
    missing = []

    for pkg, required in kDebianPackages.pkgs.items():
        logging.trace("Checking for .deb package '%s'", pkg)  # type: ignore
        if pkg not in cache or not cache[pkg].is_installed:
            missing.append(pkg)

    if missing:
        if required:
            raise RuntimeError((f"Required .deb packages {missing} missing on "
                                f"Linux distribution '{dist}'. Install all "
                                "required packages before running SIERRA! "
                                "(Did you read the \"Getting Started\" docs?)"))

        logging.debug(("Recommended .deb packages %s missing on Linux "
                       "distribution '%s'. Some SIERRA functionality will "
                       "not be available. "),
                      dist,
                      missing)


def _osx_pkg_checks() -> None:
    """Check that all the packages required by SIERRA are installed on OSX.

    """
    missing = []

    for pkg, required in kOSXPackages.pkgs.items():
        logging.trace("Checking for homebrew package '%s'",   # type: ignore
                      pkg)
        p1 = subprocess.Popen(f'brew list | grep {pkg}',
                              shell=True,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL)
        p2 = subprocess.Popen(f'brew list --cask | grep {pkg}',
                              shell=True,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL)
        p1.wait()
        p2.wait()

        if p1.returncode != 0 and p2.returncode != 0:
            missing.append(pkg)

    if missing:
        if required:
            raise RuntimeError((f"Required brew package {missing} missing on "
                                "OSX. Install all required packages before "
                                "running SIERRA! (Did you read the \"Getting "
                                "Started\" docs?)"))

        logging.debug(("Recommended brew package %s missing on OSX. "
                       "Some SIERRA functionality will not be available."),
                      pkg)

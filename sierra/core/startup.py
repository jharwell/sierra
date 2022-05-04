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

# Core packages
import sys
import logging  # type: tp.Any
import subprocess

# 3rd party packages

# Project packages

kRequiredDebPackages = ['parallel',
                        'cm-super',
                        'texlive-fonts-recommended',
                        'texlive-latex-extra',
                        'pssh',
                        'ffmpeg',
                        'xvfb',
                        'dvipng']
"""
The .deb packages SIERRA requires in debian-based distributions.
"""

kRequiredOSXPackages = ['parallel',
                        'mactex',
                        'pssh']
"""
The Homebrew packages SIERRA requires in OSX.
"""


def startup_checks(pkg_checks: bool) -> None:
    logging.debug("Performing startup checks")

    # Check python version
    if sys.version_info < (3, 9):
        raise RuntimeError("Python >= 3.9 must be used to run SIERRA!")

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
    """Check that all the packages required by SIERRA are installed on whatever
    flavor of Linux SIERRA is running on.

    """
    import distro

    dist = distro.id()
    os_info = distro.os_release_info()

    if os_info['id_like'] in ['debian', 'ubuntu']:
        import apt
        cache = apt.Cache()
        missing = []

        for pkg in kRequiredDebPackages:
            logging.trace("Checking for .deb package '%s'", pkg)
            if pkg not in cache or not cache[pkg].is_installed:
                missing.append(pkg)

        if missing:
            raise RuntimeError((f"Required .deb packages {missing} missing on "
                                f"Linux distribution '{dist}'. Install all "
                                "required packages before running SIERRA! "
                                "(Did you read the \"Getting Started\" docs?)"))

    else:
        logging.warning(("Unknown Linux distro '%s' detected: skipping package "
                         "check"),
                        dist)
        logging.warning(("If SIERRA crashes it might be because you don't have "
                         "all the required packages installed"))


def _osx_pkg_checks() -> None:
    """Check that all the packages required by SIERRA are installed on whatever
    version of OSX SIERRA is running on.

    """
    missing = []

    for pkg in kRequiredOSXPackages:
        logging.trace("Checking for homebrew package '%s'", pkg)
        p1 = subprocess.Popen('brew list | grep {pkg}',
                              shell=True,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL)
        p2 = subprocess.Popen('brew list --cask | grep {pkg}',
                              shell=True,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL)
        p1.wait()
        p2.wait()

        if p1.returncode != 0 and p2.returncode != 0:
            missing.append(pkg)

    if missing:
        raise RuntimeError((f"Required brew package {missing} missing on OSX. "
                            "Install all required packages before running"
                            "SIERRA! (Did you read the \"Getting Started\" "
                            "docs?)"))

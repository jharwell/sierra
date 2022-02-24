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
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages

kRequiredDebianPackages = ['parallel',
                           'cm-super',
                           'texlive-fonts-recommended',
                           'texlive-latex-extra',
                           'dvipng']
"""
The .deb packages SIERRA requires in debian-based distributions.
"""


def startup_checks() -> None:
    logging.debug("Performing startup checks")

    # Check python version
    if sys.version_info < (3, 9):
        raise RuntimeError("Python >= 3.9 must be used to run SIERRA!")

    # Check OS
    if sys.platform != "linux" and sys.platform != "darwin":
        raise RuntimeError("SIERRA only works on Linux and OSX!")

    # Check linux packages
    if sys.platform == "linux":
        _linux_pkg_checks()


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
        for pkg in kRequiredDebianPackages:
            logging.trace("Checking for .deb package '%s'", pkg)
            if pkg not in cache or not cache[pkg].is_installed:
                raise RuntimeError(("Required SIERRA .deb package '{0}' "
                                    "missing on Linux distribution '{1}'. "
                                    "Install all required packages before "
                                    "running SIERRA! (Did you read the "
                                    "\"Getting Started\" docs?)"
                                    .format(pkg, dist)))

    else:
        logging.warning("Unknown distro '%s' detected: skipping package checks",
                        dist)
        logging.warning(("If SIERRA crashes it might be because you don't have "
                         "all the required packages installed"))

# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
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


OSX_PACKAGES = types.OSPackagesSpec(
    "darwin",
    "OSX",
    pkgs={"parallel": True, "mactex": False, "xquartz": False, "pssh": False},
)
"""
The required/optional Homebrew packages.
"""

DEBIAN_PACKAGES = types.OSPackagesSpec(
    "linux",
    "debian",
    pkgs={
        "parallel": True,
        "cm-super": False,
        "texlive-fonts-recommended": False,
        "texlive-latex-extra": False,
        "dvipng": False,
        "psmisc": True,
        "pssh": False,
        "ffmpeg": False,
        "xvfb": False,
        "iputils-ping": False,
    },
)
RPM_PACKAGES = types.OSPackagesSpec(
    "linux",
    "fedora",
    pkgs={
        "parallel": True,
        "cm-super": False,
        "texlive-scheme-full": False,
        "dvipng": False,
        "psmisc": True,
        "pssh": False,
        "ffmpeg": False,
        "xorg-x11-server-Xvfb": False,
        "iputils-ping": False,
    },
)
"""
The required/optional .deb packages for linux-based distributions.
"""


def startup_checks(pkg_checks: bool) -> None:
    logging.debug("Performing startup checks")

    # Check python version

    # Check packages
    if sys.platform == "linux":
        if pkg_checks:
            _linux_pkg_checks()
    elif sys.platform == "darwin":
        if pkg_checks:
            _osx_pkg_checks()
    else:
        raise RuntimeError("SIERRA only works on Linux and OSX!")


def _linux_pkg_checks() -> None:
    """Check that all the packages required by SIERRA are installed on Linux."""
    # This will fail on OSX if at global scope
    import distro  # noqa: PLC0415

    dist = distro.id()
    os_info = distro.os_release_info()
    if any(
        candidate in os_info["id"] for candidate in ["debian", "ubuntu", "linuxmint"]
    ):
        _apt_pkg_checks(dist)

    elif any(candidate in os_info["id"] for candidate in ["fedora"]):
        _rpm_pkg_checks(dist)
    else:
        logging.warning(
            "Unknown Linux distro '%s' detected: skipping package check", dist
        )
        logging.warning(
            "If SIERRA crashes it might be because you don't have "
            "all the required packages installed"
        )


def _apt_pkg_checks(dist: str) -> None:
    if sys.prefix != sys.base_prefix:
        logging.debug("Running in virtual environment")
    try:
        # This will fail on OSX if at global scope
        import apt  # pytype: disable=import-error # noqa: PLC0415

    except ImportError:
        logging.warning(
            "Failed to import apt python module: Cannot check for required .deb packages."
        )
        logging.warning(
            "This can happen when:\n"
            "- Running in a venv where the python version != system python "
            "version.\n"
            "- No packaging python module is installed at the system/user level "
            "outside the venv."
        )
        return

    cache = apt.Cache()
    missing = []

    for pkg, required in DEBIAN_PACKAGES.pkgs.items():
        logging.trace("Checking for .deb package '%s'", pkg)
        if pkg not in cache or not cache[pkg].is_installed:
            missing.append(pkg)

        if missing:
            if required:
                raise RuntimeError(
                    f"Required .deb packages {missing} missing on "
                    f"Linux distribution '{dist}'. Install all "
                    "required packages before running SIERRA! "
                    '(Did you read the "Getting Started" docs?)'
                )

            logging.debug(
                (
                    "Recommended .deb packages %s missing on Linux "
                    "distribution '%s'. Some SIERRA functionality will "
                    "not be available. "
                ),
                missing,
                dist,
            )


def _rpm_pkg_checks(dist: str) -> None:
    if sys.prefix != sys.base_prefix:
        logging.debug("Running in virtual environment")
    try:
        # This will fail on OSX if at global scope
        import rpm  # pytype: disable=import-error # noqa: PLC0415

    except ImportError:
        logging.warning(
            "Failed to import rpm python module: Cannot check for required .rpm packages."
        )
        logging.warning(
            "This can happen when:\n"
            "- Running in a venv where the python version != system python "
            "version.\n"
            "- No rpm python module is installed at the system/user level "
            "outside the venv."
        )
        return

    ts = rpm.TransactionSet()
    missing = []

    for pkg, required in RPM_PACKAGES.pkgs.items():
        logging.trace("Checking for .rpm package '%s'", pkg)
        if not ts.dbMatch("name", pkg):
            missing.append(pkg)

        if missing:
            if required:
                raise RuntimeError(
                    f"Required .rpm packages {missing} missing on "
                    f"Linux distribution '{dist}'. Install all "
                    "required packages before running SIERRA! "
                    '(Did you read the "Getting Started" docs?)'
                )

            logging.debug(
                (
                    "Recommended .rpm packages %s missing on Linux "
                    "distribution '%s'. Some SIERRA functionality will "
                    "not be available. "
                ),
                missing,
                dist,
            )


def _osx_pkg_checks() -> None:
    """Check that all the packages required by SIERRA are installed on OSX."""
    missing = []

    for pkg, required in OSX_PACKAGES.pkgs.items():
        logging.trace("Checking for homebrew package '%s'", pkg)
        p1 = subprocess.Popen(
            f"brew list | grep {pkg}",
            shell=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        p2 = subprocess.Popen(
            f"brew list --cask | grep {pkg}",
            shell=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        p1.wait()
        p2.wait()

        if p1.returncode != 0 and p2.returncode != 0:
            missing.append(pkg)
            if required:
                raise RuntimeError(
                    f"Required brew package {missing} missing on "
                    "OSX. Install all required packages before "
                    'running SIERRA! (Did you read the "Getting '
                    'Started" docs?)'
                )

            logging.debug(
                (
                    "Recommended brew package %s missing on OSX. "
                    "Some SIERRA functionality will not be available."
                ),
                pkg,
            )

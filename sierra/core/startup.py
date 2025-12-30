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
    logging.debug("Performing startup checks [venv=%s]", sys.prefix != sys.base_prefix)

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
        _do_linux_pkg_checks(dist, "deb", DEBIAN_PACKAGES, ["dpkg", "-s"])

    elif any(candidate in os_info["id"] for candidate in ["fedora"]):
        _do_linux_pkg_checks(dist, "rpm", RPM_PACKAGES, ["rpm", "-q"])
    else:
        logging.warning(
            "Unknown Linux distro '%s' detected: skipping package check", dist
        )
        logging.warning(
            "If SIERRA crashes it might be because you don't have "
            "all the required packages installed"
        )


def _do_linux_pkg_checks(
    dist: str, ext: str, packages: types.OSPackagesSpec, basecmd: list[str]
) -> None:
    for pkg, required in packages.pkgs.items():

        res = subprocess.run(
            [*basecmd, pkg], capture_output=True, text=True, check=False
        )

        logging.trace(
            "Checking for .%s package %s...",
            ext,
            pkg,
        )

        if res.returncode != 0:
            if required:
                raise RuntimeError(
                    f"Required .{ext} packages {pkg} missing on "
                    f"Linux distribution {dist}. Install all "
                    "required packages before running SIERRA! "
                    '(Did you read the "Getting Started" docs?)'
                )

            logging.debug(
                "Recommended .%s packages %s missing on Linux distro %s. Some SIERRA functionality will not be available. ",
                ext,
                pkg,
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

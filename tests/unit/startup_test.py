#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for ``sierra.core.startup``.

``sys.platform`` and ``subprocess.run`` are monkeypatched so the
required-vs-optional and per-OS branches are exercised deterministically.

"""

# Core packages
import subprocess

# 3rd party packages
import pytest

# Project packages
from sierra.core import startup
import sierra.core.logging as slog


@pytest.fixture(autouse=True, scope="module")
def _init_trace_logging():
    # Installs the TRACE level so logging.trace(...) exists in the checks.
    slog.initialize("INFO")


class _Result:
    def __init__(self, returncode):
        self.returncode = returncode


# --- startup_checks OS dispatch ---------------------------------------------
class TestStartupChecksDispatch:
    def test_unsupported_platform_raises(self, monkeypatch):
        monkeypatch.setattr(startup.sys, "platform", "win32")
        with pytest.raises(RuntimeError):
            startup.startup_checks(pkg_checks=True)

    def test_linux_dispatches_to_linux_checks(self, monkeypatch):
        monkeypatch.setattr(startup.sys, "platform", "linux")
        called = {}
        monkeypatch.setattr(
            startup, "_linux_pkg_checks", lambda: called.setdefault("linux", True)
        )
        startup.startup_checks(pkg_checks=True)
        assert called.get("linux") is True

    def test_darwin_dispatches_to_osx_checks(self, monkeypatch):
        monkeypatch.setattr(startup.sys, "platform", "darwin")
        called = {}
        monkeypatch.setattr(
            startup, "_osx_pkg_checks", lambda: called.setdefault("osx", True)
        )
        startup.startup_checks(pkg_checks=True)
        assert called.get("osx") is True

    def test_pkg_checks_false_skips_checks(self, monkeypatch):
        monkeypatch.setattr(startup.sys, "platform", "linux")
        called = {}
        monkeypatch.setattr(
            startup, "_linux_pkg_checks", lambda: called.setdefault("linux", True)
        )
        startup.startup_checks(pkg_checks=False)
        assert "linux" not in called


# --- _do_linux_pkg_checks required/optional handling ------------------------
class TestLinuxPkgChecks:
    def test_all_present_no_raise(self, monkeypatch):
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(0))
        # Should complete without raising.
        startup._do_linux_pkg_checks(
            "ubuntu", "deb", startup.DEBIAN_PACKAGES, ["dpkg", "-s"]
        )

    def test_required_missing_raises(self, monkeypatch):
        # 'parallel' is required=True in DEBIAN_PACKAGES; simulate it missing.
        def fake_run(cmd, *a, **k):
            pkg = cmd[-1]
            return _Result(1 if pkg == "parallel" else 0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        with pytest.raises(RuntimeError):
            startup._do_linux_pkg_checks(
                "ubuntu", "deb", startup.DEBIAN_PACKAGES, ["dpkg", "-s"]
            )

    def test_optional_missing_does_not_raise(self, monkeypatch):
        # 'dvipng' is optional (required=False); missing -> debug log, no raise.
        def fake_run(cmd, *a, **k):
            pkg = cmd[-1]
            return _Result(1 if pkg == "dvipng" else 0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        startup._do_linux_pkg_checks(
            "ubuntu", "deb", startup.DEBIAN_PACKAGES, ["dpkg", "-s"]
        )


# --- _linux_pkg_checks distro routing ---------------------------------------
class TestLinuxDistroRouting:
    def test_debian_family_routed_to_deb(self, monkeypatch):
        import distro

        monkeypatch.setattr(distro, "id", lambda: "ubuntu")
        monkeypatch.setattr(distro, "os_release_info", lambda: {"id": "ubuntu debian"})
        seen = {}

        def fake_do(dist, ext, packages, basecmd):
            seen.update(ext=ext, basecmd=basecmd)

        monkeypatch.setattr(startup, "_do_linux_pkg_checks", fake_do)
        startup._linux_pkg_checks()
        assert seen["ext"] == "deb"
        assert seen["basecmd"] == ["dpkg", "-s"]

    def test_fedora_routed_to_rpm(self, monkeypatch):
        import distro

        monkeypatch.setattr(distro, "id", lambda: "fedora")
        monkeypatch.setattr(distro, "os_release_info", lambda: {"id": "fedora"})
        seen = {}

        def fake_do(dist, ext, packages, basecmd):
            seen.update(ext=ext, basecmd=basecmd)

        monkeypatch.setattr(startup, "_do_linux_pkg_checks", fake_do)
        startup._linux_pkg_checks()
        assert seen["ext"] == "rpm"
        assert seen["basecmd"] == ["rpm", "-q"]

    def test_unknown_distro_skips_without_raise(self, monkeypatch):
        import distro

        monkeypatch.setattr(distro, "id", lambda: "arch")
        monkeypatch.setattr(distro, "os_release_info", lambda: {"id": "arch"})
        called = {}
        monkeypatch.setattr(
            startup,
            "_do_linux_pkg_checks",
            lambda *a, **k: called.setdefault("did", True),
        )
        # Unknown distro -> warning path, no package check, no raise.
        startup._linux_pkg_checks()
        assert "did" not in called

#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Unit tests for --nodefile parsing (GNU-parallel style).

Covers the parser in ``sierra.core.plugins.execenv``: ``parse_nodefile`` (whole
file) and ``_parse_nodefile_line`` (single line). A nodefile line names a
compute resource; the parser must extract host, core count, login, and port from
several spellings, skip comments, and reject garbage.
"""

# Core packages
import os
import pwd

# 3rd party packages
import pytest

# Project packages
from sierra.core import execenv


def _me() -> str:
    """The current user's login, which the parser fills in when a line omits
    'user@'."""
    return pwd.getpwuid(os.getuid())[0]


# --- Single-line parsing ---------------------------------------------------
class TestParseLine:
    def test_comment_skipped(self):
        assert execenv._parse_nodefile_line("# a comment") is None

    def test_bare_hostname(self):
        # Just a host: 1 core, current user, default ssh port 22.
        spec = execenv._parse_nodefile_line("myhost")
        assert spec.hostname == "myhost"
        assert spec.n_cores == 1
        assert spec.login == _me()
        assert spec.port == 22

    def test_user_at_host(self):
        # "user@host": explicit login, default port.
        spec = execenv._parse_nodefile_line("alice@server1")
        assert spec.hostname == "server1"
        assert spec.login == "alice"
        assert spec.port == 22
        assert spec.n_cores == 1

    def test_cores_prefix(self):
        # "N/host": N cores. GNU-parallel spelling.
        spec = execenv._parse_nodefile_line("4/myhost")
        assert spec.n_cores == 4
        assert spec.hostname == "myhost"

    def test_cores_prefix_with_user(self):
        spec = execenv._parse_nodefile_line("8/bob@compute01")
        assert spec.n_cores == 8
        assert spec.hostname == "compute01"
        assert spec.login == "bob"

    def test_port_and_hostname(self):
        # "ssh -p PORT host": explicit port, current user.
        spec = execenv._parse_nodefile_line("ssh -p 2222 gateway")
        assert spec.port == 2222
        assert spec.hostname == "gateway"
        assert spec.login == _me()

    def test_garbage_rejected(self):
        # A line matching no known spelling raises.
        with pytest.raises(ValueError):
            execenv._parse_nodefile_line("@@@")

    def test_dotted_hostname(self):
        # FQDNs are valid identifiers.
        spec = execenv._parse_nodefile_line("node1.cluster.example.com")
        assert spec.hostname == "node1.cluster.example.com"
        assert spec.port == 22


# --- Whole-file parsing ----------------------------------------------------
class TestParseNodefile:
    def test_mixed_file(self, tmp_path):
        nf = tmp_path / "nodes"
        nf.write_text(
            "# cluster nodes\n" "4/alice@node1\n" "node2\n" "ssh -p 2200 node3\n"
        )
        specs = execenv.parse_nodefile(str(nf))
        assert len(specs) == 3  # comment skipped

        assert specs[0].n_cores == 4
        assert specs[0].login == "alice"
        assert specs[0].hostname == "node1"

        assert specs[1].hostname == "node2"
        assert specs[1].n_cores == 1

        assert specs[2].port == 2200
        assert specs[2].hostname == "node3"

    def test_all_comments(self, tmp_path):
        nf = tmp_path / "nodes"
        nf.write_text("# only\n# comments\n")
        assert execenv.parse_nodefile(str(nf)) == []

    def test_empty_file(self, tmp_path):
        nf = tmp_path / "empty"
        nf.write_text("")
        assert execenv.parse_nodefile(str(nf)) == []


class TestPortPlusUser:
    """A line specifying BOTH an ssh port and a user@host, e.g.
    ``ssh -p 2222 alice@host``, must yield all three: port, login, and host.
    """

    def test_port_and_user_and_host_all_parsed(self):
        spec = execenv._parse_nodefile_line("ssh -p 2222 alice@host")
        assert spec.port == 2222
        assert spec.login == "alice"
        assert spec.hostname == "host"

    def test_port_and_user_with_cores(self):
        # Core prefix composes with the port+user@host spelling.
        spec = execenv._parse_nodefile_line("4/ssh -p 2200 bob@node1")
        assert spec.n_cores == 4
        assert spec.port == 2200
        assert spec.login == "bob"
        assert spec.hostname == "node1"


class TestParseLineEdges:
    """Edge cases beyond the happy path for each branch. Full branch coverage
    isn't the same as thorough coverage -- these pin the behavior that real
    nodefiles actually exercise (newlines, no-space ports, FQDNs, multi-digit
    core counts) and document two rough edges."""

    def test_trailing_newline_tolerated(self):
        # readlines() keeps the '\n'; identifier_re stops before it, so a real
        # file line parses the same as a stripped one.
        spec = execenv._parse_nodefile_line("myhost\n")
        assert spec.hostname == "myhost"
        assert spec.port == 22

    def test_port_without_space(self):
        # port_re allows zero spaces after -p, so "-p2222" is valid.
        spec = execenv._parse_nodefile_line("ssh -p2222 host")
        assert spec.port == 2222
        assert spec.hostname == "host"

    def test_multi_digit_cores(self):
        spec = execenv._parse_nodefile_line("16/host")
        assert spec.n_cores == 16
        assert spec.hostname == "host"

    def test_fqdn_user_and_host(self):
        # Dots are valid identifier chars on both sides of '@'.
        spec = execenv._parse_nodefile_line("a.b@c.d")
        assert spec.login == "a.b"
        assert spec.hostname == "c.d"

    def test_colon_kept_in_hostname(self):
        # identifier_re includes ':', so a host:port-style token stays whole.
        spec = execenv._parse_nodefile_line("host:1234")
        assert spec.hostname == "host:1234"

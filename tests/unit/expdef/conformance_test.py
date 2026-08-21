#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""The expdef *contract*, expressed once and run against every backend.

Parametrized over ``ALL_BACKENDS``. Every test here runs against xml, json, and
yaml. Adding a backend means adding a ``Backend`` in ``backends.py`` and writing
zero tests here.

Two kinds of assertion live here:

* Universal contract -- behavior every backend MUST share. These read the same
  regardless of backend.
* Type-fidelity contract -- behavior that legitimately differs by backend but
  must still be pinned down (XML stringifies scalars; json/yaml preserve them).
  We assert the backend's declared value rather than papering over it.

Capability-gated tests use ``skip_unless`` so a backend that does not implement
an operation (e.g. XML flatten) is skipped, not failed, without forking the
test. Behaviors that are genuinely backend-shaped live in ``*_quirks_test.py``.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest

# Project packages
from tests.unit.expdef.backends import ALL_BACKENDS, Backend


# Parametrize the whole module: every test function that takes ``backend`` runs
# once per registered backend, with a readable id ("xml"/"json"/"yaml").
@pytest.fixture(params=ALL_BACKENDS, ids=lambda b: b.name)
def backend(request) -> Backend:
    return request.param


@pytest.fixture
def basic(backend, tmp_path) -> object:
    """A loaded ExpDef over the backend's 'basic' document."""
    fpath = tmp_path / f"basic{backend.ext}"
    fpath.write_text(backend.doc_basic)
    return backend.ctor(fpath)


@pytest.fixture
def nested(backend, tmp_path) -> object:
    """A loaded ExpDef over the backend's 'nested' document."""
    fpath = tmp_path / f"nested{backend.ext}"
    fpath.write_text(backend.doc_nested)
    return backend.ctor(fpath)


def _skip_unless(condition, reason):
    if not condition:
        pytest.skip(reason)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
class TestInitialization:
    def test_loads(self, basic):
        assert basic is not None

    def test_mods_start_empty(self, basic):
        adds, chgs = basic.n_mods()
        assert adds == 0 and chgs == 0


# ---------------------------------------------------------------------------
# attr_get
# ---------------------------------------------------------------------------
class TestAttrGet:
    def test_existing_string(self, basic, backend):
        assert basic.attr_get(backend.p_app, "name") == "MyApp"

    def test_missing_path_returns_none(self, basic, backend):
        assert basic.attr_get(backend.p_missing, "name") is None

    def test_missing_attr_returns_none(self, basic, backend):
        assert basic.attr_get(backend.p_app, "nonexistent") is None

    def test_nested(self, nested, backend):
        assert nested.attr_get(backend.p_nested, "value") == "deep"

    def test_container_not_returned_as_attr(self, basic, backend):
        # 'database' is a container under root, not a scalar attribute of it.
        assert basic.attr_get(backend.p_root, "database") is None

    def test_scalar_type_fidelity(self, basic, backend):
        # The tests that are SUPPOSED to differ per backend, pinned down.
        assert basic.attr_get(backend.p_app, "port") == backend.port_value
        assert basic.attr_get(backend.p_app, "debug") == backend.debug_value


# ---------------------------------------------------------------------------
# attr_change
# ---------------------------------------------------------------------------
class TestAttrChange:
    def test_existing_roundtrips(self, basic, backend):
        assert basic.attr_change(backend.p_app, "name", "new") is True
        assert basic.attr_get(backend.p_app, "name") == "new"

    def test_int_value(self, basic, backend):
        assert basic.attr_change(backend.p_app, "port", 42) is True
        assert basic.attr_get(backend.p_app, "port") == backend.changed_int_value

    def test_missing_path_is_noop(self, basic, backend):
        assert basic.attr_change(backend.p_missing, "name", "x") is False

    def test_missing_attr_is_noop(self, basic, backend):
        assert basic.attr_change(backend.p_app, "nope", "x") is False

    def test_nested(self, nested, backend):
        assert nested.attr_change(backend.p_nested, "value", "shallow") is True
        assert nested.attr_get(backend.p_nested, "value") == "shallow"

    def test_tracks_modification(self, basic, backend):
        _, before = basic.n_mods()
        basic.attr_change(backend.p_app, "name", "new")
        _, after = basic.n_mods()
        assert after == before + 1

    def test_noprint_still_changes(self, basic, backend):
        assert basic.attr_change(backend.p_app, "name", "q", noprint=True) is True
        assert basic.attr_get(backend.p_app, "name") == "q"


# ---------------------------------------------------------------------------
# attr_add
# ---------------------------------------------------------------------------
class TestAttrAdd:
    def test_new_attr(self, basic, backend):
        assert basic.attr_add(backend.p_app, "added", "v") is True
        assert basic.attr_get(backend.p_app, "added") == "v"

    def test_duplicate_fails(self, basic, backend):
        assert basic.attr_add(backend.p_app, "name", "dup") is False

    def test_missing_path_fails(self, basic, backend):
        assert basic.attr_add(backend.p_missing, "added", "v") is False

    def test_nested(self, nested, backend):
        assert nested.attr_add(backend.p_nested, "extra", "e") is True
        assert nested.attr_get(backend.p_nested, "extra") == "e"

    def test_tracks_modification(self, basic, backend):
        _, chgs_before = basic.n_mods()
        basic.attr_add(backend.p_app, "added", "v")
        _, chgs_after = basic.n_mods()
        assert chgs_after == chgs_before + 1

    def test_noprint(self, basic, backend):
        assert basic.attr_add(backend.p_app, "q", "v", noprint=True) is True


# ---------------------------------------------------------------------------
# has_element / has_attr
# ---------------------------------------------------------------------------
class TestHasElement:
    def test_true(self, basic, backend):
        assert basic.has_element(backend.p_app) is True

    def test_second_container_true(self, basic, backend):
        assert basic.has_element(backend.p_db_child) is True

    def test_false(self, basic, backend):
        assert basic.has_element(backend.p_missing) is False

    def test_nested_true(self, nested, backend):
        assert nested.has_element(backend.p_nested) is True


class TestHasAttr:
    def test_true(self, basic, backend):
        assert basic.has_attr(backend.p_app, "name") is True

    def test_false_attr(self, basic, backend):
        assert basic.has_attr(backend.p_app, "nope") is False

    def test_false_path(self, basic, backend):
        assert basic.has_attr(backend.p_missing, "name") is False

    def test_nested_true(self, nested, backend):
        assert nested.has_attr(backend.p_nested, "value") is True


# ---------------------------------------------------------------------------
# element_add / element_remove
# ---------------------------------------------------------------------------
class TestElementAdd:
    def test_add_present_after(self, basic, backend):
        basic.element_add(backend.p_app, "child", allow_dup=True)
        adds, _ = basic.n_mods()
        assert adds >= 1

    def test_add_missing_parent_fails(self, basic, backend):
        assert basic.element_add(backend.p_missing, "child") is False

    def test_add_duplicate_not_allowed(self, basic, backend):
        basic.element_add(backend.p_app, "child", allow_dup=False)
        result = basic.element_add(backend.p_app, "child", allow_dup=False)
        assert result is False


class TestElementRemove:
    def test_remove_missing_is_noop(self, basic, backend):
        assert basic.element_remove(backend.p_missing, "element") is False

    def test_remove_existing(self, basic, backend):
        # database is a removable child of root.
        assert basic.element_remove(backend.p_db_parent, backend.p_db_child) is True
        assert basic.has_element(backend.p_db) is False

    def test_remove_noprint(self, basic, backend):
        assert basic.element_remove(backend.p_missing, "element", noprint=True) is False


# ---------------------------------------------------------------------------
# element_change (capability-gated: json does not support leaf renames)
# ---------------------------------------------------------------------------
class TestElementChange:
    def test_rename_leaf(self, nested, backend):
        _skip_unless(backend.supports_element_change, "no element_change")
        parent = backend.p_nested_parent  # holds 'level3'
        nested.element_change(parent, "level3", "leaf3")
        # Assert the observable post-condition rather than the return sentinel:
        # the old name is gone and the new one is present under the same parent.
        old_path = backend.p_nested  # ...level2/level3
        new_path = old_path.rsplit("level3", 1)[0] + "leaf3"
        assert nested.has_element(old_path) is False
        assert nested.has_element(new_path) is True

    def test_rename_preserves_subtree(self, nested, backend):
        _skip_unless(backend.supports_element_change, "no element_change")
        val_before = nested.attr_get(backend.p_nested, "value")
        parent = backend.p_nested_parent
        nested.element_change(parent, "level3", "leaf3")
        # value survives the rename (path now ends in leaf3)
        new_path = backend.p_nested.rsplit("level3", 1)[0] + "leaf3"
        assert nested.attr_get(new_path, "value") == val_before


# ---------------------------------------------------------------------------
# write round-trip (structural; value regression lives in regression/)
# ---------------------------------------------------------------------------
class TestWriteRoundtrip:
    def test_write_produces_readable_file(self, basic, backend, tmp_path):
        from sierra.core.experiment import definition

        basic.attr_change(backend.p_app, "name", "written")
        out = tmp_path / f"out{backend.ext}"
        cfg = definition.WriterConfig([{"src_parent": None, "src_tag": backend.p_root}])
        basic.write_config_set(cfg)
        basic.write(out)

        assert out.is_file()
        reloaded = backend.ctor(out)
        assert reloaded.attr_get(backend.p_app, "name") == "written"

    def test_write_after_add(self, basic, backend, tmp_path):
        from sierra.core.experiment import definition

        basic.attr_add(backend.p_app, "added", "v")
        out = tmp_path / f"out2{backend.ext}"
        cfg = definition.WriterConfig([{"src_parent": None, "src_tag": backend.p_root}])
        basic.write_config_set(cfg)
        basic.write(out)
        reloaded = backend.ctor(out)
        assert reloaded.attr_get(backend.p_app, "added") == "v"


# ---------------------------------------------------------------------------
# write configuration (universal: every backend gates write on a config)
# ---------------------------------------------------------------------------
class TestWriteConfig:
    def test_write_config_set_then_write_succeeds(self, basic, backend, tmp_path):
        from sierra.core.experiment import definition

        cfg = definition.WriterConfig([{"src_parent": None, "src_tag": backend.p_root}])
        basic.write_config_set(cfg)
        out = tmp_path / f"cfg{backend.ext}"
        basic.write(out)
        assert out.is_file()

    def test_write_section(self, basic, backend, tmp_path):
        from sierra.core.experiment import definition

        cfg = definition.WriterConfig([{"src_parent": None, "src_tag": backend.p_root}])
        basic.write_config_set(cfg)
        basic.attr_change(backend.p_app, "name", "sectioned")
        out = tmp_path / f"sec{backend.ext}"
        basic.write(out)
        reloaded = backend.ctor(out)
        assert reloaded.attr_get(backend.p_app, "name") == "sectioned"


# ---------------------------------------------------------------------------
# n_mods accounting
# ---------------------------------------------------------------------------
class TestNMods:
    def test_mixed_ops_exact_tally(self, basic, backend):
        """The exact accounting contract, asserted for every backend:
        ``element_add`` increments the ADD count, while ``attr_change`` AND
        ``attr_add`` both increment the CHANGE count. Starting from a freshly
        loaded doc the counters are zero, so the totals are exact, not just
        ``>= 1``.
        """
        adds0, chgs0 = basic.n_mods()
        assert adds0 == 0 and chgs0 == 0

        basic.attr_change(backend.p_app, "name", "NewApp")  # change
        basic.attr_add(backend.p_app, "timeout", "30")  # counts as change
        basic.element_add(backend.p_root, "cache", allow_dup=True)  # add
        basic.attr_change(backend.p_db, "host", "newhost")  # change

        adds, chgs = basic.n_mods()
        assert adds == 1, f"expected 1 add (element_add), got {adds}"
        assert chgs == 3, f"expected 3 changes (2 attr_change + 1 attr_add), got {chgs}"

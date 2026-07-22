#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Verify the documented YAML examples actually validate against the schemas.

These files are included verbatim into the docs via ``literalinclude``, so if
they drift from :mod:`sierra.core.graphs.schema` users will follow them and get
validation errors. Checking them mechanically is cheap and catches the drift at
CI time rather than at the user's terminal.
"""

# Core packages
import pathlib

# 3rd party packages
import pytest
import yaml
import strictyaml

# Project packages
from sierra.core.graphs import schema
from sierra.plugins.compare.graphs import schema as compareschema

DOC_ROOT = (
    pathlib.Path(__file__).parents[0].parents[1] / "docs" / "src" / "plugins" / "prod"
)

#: Maps each documented YAML file to the schema it is supposed to conform to.
#: Every schema in :data:`schema.BY_TYPE` must appear here, which is asserted
#: by :func:`test_all_types_documented` below.
DOC_FILES = {
    "prod/heatmap.yaml": schema.heatmap,
    "prod/confusion_matrix.yaml": schema.confusion_matrix,
    "prod/stacked_line.yaml": schema.stacked_line,
    "prod/histogram.yaml": schema.histogram,
    "prod/summary_line.yaml": schema.summary_line,
    "prod/network.yaml": schema.network,
    "compare/cc_and_sc.yaml": compareschema.comparison_line,
}


@pytest.mark.parametrize("fname,sch", sorted(DOC_FILES.items()))
def test_doc_yaml_validates(fname: str, sch) -> None:
    """Each graph in each documented example validates against its schema."""
    path = DOC_ROOT / fname
    if not path.exists():
        pytest.skip(f"{fname} not present in this checkout")

    doc = yaml.safe_load(path.read_text())

    # Documented examples are a single category mapping to a list of graphs.
    assert len(doc) == 1, f"{fname}: expected exactly one category"
    graphs = next(iter(doc.values()))
    assert graphs, f"{fname}: category is empty"

    for i, graph in enumerate(graphs):
        try:
            strictyaml.load(yaml.dump(graph), sch)
        except strictyaml.YAMLError as e:
            pytest.fail(f"{fname}[{i}] does not validate:\n{e}")


@pytest.mark.parametrize("fname,sch", sorted(DOC_FILES.items()))
def test_doc_yaml_type_matches(fname: str, sch) -> None:
    """The documented ``type`` matches the file it is documented in.

    Guards against the copy-paste failure mode which previously left
    ``histogram.yaml`` claiming ``type: stacked_line``.
    """
    path = DOC_ROOT / fname
    if not path.exists():
        pytest.skip(f"{fname} not present in this checkout")

    doc = yaml.safe_load(path.read_text())
    expected = _expected_type(fname)

    for graph in next(iter(doc.values())):
        assert (
            graph["type"] == expected
        ), f"{fname}: documented type is '{graph['type']}', expected '{expected}'"


def _expected_type(fname: str) -> str:
    """The graph type a given documented example is supposed to show.

    Filenames match the type they document, except the compare plugin's single
    file which covers both of its sections.
    """
    stem = pathlib.Path(fname).stem

    return "comparison_line" if stem == "cc_and_sc" else stem


def test_all_types_documented() -> None:
    """Every schema has a corresponding documented example, and vice versa."""
    documented = {_expected_type(f) for f in DOC_FILES} - {"comparison_line"}
    assert documented == set(schema.BY_TYPE), (
        "schema.BY_TYPE and the documented examples have drifted: "
        f"only in schema={set(schema.BY_TYPE) - documented}, "
        f"only in docs={documented - set(schema.BY_TYPE)}"
    )


def test_doc_yaml_exercises_optional_keys() -> None:
    """Documented examples show every key the schema accepts.

    The examples double as the reference for what is configurable, so a key
    which exists in the schema but appears in no example is undiscoverable.
    """
    for fname, sch in DOC_FILES.items():
        path = DOC_ROOT / fname
        if not path.exists():
            continue

        doc = yaml.safe_load(path.read_text())
        shown = set()
        for graph in next(iter(doc.values())):
            shown.update(graph)

        expected = {str(k) for k in sch._validator_dict}
        missing = expected - shown
        assert not missing, f"{fname}: schema keys never shown in docs: {sorted(missing)}"

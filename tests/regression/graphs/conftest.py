# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
"""Shared fixtures for the graph regression suite.

Comparison is handled by **pytest-mpl**. Because SIERRA's ``generate()``
functions write a PNG to disk rather than returning a Figure, each test wraps
the produced PNG back into a Figure via :func:`png_to_figure` and returns it;
pytest-mpl owns baseline storage, the ``--mpl-generate-path`` bless workflow,
RMS tolerance, and failure-diff images.

Goldens are only valid on an image with the same matplotlib/freetype/TeX stack.

"""

# Core packages
import pathlib
import os

# 3rd party packages
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pytest

# Project packages
from sierra.core.graphs import PathSet
from sierra.core import config
from sierra.core import plugin as pm

CSV_MEDIUM = "storage.csv"
GRAPHML_MEDIUM = "storage.graphml"


@pytest.fixture
def make_pathset(tmp_path):
    """Return a real PathSet rooted in a tmp dir.

    Exposes ``.input_root`` / ``.output_root`` / ``.model_root`` for the test to
    populate with fixtures; the graph code reads exactly these plus ``batchroot``.
    """

    def build():
        input_root = tmp_path / "input"
        output_root = tmp_path / "output"
        model_root = tmp_path / "models"
        for d in (input_root, output_root, model_root):
            d.mkdir(parents=True, exist_ok=True)
        return PathSet(
            input_root=input_root,
            output_root=output_root,
            batchroot=tmp_path,
            model_root=model_root,
        )

    return build


@pytest.fixture(scope="session", autouse=True)
def storage_plugins():
    """Ensure the necessary storage plugins are loaded."""
    # This is dependent on directory structure
    search_path = [
        pathlib.Path(os.environ["SIERRA_REPO_ROOT"]) / "sierra/plugins/storage"
    ]

    try:
        pm.pipeline.get_plugin_module(CSV_MEDIUM)
    except Exception:
        pm.pipeline.initialize("regression", search_path)
        pm.pipeline.load_plugin(CSV_MEDIUM)
        pm.pipeline.load_plugin(GRAPHML_MEDIUM)


def png_to_figure(png_path: pathlib.Path) -> plt.Figure:
    """Load a PNG from disk and return a Figure that renders it 1:1.

    pytest-mpl always re-saves the returned Figure, so this re-encode is
    unavoidable; the axis is turned off and interpolation disabled so the only
    delta vs the original is the (tolerance-absorbed) re-encode + AA.
    """
    img = mpimg.imread(png_path)
    h, w = img.shape[0], img.shape[1]
    fig = plt.figure(
        figsize=(w / config.GRAPHS["dpi"], h / config.GRAPHS["dpi"]),
        dpi=config.GRAPHS["dpi"],
    )
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.imshow(img, interpolation="none")
    return fig


def produced_png(pathset) -> pathlib.Path:
    """Return the single PNG a generator wrote, failing clearly otherwise."""
    pngs = sorted(pathset.output_root.glob("*.png"))
    assert len(pngs) == 1, f"expected one PNG, found {[p.name for p in pngs]}"
    return pngs[0]

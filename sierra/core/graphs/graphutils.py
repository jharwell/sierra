#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages
import pathlib
import typing as tp

# 3rd party packages
import holoviews as hv
import matplotlib.pyplot as plt
import bokeh

# Project packages
from sierra.core import config, utils


def save_plot(plot: hv.Overlay, output_fpath: pathlib.Path, backend: str) -> None:
    output_fpath.parent.mkdir(parents=True, exist_ok=True)
    if backend == "matplotlib":
        hv.save(
            plot.opts(fig_inches=config.GRAPHS["fig_size"]),
            output_fpath,
            fig=config.GRAPHS["static_type"],
            dpi=config.GRAPHS["dpi"],
        )
        plt.close("all")
    elif backend == "bokeh":
        fig = hv.render(plot)

        # 2025-12-02 [JRH]: We don't set dimensions, because that makes the
        # interactive plots fixed size, which makes them unsuitable for
        # embedding into webpages.
        fig.sizing_mode = "scale_width"

        html = bokeh.embed.file_html(fig, resources=bokeh.resources.INLINE)
        with utils.utf8open(output_fpath, "w") as f:
            f.write(html)


def ofile_ext(backend: str) -> tp.Optional[str]:
    if backend == "matplotlib":
        return str(config.GRAPHS["static_type"])

    if backend == "bokeh":
        return str(config.GRAPHS["interactive_type"])

    return None

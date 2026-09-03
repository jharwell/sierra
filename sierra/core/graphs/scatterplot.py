# Copyright 2018 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
{Intra,Inter}-experiment scatterplot generation for stage{4,5}.
"""

# Core packages
import logging
import typing as tp

# 3rd party packages
import holoviews as hv
import numpy as np

# Project packages
from sierra.core import config, utils, storage
from . import pathset, graphutils

_logger = logging.getLogger(__name__)


def generate(  # noqa: PLR0913
    pathset: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    xlabel: str,
    ylabel: str,
    backend: str,
    stats_center: str,
    legend: tp.Optional[list[str]] = None,
    xcol: tp.Optional[str] = None,
    ycol: tp.Optional[str] = None,
    show_best_fit: bool = False,
    best_fit_kind: tp.Optional[str] = None,
    large_text: bool = False,
) -> bool:
    """Generate a scatterplot from a set of columns in a file.

    If the necessary data file does not exist, the graph is not generated.

    Attributes:
        paths: Set of run-time tree paths for the batch experiment.

        input_stem: Stem of the :term:`Batch Summary Data` file to generate a
                    graph from.

        output_fpath: The absolute path to the output image file to save
                      generated graph to.

        stats: The type of statistics to use as the main data input. (from
               ``--stats``).

        title: Graph title.

        xcol: The column to use for the X values (intra-experiment only).

        ycol: The column to use for the Y values (intra-experiment only).

        xlabel: X-label for graph.

        ylabel: Y-label for graph.

        show_best_fit: Show a curve of best fit be overlayed over the
                       scatterplot?

        best_fit_kind: The type of fit to plot (linear, quadratic, etc).

        backend: The holoviews backend to use.

        large_text: Should the labels, ticks, and titles be large, or regular
                    size?


    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = graphutils.ofile_ext(backend)

    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )
    output_fpath = pathset.output_root / f"SP-{output_stem}.{ofile_ext}"

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot),
            input_fpath.relative_to(pathset.batchroot),
        )
        return False

    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )
    df = storage.df_read(input_fpath, medium)

    scatters = {}
    using_longform = {"exp", "x", "y"}.issubset(df.columns)
    colors = hv.Cycle().values

    points_size = tp.cast(dict[str, tp.Any], config.GRAPHS["points_size"])
    if using_longform:
        # LONG (inter-exp): one series per experiment
        by_exp = df.group_by("exp", maintain_order=True)
        exps = [e[0] for (e, _) in by_exp]
        for exp_id, group in by_exp:
            xs = group["x"].to_numpy()
            ys = group["y"].to_numpy()
            label = legend[
                exps.index(exp_id[0])  # group_by key is a 1 element tuple here
            ]
            color = colors[exps.index(exp_id[0]) % len(colors)]

            scatters[label] = hv.Scatter((xs, ys)).opts(
                alpha=0.5, **points_size[backend], color=color
            )

    else:
        points_size = tp.cast(dict[str, tp.Any], config.GRAPHS["points_size"])
        # WIDE (intra-exp): one series per (xcol, ycol) pair
        xs = df[xcol].to_numpy()
        ys = df[ycol].to_numpy()
        scatters["exp"] = hv.Scatter((xs, ys)).opts(alpha=0.5, **points_size[backend])

    plot = hv.NdOverlay(scatters, kdims="series").opts(
        hv.opts.Scatter(marker=hv.Cycle(["o", "s", "^", "d", "x", "+", "*"]))
    )

    if show_best_fit and using_longform:
        fits = []
        exps = [e[0] for (e, _) in by_exp]
        for exp_id, group in by_exp:
            xs = group["x"].to_numpy()
            ys = group["y"].to_numpy()
            x_line, y_line, r2, _eqn = _calc_best_fit(xs, ys, best_fit_kind)
            color = colors[exps.index(exp_id[0]) % len(colors)]
            fits.append(hv.Curve((x_line, y_line)).opts(show_legend=False, color=color))

        for f in fits:
            plot *= f

    if show_best_fit and not using_longform:
        xs = df[xcol].to_numpy()
        ys = df[ycol].to_numpy()
        x_line, y_line, r2, eqn_label = _calc_best_fit(xs, ys, best_fit_kind)
        plot *= hv.Curve((x_line, y_line), label="Fit")

        # Only put the eqn on there for a single line; too noisy otherwise.
        title = f"{title}: {eqn_label} (R² = {r2:.3f})"

    plot.opts(title=title, xlabel=xlabel, ylabel=ylabel)

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
            "legend": text_size["legend_label"],
        },
    )

    graphutils.plot_save(plot, output_fpath, backend)

    _logger.debug(
        "Graph written to <batchroot>/%s", output_fpath.relative_to(pathset.batchroot)
    )

    return True


_POLY_DEGREE = {"linear": 1, "quadratic": 2, "cubic": 3}


def _calc_best_fit(xs, ys, kind):
    """Return (x_line, y_line, r2, label_str) for the requested fit kind."""
    if xs.size < 2 or np.ptp(xs) == 0 or np.ptp(ys) == 0:
        return None, None, float("nan"), ""
    if kind in _POLY_DEGREE:
        deg = _POLY_DEGREE[kind]
        coeffs = np.polyfit(xs, ys, deg)
        y_pred = np.polyval(coeffs, xs)
        x_line = np.linspace(xs.min(), xs.max(), 200)
        y_line = np.polyval(coeffs, x_line)
        eqn = _format_poly_eqn(coeffs)

    elif kind == "log":  # y = a*ln(x) + b
        mask = xs > 0  # ln undefined for x <= 0
        a, b = np.polyfit(np.log(xs[mask]), ys[mask], 1)
        y_pred = a * np.log(xs) + b
        x_line = np.linspace(xs.min(), xs.max(), 200)
        y_line = a * np.log(x_line) + b
        eqn = f"y = {a:.3g}·ln(x) + {b:.3g}"

    elif kind == "exp":  # y = a*exp(b*x)  -> fit ln(y) = ln(a) + b*x
        mask = ys > 0
        b, ln_a = np.polyfit(xs[mask], np.log(ys[mask]), 1)
        a = np.exp(ln_a)
        y_pred = a * np.exp(b * xs)
        x_line = np.linspace(xs.min(), xs.max(), 200)
        y_line = a * np.exp(b * x_line)
        eqn = f"y = {a:.3g}·exp({b:.3g}x)"

    else:
        raise ValueError(f"Unknown best_fit_kind: {kind!r}")

    # R^2 computed against the ORIGINAL y, in original space
    ss_res = np.sum((ys - y_pred) ** 2)
    ss_tot = np.sum((ys - np.mean(ys)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return x_line, y_line, r2, eqn


def _format_poly_eqn(coeffs):
    """Format polyfit coefficients (highest-degree first) as 'y = ...'."""
    deg = len(coeffs) - 1
    terms = []
    for i, c in enumerate(coeffs):
        power = deg - i
        if power == 0:
            terms.append(f"{c:.3g}")
        elif power == 1:
            terms.append(f"{c:.3g}x")
        else:
            terms.append(f"${c:.3g}x^{power}$")
    return "y = " + " + ".join(terms)


__all__ = ["generate"]

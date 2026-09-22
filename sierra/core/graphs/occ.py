# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Intra-experiment Operating Characteristic Curves (OCC) for stage {4,5}."""
# Core packages
import logging
import typing as tp

# 3rd party packages
import holoviews as hv
import numpy as np
import polars as pl
from sklearn.metrics import auc, roc_curve

# Project packages
from sierra.core import config, utils, storage
from . import graphutils, pathset

_logger = logging.getLogger(__name__)


def generate_risk_coverage(  # noqa: PLR0913,PLR0917
    pathset: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    truthcol: str,
    predcol: str,
    confcol: str,
    title: str,
    xlabel: str,
    ylabel: str,
    backend: str,
    stats_center: str,
    show_oracle: bool,
    show_baseline: bool,
    *,
    large_text: bool = False,
):
    """

    Top-1-only classifier risk vs coverage curves.

    This is the curve a top-1-only classifier *can* support: it needs just
    the predicted class, the true class, and the single top-1 confidence per
    sample -- no per-class score vector. We threshold on that confidence ("only
    answer when conf >= t") and sweep t. As the gate loosens, coverage (the
    fraction of samples answered) rises 0 -> 1 and the selective risk (error
    rate among answered samples) typically rises with it. The area under that
    curve (AURC, lower is better) summarises how well the model's confidence
    tracks its own correctness.

    Two reference traces can be overlaid: the *oracle* (the lowest risk-coverage
    curve any confidence ranking could achieve on this data -- all correct
    predictions answered first) and the *overall error* line (risk at full
    coverage). The gap between model and oracle is the headroom in the
    confidence signal.

    .. IMPORTANT:: This is NOT an ROC/AUC and must not be reported as one: it
       measures confidence-vs-correctness, not class separability.

    Arguments
    ---------
    truthcol : column holding the true class of each sample.
    predcol  : column holding the model's predicted class.
    confcol  : column holding the model's top-1 confidence for that prediction.
    show_oracle : overlay the best-achievable (perfectly-ranked) curve.
    show_baseline : overlay the overall-error line (risk at full coverage).

    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = graphutils.ofile_ext(backend)

    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )

    output_fpath = pathset.output_root / f"RC-{output_stem}.{ofile_ext}"

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot),
            input_fpath.relative_to(pathset.batchroot),
        )
        return False

    df = storage.df_read(input_fpath, medium)

    required_cols = [truthcol, predcol, confcol]
    if not all(c in df.columns for c in required_cols):
        _logger.warning(
            (
                "Not generating <batchroot>/%s: not all required columns "
                "present: required=%s,missing=%s"
            ),
            output_fpath.relative_to(pathset.batchroot),
            required_cols,
            set(required_cols) - set(df.columns),
        )
        return False

    # Correctness is the only thing the confidence gets scored against here.
    correct = (df[predcol] == df[truthcol]).cast(pl.Int32).to_numpy()

    conf = df[confcol].to_numpy()
    n = len(correct)

    # Answer the most-confident samples first; sweep the gate down.
    order = np.argsort(-conf, kind="stable")
    correct_sorted = correct[order]

    covered = np.arange(1, n + 1)
    coverage = covered / n
    selective_risk = 1.0 - np.cumsum(correct_sorted) / covered
    aurc = float(np.trapz(selective_risk, coverage))
    overall_error = 1.0 - correct.mean()

    palette = hv.Cycle().values

    curve_width = tp.cast(dict[str, tp.Any], config.GRAPHS["curve_width"])
    curve_dashed = tp.cast(dict[str, tp.Any], config.GRAPHS["curve_dashed"])
    overlays = [
        hv.Curve(
            (coverage, selective_risk),
            kdims=["coverage"],
            vdims=["risk"],
            label=f"Model (AURC={aurc:.3f})",
        ).opts(
            color=palette[0],
            **curve_width[backend],
        )
    ]

    if show_oracle:
        # Lowest curve any ranking could reach: all correct answered first.
        oracle_sorted = np.sort(correct)[::-1]
        oracle_risk = 1.0 - np.cumsum(oracle_sorted) / covered
        aurc_oracle = float(np.trapz(oracle_risk, coverage))
        overlays.append(
            hv.Curve(
                (coverage, oracle_risk),
                kdims=["coverage"],
                vdims=["risk"],
                label=f"Oracle (AURC={aurc_oracle:.3f})",
            ).opts(
                color="gray",
                **curve_dashed[backend],
            )
        )

    if show_baseline:
        curve_dotted = tp.cast(dict[str, tp.Any], config.GRAPHS["curve_dotted"])
        overlays.append(
            hv.Curve(
                [(0.0, overall_error), (1.0, overall_error)],
                kdims=["coverage"],
                vdims=["risk"],
                label=f"Overall Error ({overall_error:.3f})",
            ).opts(
                color="red",
                **curve_dotted[backend],
            )
        )

    plot = hv.Overlay(overlays).opts(
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        show_legend=True,
        legend_position="right",
    )
    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )
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


def generate_roc(  # noqa: PLR0913, PLR0917
    pathset: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    truthcol: str,
    scorecols: dict[str, str],
    title: str,
    xlabel: str,
    ylabel: str,
    backend: str,
    stats_center: str,
    show_micro: bool,
    show_diagonal: bool,
    *,
    legend: tp.Optional[tp.Sequence[str]] = None,
    large_text: bool = False,
):
    """One-vs-Rest ROC curves for a multiclass classifier.

    Unlike :func:`generate_src`, this needs the model's *per-class score
    vector*, not just top-1 confidence: one score column per class, giving the
    model's belief in that class for *every* sample (including ones where the
    class was not predicted). For each class ``c`` we form the binary
    sub-problem "is this sample class ``c`` or not", threshold that class's
    score column, and sweep -- yielding one curve per class. A pooled
    micro-average curve and the chance diagonal are overlaid for reference; the
    macro-average AUC (unweighted mean of the per-class AUCs) is reported in the
    title.

    ``scorecols`` is keyed on the *raw* label value (not a display name),
    mirroring the raw-keyed colour map so curves, colours, scores and legend
    stay in sync without touching the dataframe dtype. Its keys must cover every
    value present in ``truthcol``.

    .. IMPORTANT:: ROC and :func:`generate_src` consume *different inputs* and
       answer *different questions*. ROC measures class separability (higher AUC
       better); the selective-risk curve measures confidence-vs-correctness
       (lower AURC better). Do not compare the two scalars.

    Arguments
    ---------

    truthcol: Column holding the true class of each sample.

    scorecols: Mapping of each raw class label to the column holding that
        class's score. Must cover every class in ``truthcol``.

    show_micro: Overlay the pooled (frequency-weighted) micro-average curve.

    show_diagonal: Overlay the chance diagonal (AUC = 0.5 reference).

    legend: Optional display names, supplied positionally in sorted-label
        order; defaults to the stringified labels.

    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = graphutils.ofile_ext(backend)

    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )
    output_fpath = pathset.output_root / f"ROC-{output_stem}.{ofile_ext}"

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot),
            input_fpath.relative_to(pathset.batchroot),
        )
        return False

    df = storage.df_read(input_fpath, medium)

    required_cols = [*list(scorecols.values()), truthcol]
    if not all(c in df.columns for c in required_cols):
        _logger.warning(
            (
                "Not generating <batchroot>/%s: not all required columns "
                "present: required=%s,missing=%s"
            ),
            output_fpath.relative_to(pathset.batchroot),
            required_cols,
            set(required_cols) - set(df.columns),
        )
        return False

    unique_labels = sorted(df[truthcol].unique().to_list())

    missing = [lab for lab in unique_labels if lab not in scorecols]
    if missing:
        raise ValueError(
            f"scorecols is missing a score column for label(s) {missing}; "
            f"every class in '{truthcol}' needs one"
        )

    # Display names: stringify by default; a caller-supplied `legend` overrides
    # positionally in sorted-label order.
    if legend is None:
        legend = [str(lab) for lab in unique_labels]

    if len(legend) != len(unique_labels):
        raise ValueError(
            f"legend has {len(legend)} entries but '{truthcol}' has "
            f"{len(unique_labels)} unique values"
        )

    name_map = dict(zip(unique_labels, legend))

    # Colours keyed on the RAW label value, so curves and legend swatches stay
    # in sync without rewriting the dataframe.
    palette = hv.Cycle().values
    cmap = {lab: palette[i % len(palette)] for i, lab in enumerate(unique_labels)}

    y = df[truthcol].to_numpy()

    # One Curve per class -> Holoviews emits a categorical legend entry per
    # element. For class `lab`: positive = (truth == lab), score = its column.
    overlays = []
    aucs = []
    pooled_true, pooled_score = [], []
    for lab in unique_labels:
        binary = (y == lab).astype(int)
        score = df[scorecols[lab]].to_numpy()

        fpr, tpr, _ = roc_curve(binary, score)
        roc_auc = auc(fpr, tpr)

        aucs.append(roc_auc)
        pooled_true.append(binary)
        pooled_score.append(score)

        overlays.append(
            hv.Curve(
                (fpr, tpr),
                kdims=["fpr"],
                vdims=["tpr"],
                label=f"{name_map[lab]} ({roc_auc:.2f})",
            ).opts(color=cmap[lab])
        )

    macro_auc = float(np.mean(aucs))

    if show_micro:
        curve_width = tp.cast(dict[str, tp.Any], config.GRAPHS["curve_width"])
        # Micro-average: pool every (score, is-this-class) decision into one ROC.
        mt = np.concatenate(pooled_true)
        ms = np.concatenate(pooled_score)
        mfpr, mtpr, _ = roc_curve(mt, ms)
        micro_auc = auc(mfpr, mtpr)
        overlays.append(
            hv.Curve(
                (mfpr, mtpr),
                kdims=["fpr"],
                vdims=["tpr"],
                label=f"Micro-avg ({micro_auc:.2f})",
            ).opts(color="black", **curve_width[backend])
        )

    if show_diagonal:
        curve_dashed = tp.cast(dict[str, tp.Any], config.GRAPHS["curve_dashed"])
        overlays.append(
            hv.Curve(
                [(0.0, 0.0), (1.0, 1.0)],
                kdims=["fpr"],
                vdims=["tpr"],
                label="Chance",
            ).opts(color="gray", **curve_dashed[backend])
        )

    plot = hv.Overlay(overlays).opts(
        title=f"{title} (macro-AUC={macro_auc:.3f})",
        xlabel=xlabel,
        ylabel=ylabel,
        show_legend=True,
        legend_position="right",
    )
    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )
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


__all__ = ["generate_risk_coverage", "generate_roc"]

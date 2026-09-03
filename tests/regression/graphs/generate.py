# Copyright 2026, All rights reserved.
#
# SPDX-License-Identifier: MIT
"""
Deterministic, high-fidelity fixture data for the graph regression suite.

The data here is modeled on SIERRA's example ``jsonsim`` / ``yamlsim`` engines:
a deterministic reference signal with genuinely distinct noisy channels
(gaussian / heavy-tailed / drift), Anscombe's quartet, a 2D ripple interference
field, a story-telling confusion matrix, scale-free graphs with clear hubs, and
named distribution families. The point is that every blessed graph should look
*interesting*, not like a toy.

Determinism: the reference/baseline channels and Anscombe are pure functions of
their index (byte-stable regression anchors). Noisy channels are drawn from a
seeded generator, and -- crucially -- the spread siblings are computed
*analytically* from a fixed noise model rather than sampled across runs, so the
conf95/bw/iqr bands are real and reproducible without a Monte-Carlo step.
"""

# Core packages
import hashlib
import pathlib

# 3rd party packages
import numpy as np
import polars as pl
import networkx as nx

SEED = 42
N_TICKS = 50  # matches jsonsim's signal length
N_EXP = 10  # datapoints in a batch summary


def _rng(tag: str) -> np.random.Generator:
    # hashlib (not builtin hash()) -- builtin hash is salted per-process, which
    # would make fixture data differ every run and break pixel baselines.
    digest = hashlib.sha256(f"{SEED}:{tag}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def _write(df: pl.DataFrame, root: pathlib.Path, stem: str, ext: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    df.write_csv(root / f"{stem}{ext}")


# ---------------------------------------------------------------------------
# Analytic spread siblings
# ---------------------------------------------------------------------------
def _spread_siblings(
    root, stem, mean_vdims: pl.DataFrame, sigma: dict[str, np.ndarray]
) -> None:
    """Write conf95 + bw + iqr siblings from a per-column sigma profile.

    Bands are computed from a normal model: stddev=sigma, quartiles at
    +/-0.674 sigma, whiskers at +/-1.5 IQR, CI of the median at
    +/-1.57*IQR/sqrt(N). This yields well-formed, visually meaningful boxes
    that are exactly reproducible (no sampling).
    """
    cols = mean_vdims.columns
    n = len(mean_vdims)

    def frame(fn):
        return pl.DataFrame({c: fn(mean_vdims[c].to_numpy(), sigma[c]) for c in cols})

    iqr = {c: 2 * 0.674 * sigma[c] for c in cols}

    _write(frame(lambda m, s: s), root, stem, ".stddev")
    _write(frame(lambda m, s: m), root, stem, ".median")
    _write(frame(lambda m, s: m - 0.674 * s), root, stem, ".q1")
    _write(frame(lambda m, s: m + 0.674 * s), root, stem, ".q3")
    _write(frame(lambda m, s: m - (0.674 + 1.5) * s), root, stem, ".whislo")
    _write(frame(lambda m, s: m + (0.674 + 1.5) * s), root, stem, ".whishi")
    _write(
        frame(lambda m, s: m - 1.57 * (2 * 0.674 * s) / np.sqrt(n)), root, stem, ".cilo"
    )
    _write(
        frame(lambda m, s: m + 1.57 * (2 * 0.674 * s) / np.sqrt(n)), root, stem, ".cihi"
    )


# ---------------------------------------------------------------------------
# Signal-trace channels (the jsonsim/yamlsim heart)
# ---------------------------------------------------------------------------
def _trace_channels(n: int, rng):
    """Return (mean_frame, sigma_profile) for the signal-trace family.

    reference/baseline are deterministic; measured/drift/raw carry distinct,
    physically-flavored noise so the spread bands differ per channel:
      * measured: constant gaussian sigma
      * drift:    accumulating bias + small sigma (band widens over time)
      * raw:      heavy-tailed -> larger effective sigma
    """
    clock = np.arange(n)
    t = clock / max(n - 1, 1) * 2.0 * np.pi
    reference = np.sin(t)
    baseline = np.cos(t)
    measured = reference + rng.normal(0.0, 0.25, n)
    drift = reference + np.linspace(0.0, 0.8, n) + rng.normal(0.0, 0.10, n)
    raw = reference + rng.standard_t(3, n) * 0.20

    mean = pl.DataFrame(
        {
            "reference": reference,
            "measured": measured,
            "drift": drift,
            "baseline": baseline,
            "raw": raw,
        }
    )
    sigma = {
        "reference": np.full(n, 0.02),
        "measured": np.full(n, 0.25),
        "drift": 0.10 + np.linspace(0.0, 0.25, n),  # widening band
        "baseline": np.full(n, 0.02),
        "raw": np.full(n, 0.35),  # heavy tail -> wide
    }
    return mean, sigma


def timeseries_data(
    root, stem, with_stats=True, with_model=False, positive=False, cols=None
):
    """Intra-experiment signal trace for stacked_line."""
    rng = _rng("ts:" + stem)
    mean, sigma = _trace_channels(N_TICKS, rng)
    if cols:
        mean = mean.select(cols)
        sigma = {c: sigma[c] for c in cols}
    if positive:
        # Shift everything positive for the logyscale variation.
        shift = min(mean[c].min() for c in mean.columns)
        mean = pl.DataFrame({c: mean[c].to_numpy() - shift + 1.0 for c in mean.columns})
    _write(mean, root, stem, ".mean")
    if with_stats:
        _spread_siblings(root, stem, mean, sigma)
    if with_model:
        # A plausible model: a clean sine fit through the reference phase.
        model = pl.DataFrame({c: mean[c].to_numpy() * 0.95 + 0.1 for c in mean.columns})
        _write(model, root, stem, ".model")
        (root / f"{stem}.legend").write_text(
            "\n".join(f"model: {c}" for c in mean.columns) + "\n"
        )


def summary_data(root, stem, ncols=3, with_stats=True, with_model=False):
    """Batch-summary: col 0 is experiment index, then vdims.

    Emulates a scaling study: a saturating performance curve, a linear cost, and
    a decaying error -- three qualitatively different shapes on one graph.
    """
    rng = _rng("summary:" + stem)
    idx = np.arange(N_EXP)
    x = idx.astype(float)
    shapes = {
        "throughput": 100 * (1 - np.exp(-x / 3)),  # saturating
        "cost": 5 + 2.0 * x,  # linear
        "error": 50 * np.exp(-x / 4) + 2,  # decaying
        "latency": 20 + 8 * np.sin(x / 2) + x,  # oscillating+trend
    }
    names = list(shapes)[:ncols]
    mean_vdims = pl.DataFrame({c: shapes[c] for c in names})
    _write(
        pl.DataFrame({"exp": idx, **{c: shapes[c] for c in names}}), root, stem, ".mean"
    )
    if with_stats:
        sigma = {c: 0.05 * np.abs(mean_vdims[c].to_numpy()) + 1.0 for c in names}
        _spread_siblings(root, stem, mean_vdims, sigma)
    if with_model:
        model = pl.DataFrame({"exp": idx, **{c: shapes[c] * 1.05 for c in names}})
        _write(model, root, stem, ".model")
        (root / f"{stem}.legend").write_text(
            "\n".join(f"model: {c}" for c in names) + "\n"
        )


# ---------------------------------------------------------------------------
# Heatmaps
# ---------------------------------------------------------------------------
def heatmap_numeric_data(root, stem, nx=12, ny=10):
    """2D ripple/interference field z = sin(r): smooth, structured, pretty."""
    rng = _rng("hm:" + stem)
    xs, ys, zs = [], [], []
    for i in range(nx):
        for j in range(ny):
            r = np.sqrt((i - nx / 2) ** 2 + (j - ny / 2) ** 2)
            xs.append(i)
            ys.append(j)
            zs.append(float(np.sin(r) + rng.normal(0, 0.02)))
    _write(pl.DataFrame({"x": xs, "y": ys, "z": zs}), root, stem, ".mean")


def heatmap_grid_data(root, stem, n=10):
    """Square grid form (row index + columns) for dual-heatmap inputs."""
    rng = _rng("hmgrid:" + stem)
    grid = np.fromfunction(
        lambda i, j: np.sin(np.sqrt((i - n / 2) ** 2 + (j - n / 2) ** 2)), (n, n)
    )
    grid = grid + rng.normal(0, 0.02, (n, n))
    _write(pl.DataFrame(grid, schema=[f"c{i}" for i in range(n)]), root, stem, ".mean")


def confusion_data(root, stem):
    """Diagonal-dominant matrix with SYSTEMATIC confusions (0<->1, 3<->8),
    so the CM- heatmap tells a story rather than being uniform noise."""
    rng = _rng("cm:" + stem)
    classes = list(range(10))
    confused = {0: 1, 1: 0, 3: 8, 8: 3}
    truth, pred = [], []
    for a in classes:
        for p in classes:
            if a == p:
                cnt = int(rng.integers(70, 95))
            elif confused.get(a) == p:
                cnt = int(rng.integers(20, 35))
            else:
                cnt = int(rng.integers(1, 6))
            truth += [a] * cnt
            pred += [p] * cnt
    _write(pl.DataFrame({"truth": truth, "predicted": pred}), root, stem, ".mean")


# ---------------------------------------------------------------------------
# Scatterplots
# ---------------------------------------------------------------------------
_ANSCOMBE_X = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]


def scatter_wide_data(root, stem, which="dose"):
    """Wide form (xcol/ycol). 'dose' = strong linear + fan-shaped noise;
    'anscombe1'..'anscombe4' expose the classic quartet."""
    rng = _rng("spw:" + stem)
    if which == "dose":
        dose = np.sort(rng.uniform(0, 10, 60))
        resp = 1.8 * dose + 2.0 + rng.normal(0, 0.3 + 0.3 * dose)
        _write(pl.DataFrame({"dose": dose, "response": resp}), root, stem, ".mean")
    else:
        ys = {
            "anscombe1": [
                8.04,
                6.95,
                7.58,
                8.81,
                8.33,
                9.96,
                7.24,
                4.26,
                10.84,
                4.82,
                5.68,
            ],
            "anscombe2": [
                9.14,
                8.14,
                8.74,
                8.77,
                9.26,
                8.10,
                6.13,
                3.10,
                9.13,
                7.26,
                4.74,
            ],
            "anscombe3": [
                7.46,
                6.77,
                12.74,
                7.11,
                7.81,
                8.84,
                6.08,
                5.39,
                8.15,
                6.42,
                5.73,
            ],
        }[which]
        _write(pl.DataFrame({"xcol": _ANSCOMBE_X, "ycol": ys}), root, stem, ".mean")


def scatter_long_data(root, stem, nexp=3, kind="linear"):
    """Long form (exp,x,y): one series per experiment, shaped so best-fit
    variations have real structure to fit. x>0 so log/exp are defined."""
    rng = _rng("spl:" + stem)
    rows = {"exp": [], "x": [], "y": []}
    for e in range(nexp):
        xs = np.linspace(1, 10, 30)
        if kind == "linear":
            ys = (e + 1) * xs + rng.normal(0, 1.0, 30)
        elif kind == "quadratic":
            ys = 0.5 * xs**2 + (e + 1) + rng.normal(0, 1.0, 30)
        elif kind == "cubic":
            ys = 0.1 * xs**3 - xs + (e + 1) + rng.normal(0, 1.0, 30)
        elif kind == "log":
            ys = 3 * np.log(xs) + e + rng.normal(0, 0.3, 30)
        elif kind == "exp":
            ys = np.exp(0.3 * xs) + e + rng.normal(0, 0.5, 30)
        else:
            ys = (e + 1) * xs
        rows["exp"] += [e] * 30
        rows["x"] += xs.tolist()
        rows["y"] += ys.tolist()
    _write(pl.DataFrame(rows), root, stem, ".mean")


# ---------------------------------------------------------------------------
# Histograms
# ---------------------------------------------------------------------------
def histogram_data(root, stem, family="beta"):
    """Named distribution families -- each visually distinct.
    'beta' = {u-shaped, bell, j-shaped, uniform}; 'mixed' = {lognormal, bimodal}."""
    rng = _rng("hg:" + stem)
    m = 800
    if family == "beta":
        data = {
            "u_shaped": rng.beta(0.5, 0.5, m),
            "bell": rng.beta(5.0, 5.0, m),
            "j_shaped": rng.beta(2.0, 5.0, m),
            "uniform": rng.beta(1.0, 1.0, m),
        }
    else:
        half = m // 2
        data = {
            "lognormal": rng.lognormal(0.0, 0.6, m),
            "bimodal": np.concatenate(
                [rng.normal(-2, 0.5, half), rng.normal(2.5, 0.8, half)]
            ),
        }
    _write(pl.DataFrame(data), root, stem, ".mean")


# ---------------------------------------------------------------------------
# Networks
# ---------------------------------------------------------------------------
def network_graphml(root, stem, kind="scale_free", directed=False):
    """Scale-free graph with clear hubs (kind='scale_free') or a balanced tree
    (kind='tree', valid for bfs/graphviz root-finding layouts)."""
    rng = _rng("nw:" + stem)
    if kind == "tree":
        G = nx.balanced_tree(2, 3, create_using=nx.DiGraph if directed else nx.Graph)
    else:
        G = nx.barabasi_albert_graph(30, 2, seed=SEED)
        if directed:
            G = G.to_directed()
    for node in G.nodes():
        G.nodes[node]["degree"] = int(G.degree[node])
        G.nodes[node]["group"] = int(G.degree[node]) % 4
    for u, v in G.edges():
        G.edges[u, v]["weight"] = float(G.degree[u] * G.degree[v])
    root.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, root / f"{stem}.graphml")


__all__ = [
    "summary_data",
    "timeseries_data",
    "heatmap_numeric_data",
    "heatmap_grid_data",
    "confusion_data",
    "scatter_wide_data",
    "scatter_long_data",
    "histogram_data",
    "network_graphml",
]

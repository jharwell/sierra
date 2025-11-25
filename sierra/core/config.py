# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Contains all SIERRA hard-coded configuration in one place.
"""

# Core packages
import logging
import typing as tp
import packaging
import os
import ssl
import contextlib
import certifi

# 3rd party packages
import holoviews as hv

# Project packages
from sierra.core import types


################################################################################
# Holoviews Configuration
################################################################################
def bokeh_init() -> None:
    # Only needed when hv backend is bokeh
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def mpl_init() -> None:
    # Turn off MPL messages when the log level is set to DEBUG or
    # higher. Otherwise you get HUNDREDS. Must be before import to suppress
    # messages which occur during import.
    #
    # Only needed when the hv backend is mpl
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    import matplotlib as mpl  # noqa: PLC0415

    mpl.rcParams["lines.linewidth"] = 3
    mpl.rcParams["lines.markersize"] = 10
    mpl.rcParams["figure.max_open_warning"] = 1000
    mpl.rcParams["axes.formatter.limits"] = (-4, 4)

    # Use latex to render all math, so that it matches how the math renders in
    # papers.
    mpl.rcParams["text.usetex"] = True

    # Set MPL backend (headless for non-interactive use). Must be BEFORE
    # importing pyplot reduce import loading time.
    mpl.use("Agg")

    import matplotlib.pyplot as plt  # noqa: PLC0415

    # Set MPL style
    plt.style.use("seaborn-v0_8-colorblind")


def hv_ssl_init() -> None:
    """Initialize SSL properly to ensure fork()ing works.

    This should NOT be necessary, but it is until holoviews/other packages fix
    this.

    2025-11-24 [JRH]: This is ABSOLUTELY CRUCIAL to avoid SSL related errors in
    the tornado package which hv uses.  By forcing initialization of SSL in the
    main process before any forking happens, we (apparently) avoid memory
    corruption which can happen otherwise.
    """

    # Disable SSL verification globally before any forks
    os.environ["PYTHONHTTPSVERIFY"] = "0"
    os.environ["SSL_CERT_FILE"] = certifi.where()

    # Create SSL context in parent to "warm it up"
    with contextlib.suppress(BaseException):
        ssl.create_default_context()

    # Override default context creator
    ssl._create_default_https_context = ssl._create_unverified_context

    # Pre-import tornado to initialize its SSL before fork
    with contextlib.suppress(BaseException):
        import tornado.netutil  # noqa: PLC0415


hv_ssl_init()
bokeh_init()
mpl_init()

hv.core.cache_size = 10
hv.config.cache_size = 0
hv.config.warning_level = 0

################################################################################
# General Configuration
################################################################################
PICKLE_EXT = ".pkl"
PICKLE_LEAF = "exp_def" + PICKLE_EXT
RANDOM_SEEDS_LEAF = "seeds" + PICKLE_EXT

GRAPHS = {
    "static_type": "png",
    "interactive_type": "html",
    "dpi": 100,
    "base_size": 10.0,  # inches,
    "text_size_small": {
        "title": 24,
        "xyz_label": 18,
        "tick_label": 12,
        "legend_label": 18,
    },
    "text_size_large": {
        "title": 36,
        "xyz_label": 24,
        "tick_label": 24,
        "legend_label": 32,
    },
}


# These are the file extensions that files read/written by a given storage
# plugin should have. Once processed by SIERRA they are written out as CSV files
# with new extensions contextualizing them.
STORAGE_EXT: types.StrDict = {"csv": ".csv", "arrow": ".arrow"}

STATS: dict[str, types.StatisticsSpec] = {
    # The default for averaging
    "mean": types.StatisticsSpec({"mean": ".mean"}),
    # For calculating 95% confidence intervals
    "conf95": types.StatisticsSpec({"stddev": ".stddev"}),
    # For calculating box and whisker plots
    "bw": types.StatisticsSpec(
        {
            "median": ".median",
            "q1": ".q1",
            "q3": ".q3",
            "whislo": ".whislo",
            "whishi": ".whishi",
            "cilo": ".cilo",
            "cihi": ".cihi",
        }
    ),
}

MODELS_EXT: types.StrDict = {"model": ".model", "legend": ".legend"}

ARGOS: dict[str, tp.Any] = {
    "frames_leaf": "frames",
    "physics_iter_per_tick": 10,
    "min_version": packaging.version.parse("3.0.0-beta53"),
    "launch_cmd": "argos3",
    "launch_file_ext": ".argos",
    "n_secs_per_run": 5000,  # seconds
    "n_ticks_per_sec": 5,
    # These are the cell sizes for use with the spatial_hash method for the
    # dynamics2D engine. Since that method should only be used with lots of
    # robots (per the docs), we set a cell a little larger than the robot.
    "spatial_hash2D": {
        "foot-bot": 0.5,
        "e-puck": 0.5,
    },
}

RENDERING = {
    "argos": {
        "frames_leaf": ARGOS["frames_leaf"],
    },
    "format": ".mp4",
}


ROS: types.SimpleDict = {
    "launch_cmd": "roslaunch",
    "launch_file_ext": ".launch",
    "param_file_ext": ".params",
    "n_ticks_per_sec": 5,
    "n_secs_per_run": 1000,  # seconds
    "port_base": 11235,
    "inter_run_pause": 60,  # seconds
}

# 2025-06-23 [JRH]: These are empirically determined minimum values which
# generally result in all data being processed in stage {3,4}. Change with
# extreme caution.
GATHER_WORKER_RETRIES = 3
PROCESS_WORKER_RETRIES = 3

PROJECT_YAML = types.YAMLConfigFileSpec(
    main="main.yaml",
    graphs="graphs.yaml",
    collate="collate.yaml",
    controllers="controllers.yaml",
    models="models.yaml",
)

GAZEBO = {
    "launch_cmd": "gazebo",
    "min_version": "11.0.0",
    "physics_iter_per_tick": 1000,
}

GNU_PARALLEL: types.StrDict = {"cmdfile_stem": "commands", "cmdfile_ext": ".txt"}

ENGINE = {"ping_timeout": 10}  # seconds

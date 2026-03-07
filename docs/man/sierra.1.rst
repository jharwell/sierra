.. SPDX-License-Identifier: MIT

.. _man/sierra:

======
sierra
======

Synopsis
========

.. code-block:: none

   sierra --sierra-root DIR --project NAME --controller CATEGORY.NAME
          --scenario NAME --expdef-template FILE --batch-criteria CRITERIA
          [--pipeline STAGES] [OPTIONS]

----------
sierra(1)
----------

:Date: |today|
:Version: |release|
:Manual section: 1
:Manual group: SIERRA


Description
===========

SIERRA is a command-line framework for running large-scale, reproducible
computational experiments. It automates the full experimental workflow:
generating experiment inputs, executing experiments across heterogeneous
computing environments, collecting results, processing data, and producing
analysis artifacts such as plots, videos, and comparative summaries.

Experiments are defined by an *experiment template* and a *batch criteria*
that sweeps one or more independent variables. SIERRA instantiates the
criteria against the template to produce a :term:`Batch Experiment`, then
runs it through a configurable pipeline.

Pipeline Stages
===============

Stages are selected with ``--pipeline`` (default: ``1 2 3 4``).

``1``
   **Generate** — transforms the template and batch criteria into individual
   experiment input files under ``--sierra-root``.

``2``
   **Execute** — runs the generated inputs using the configured engine and
   execution environment.

``3``
   **Post-process** — reduces raw outputs across runs within each experiment
   into processed statistical files.

``4``
   **Generate products** — produces graphs, videos, and other deliverables
   from processed files.

``5``
   **Compare** — overlays products from multiple batch experiments. Not
   included in the default pipeline; invoke explicitly with
   ``--pipeline 5``.

Options
=======

Option parsing follows standard conventions. If an option is given more than
once, the last occurrence wins. If both short and long forms are given with
different values, the short form wins.  Options may also be placed in an rcfile
(see :envvar:`SIERRA_RCFILE`).  Required options and short-form options cannot
be placed in the rcfile.

Bootstrap Options
-----------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_bootstrap
   :prog: sierra-cli

Multi-stage Options
-------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_multistage

Stage 1: Generating Experiments
--------------------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage1

Stage 2: Running Experiments
-----------------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage2

Stage 3: Processing Experiment Results
---------------------------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage3

Stage 4: Product Generation
----------------------------

No additional options. Product generation is configured via the engine and
processor plugins selected at stages 1–3.

Stage 5: Comparing Controllers
-------------------------------

No additional options. Comparison targets are determined by the batch
criteria and controller arguments supplied at stage 1.

Plugin Options
--------------

Each engine, execution environment, and project plugin may define additional
options. See the documentation for the relevant plugin.

Core Environment Variables
==========================

.. envvar:: SIERRA_PLUGIN_PATH

   Colon-separated list of directories searched recursively for plugins.
   Do not also add these directories to :envvar:`PYTHONPATH`; SIERRA
   manages ``sys.path`` internally. Used in stages 1–5.

.. envvar:: SIERRA_RCFILE

   Path to a file containing additional command-line arguments, one per
   line. Equivalent to passing ``--rcfile``. Priority order:

   1. ``--rcfile`` flag
   2. :envvar:`SIERRA_RCFILE`
   3. ``~/.sierrarc``

   Short-form and required arguments cannot appear in the rcfile.

.. envvar:: SIERRA_ARCH

   Suffix appended to engine executable names, enabling per-architecture
   binaries on HPC clusters with heterogeneous nodes. If set to ``avx2``,
   SIERRA looks for ``foobar-avx2`` instead of ``foobar``. Not all engines
   use this variable.

.. envvar:: SIERRA_NODEFILE

   Path to a file of hostnames suitable for passing to :program:`parallel`
   via ``--sshloginfile``. Required when running distributed experiments if
   ``--nodefile`` is not passed directly.

.. envvar:: PYTHONPATH

   Standard Python path. Used to locate project plugins.

Files
=====

``~/.sierrarc``
   Default rcfile location. Contains additional command-line arguments,
   one per line. See :envvar:`SIERRA_RCFILE`.

``--sierra-root``
   Root of the runtime directory tree. All experiment inputs, outputs,
   statistics, and products are written under this path, organized as::

      <sierra-root>/<project>/<controller>/<scenario>/<batch-criteria>/

Exit Status
===========

SIERRA will always return 0, unless it crashes with an exception or a failed
assert, in which case the return code will be non-zero.

Errors should be reported to :xref:`SIERRA_GITHUB`.

See Also
========

Full documentation: :xref:`SIERRA_DOCS`

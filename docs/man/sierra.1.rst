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
criteria against the template to produce a batch experiment, then runs it
through a configurable pipeline.

Concepts
========

The following terms are used throughout this page and in SIERRA's option
help. Fuller treatments are in the online documentation (see *See Also*).

Batch experiment
   The full set of individual experiments produced by applying a batch
   criteria to an experiment template. Each distinct value of the swept
   variable(s) yields one experiment; each experiment is run some number of
   times (``--n-runs``).

Experiment template
   The input file (``--expdef-template``) describing a single experiment,
   into which SIERRA substitutes batch-criteria values to generate concrete
   experiment inputs.

Batch criteria
   The specification (``--batch-criteria``) of one or more independent
   variables to sweep, and the values they take. Determines how many
   experiments the batch contains.

Engine
   The plugin (``--engine``) that knows how to execute one experiment — for
   example a simulator or a real-robot platform. Selected at stage 1 and
   used at stage 2.

Execution environment
   The platform on which experiments run (local machine, HPC cluster, etc.),
   which governs how work is parallelized and dispatched at stage 2.

Run-time directory tree
   The on-disk layout SIERRA writes under ``--sierra-root``; see *Files*.

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
be placed in the rcfile. All options below are for the SIERRA core only; see
plugin docs pages for the options for individual plugins.

Bootstrap Options
-----------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_bootstrap
   :prog: sierra

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

SIERRA returns 0 on success. If it terminates early due to an unhandled
exception or a failed assertion, the return code is non-zero.

Report bugs at :xref:`SIERRA_GITHUB`.

See Also
========

:program:`parallel`\(1)

Full documentation, tutorials, and plugin reference: :xref:`SIERRA_DOCS`

Sample project referenced throughout the docs: :xref:`SIERRA_SAMPLE_PROJECT`

.. SPDX-License-Identifier: MIT

.. _user-guide/running-experiments:

====================
Running Experiments
====================

This page covers common invocation patterns and workflows. For the full
description of every option, see :ref:`reference/cli`. For a conceptual
overview of what each pipeline stage does, see :ref:`concepts/pipeline`.

.. _user-guide/running-experiments/invocation:

Basic Invocation
================

A minimal ``sierra-cli`` invocation looks like this:

.. code-block:: bash

   sierra-cli                                        \
     --project        myproject                      \
     --engine         engine.argos                   \
     --expdef-template exp/template.argos            \
     --batch-criteria  population_size.1.16.C4       \
     --scenario        myScenario.10x10x1            \
     --controller      myCategory.myController

The bootstrap options (:ref:`--engine <src/reference/cli:sierra-cli---engine>`, :ref:`--execenv
<src/reference/cli:sierra-cli---execenv>`, :ref:`--expdef <src/reference/cli:sierra-cli---expdef>`, ``--storage``,
:ref:`--proc <src/reference/cli:sierra-cli---proc>`, ``--prod``) all have defaults and only need
to be specified when overriding them. The four options that change most often
between runs are :ref:`--batch-criteria <src/reference/cli:sierra-cli---batch-criteria>`,
``--scenario``, ``--controller``, and :ref:`--expdef-template
<src/reference/cli:sierra-cli---expdef-template>` — together they determine both the shape of the
batch and where outputs are stored under
:ref:`--sierra-root<src/reference/cli:sierra-cli---sierra-root>`. See
:ref:`concepts/run-time-tree` for the resulting directory layout.

.. _user-guide/running-experiments/batch-criteria:

Specifying Batch Criteria
=========================

:ref:`--batch-criteria <src/reference/cli:sierra-cli---batch-criteria>` accepts N
space-separated strings, each of the form ``<category>.<definition>``:

.. code-block:: bash

   # Univariate: one parameter swept across 5 experiments
   sierra-cli ... --batch-criteria population_size.Linear16.C5

   # Bivariate: two parameters producing a 5x4 grid of 20 experiments
   sierra-cli ... --batch-criteria population_size.Linear16.C5 max_speed.1.4.C4

   # Trivariate: 3 parameters producing a 2x4x6 grid of 48 experiments
   sierra-cli ... --batch-criteria comm_distance.1.2.C2 population_size.Linear8.C4 max_speed.1.6.C6

   # Built-in: 8 Monte Carlo replicates with no parameter variation
   sierra-cli ... --batch-criteria builtin.MonteCarlo.C8

``<category>`` is a Python module name from your project's
``variables/`` directory, or ``sierra.core.variables`` for built-ins.
``<definition>`` is a string whose format is defined by that module and
parsed by its ``factory()`` function.

N criteria produce an N-dimensional Cartesian product of experiments.
Stage 4 generates line graphs for univariate batches and heatmaps for
bivariate; graph generation beyond 2 dimensions is not yet supported.
See :ref:`concepts/batch-criteria` for how experiments are named and
structured on disk, and :ref:`tutorials/project/new-bc` to create a new
criteria.

.. _user-guide/running-experiments/pipeline:

Running a Subset of Stages
===========================

By default SIERRA runs stages 1–4. The most common reason to run a
subset is to regenerate graphs after adjusting graph configuration,
without re-running experiments:

.. code-block:: bash

   sierra-cli ... --pipeline 3 4

Or to re-run stage 2 only, after fixing a crashed experiment:

.. code-block:: bash

   sierra-cli ... --pipeline 2

Stage N generally requires stage N-1 to have completed successfully — running
stage 4 against missing stage 3 outputs will crash or produce empty
graphs. Stages 3 and 4 are idempotent and freely overwrite their own outputs;
stage 2 is not. See :ref:`--pipeline <src/reference/cli:sierra-cli---pipeline>` for the full
option reference.

.. _user-guide/running-experiments/partial:

Re-Running Part of a Batch
===========================

To process only a contiguous slice of experiments from a batch, use
:ref:`--exp-range <src/reference/cli:sierra-cli---exp-range>`. This is useful after a partial HPC
failure, or when iterating on a single experiment without waiting for the
full batch:

.. code-block:: bash

   # Re-run only experiments 2 and 3 (0-based) from a batch of 5
   sierra-cli ... --pipeline 2 --exp-range 2:3

The same range applies to stages 3 and 4 if passed there — only the
specified experiments will be processed or graphed.

.. _user-guide/running-experiments/resume:

Resuming After a Crash
=======================

If stage 2 is killed partway through (e.g. by an HPC time limit), pass
:ref:`--exec-resume<src/reference/cli:sierra-cli---exec-resume>` with the same arguments on the
next invocation:

.. code-block:: bash

   sierra-cli ... --pipeline 2 --exec-resume

SIERRA skips any experimental run whose output directory already exists and runs
only those that did not complete. Without
:ref:`--exec-resume<src/reference/cli:sierra-cli---exec-resume>`, re-running stage 2 against an
existing batch results in redundant work.

.. _user-guide/running-experiments/overwrite:

Starting a Batch Over
=====================

To discard and regenerate an existing batch experiment entirely, pass
:ref:`--exp-overwrite <src/reference/cli:sierra-cli---exp-overwrite>`:

.. code-block:: bash

   sierra-cli ... --exp-overwrite

.. warning::

   This deletes stage 1 inputs and regenerates them from scratch. Any existing
   stage 2 outputs will no longer correspond to the inputs that produced
   them. Use only when you intend to re-run the full batch. See
   :ref:`reference/philosophy` for why SIERRA requires explicit permission for
   this.

.. _user-guide/running-experiments/rcfile:

Factoring Out Common Options
============================

Invocations grow long quickly when options are shared across many runs.  Put
stable options in an rcfile rather than repeating them:

.. code-block:: text

   # ~/.sierrarc
   --project=myproject
   --engine=engine.argos
   --execenv=hpc.local
   --expdef=expdef.xml
   --sierra-root=/data/experiments

.. code-block:: bash

   # Invocation now only needs the per-run arguments
   sierra-cli                                        \
     --batch-criteria population_size.1.16.C4        \
     --scenario       myScenario.10x10x1             \
     --controller     myCategory.myController        \
     --expdef-template exp/template.argos

Command line arguments override rcfile arguments. See :ref:`--rcfile
<src/reference/cli:sierra-cli---rcfile>` and :envvar:`SIERRA_RCFILE` for the full priority order
and non-default rcfile path options.

.. note::

   Shortform aliases (:ref:`-p <src/reference/cli:sierra-cli--p>`, :ref:`-e <src/reference/cli:sierra-cli--e>`,
   :ref:`-x <src/reference/cli:sierra-cli--x>`, :ref:`-s <src/reference/cli:sierra-cli--s>`) cannot be used inside
   an rcfile. Only longform :ref:`--option=value<src/reference/cli:sierra-cli---option=value>` syntax is supported.

.. _user-guide/running-experiments/parallelism:

Tuning Resource Usage
=====================

On machines with many cores or limited memory, two options control how
aggressively SIERRA uses resources during stages 3 and 4:

- :ref:`--processing-parallelism <src/reference/cli:sierra-cli---processing-parallelism>` — number
  of worker processes for results processing and graph generation. On I/O-bound
  systems, increasing this above the CPU count can improve throughput.

- :ref:`--processing-mem-limit <src/reference/cli:sierra-cli---processing-mem-limit>` — caps
  memory usage as a percentage of total available memory. Useful on shared
  machines.

For stage 2, parallelism is determined by the ``--execenv`` plugin.  See
:ref:`plugins/execenv/index` for per-environment details.

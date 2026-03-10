.. _concepts/batch-criteria:

==============
Batch Criteria
==============

A batch criteria is an experimental variable — an axis of the parameter space
your experiment explores. It defines a *range* of modifications to an experiment
template (:ref:`--expdef-template <src/reference/cli:sierra---expdef-template>`), one per
experiment in the batch, in parameter space terms. In implementation terms, this
can translate to multiple changes to the template file, which makes SIERRA
incredibly powerful how you can define experiments.  The full set of experiments
produced is a :term:`Batch Experiment`.

For example, if you want to measure how swarm behavior changes as
population increases, your batch criteria would define a range of
population sizes. SIERRA applies each size in turn to the template to
produce one experiment per size.

Batch criteria can be combined to vary multiple parameters simultaneously. N
criteria produce an N-dimensional Cartesian product: M×N experiments for two
criteria of cardinality M and N, M×N×P for three, and so on. See
:ref:`user-guide/running-experiments/batch-criteria` and for command-line
syntax.

.. _concepts/batch-criteria/directory-structure:

Directory Structure
===================

Each experiment in a batch gets its own subdirectory, named by its
position in the criteria space. For a univariate batch of cardinality 5:

.. code-block:: text

   <batch-root>/
   ├── exp-inputs/
   │   ├── c1-exp0/
   │   ├── c1-exp1/
   │   ├── c1-exp2/
   │   ├── c1-exp3/
   │   └── c1-exp4/
   └── exp-outputs/
       ├── c1-exp0/
       └── ...

For a bivariate batch combining two criteria of cardinality 3 and 2,
experiment names encode both dimensions using ``+`` as a separator:

.. code-block:: text

   <batch-root>/
   ├── exp-inputs/
   │   ├── c1-exp0+c2-exp0/
   │   ├── c1-exp0+c2-exp1/
   │   ├── c1-exp1+c2-exp0/
   │   ├── c1-exp1+c2-exp1/
   │   ├── c1-exp2+c2-exp0/
   │   └── c1-exp2+c2-exp1/
   └── exp-outputs/
       └── ...

The same pattern extends to higher-dimensional criteria:
``c1-exp0+c2-exp0+c3-exp0``, and so on.

.. _concepts/batch-criteria/graphs:

Graph Types
===========

The dimensionality of the batch determines what stage 4 can produce:

- **Univariate** — line graphs, with the varied parameter on the X axis
  and the quantity of interest on the Y.

- **Bivariate** — heatmaps with one criteria on each axis and the
  quantity of interest on the Z, or line graph "slices" along either
  axis.

- **Higher-dimensional** — graph generation beyond 2 dimensions is not
  yet supported. See :ref:`roadmap`.

.. _concepts/batch-criteria/sources:

Where Batch Criteria Come From
===============================

The batch criteria available to you depend on what is loaded:

- **Built-in** — :ref:`concepts/batch-criteria/montecarlo` is always
  available from ``sierra.core.variables``.

- **Engine-specific** — some engines define criteria that any project can
  use. See the documentation for your selected :term:`Engine`.

- **Project-specific** — your :term:`Project` can define its own
  criteria under ``<project>/variables/``. See
  :ref:`tutorials/project/new-bc` to create one.

.. _concepts/batch-criteria/montecarlo:

Monte Carlo
===========

An empty batch criteria that does not modify the experiment template at
all. Its sole purpose is to produce a batch of the desired cardinality,
where experiments differ only in their random seed. Useful for measuring
variance in stochastic systems, or for debugging with a minimal batch.

Cmdline syntax: ``builtin.MonteCarlo.C{cardinality}``

Examples:

- ``builtin.MonteCarlo.C1`` — one experiment (useful for debugging)
- ``builtin.MonteCarlo.C16`` — 16 Monte Carlo replicates

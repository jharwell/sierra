.. _concepts/batch-criteria:

==============
Batch Criteria
==============

Batch criteria are *variables* you wish to use with SIERRA to measure their
effect on system behavior. From the perspective of experimental design, a batch
criteria is an axis of the parameter space the experiment is exploring. For
example, if your experiment has a single variable, such as :ref:`# robots
<plugins/engine/argos/bc/population-size>`), you would use a univariate batch
criteria like this one to create it. If you want to investigate two variables
simultaneously, such as :ref:`# robots
<plugins/engine/argos/bc/population-size>` and another batch criteria such as
one defining sensor and actuator noise to apply to the robots), you would use a
bivariate batch criteria to create it.

.. IMPORTANT:: SIERRA supports N-dimensional batch criteria.

Univariate batch criteria have cardinality=1, and so the graphs produced
by them are (usually) linegraphs with a numerical representation of the
range for the variable on the X axis, and some other quantity of interest
on the Y. Bivariate batch criteria have cardinality=2, and so the graphs
produced by them might be heatmaps with the first variable in the criteria
on the X axis, the second on the Y, and the quantity of interest on
the Z. Or they could be linegraphs, with a "slice" along the axis of
interest. You can imagine similar cases for higher cardinality criteria.

Batch criteria define a *range* of sets changes for one or more elements
in a template file (passed to SIERRA with ``--expdef-template``). For each
element in the range, the changes are applied to the template file to
define :term:`Experiments<Experiment>`. The set of defined experiments is
called a :term:`Batch Experiment`.

The batch criteria you can use depends on:

- The :term:`Project` you have loaded, as each project can define their
  own batch criteria (see :ref:`tutorials/project/new-bc`).

- The :term:`Engine` you have selected, as some engines define basic batch
  criteria that any project/experiment can use.

In addition, SIERRA has a few general purpose batch criteria which are always
available:

- :ref:`concepts/batch-criteria/montecarlo`

.. _concepts/batch-criteria/montecarlo:

Monte Carlo
===========

An "empty" batch criteria which doesn't modify the input ``--expdef-template``
file at all, and serves solely to create an :term:`Batch Experiment` of the
desired cardinality. Useful in debugging/when all you care about varying is the
random seed.


Cmdline Syntax
--------------

``builtin.MonteCarlo.C{cardinality}``

- ``cardinality`` - Specify how many experiments to generate in the batch. If
  debugging something, this should probably be 1. If you're doing "regular"
  MonteCarlo analysis, then should be >> 1.

Examples
--------

- ``builtin.MonteCarlo.C1``: Generate 1 experiment.
- ``builtin.MonteCarlo.C10``: Generate 10 experiments.

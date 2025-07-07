.. _usage/bc:

==============
Batch Criteria
==============

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you.  The following batch criteria are defined which can be used with any
:term:`Project`.

- :ref:`usage/bc/montecarlo`

.. _usage/bc/montecarlo:

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

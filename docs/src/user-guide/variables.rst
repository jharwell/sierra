.. _usage/vars:

=============================
Configurable SIERRA Variables
=============================

Non-:term:`Batch Criteria` variables which you can use to configure
simulations. All batch criteria are variables, but not all variables are batch
criteria.

- :ref:`Experiment Setup <usage/vars/expsetup>`

.. _usage/vars/expsetup:

Experiment Setup
================

Configure :term:`Experiment` time: length, controller cadence (:term:`Tick`
duration/timestep), and how many datapoints to capture per :term:`Experimental
Run`.

.. _usage/vars/expsetup/cmdline:

Cmdline Syntax
--------------

``T{duration}[.K{ticks_per_sec}]``

- ``duration`` - Duration of timesteps in *seconds* (not timesteps/ticks).

- ``ticks_per_sec`` - How many times each controller will be run per
  second. Well, controllers can actually run more often than this if they want,
  but this should be how many times/sec they output data, so that the #
  datapoints gathered can (roughly) be calculated as ``duration *
  ticks_per_sec`` for the purpose of generating :term:`products <Product>`.

``duration`` must always be specified, but ``ticks_per_sec`` is optional.

.. IMPORTANT:: All :Term:`Experimental Runs <Experimental Run>` *must* respect
               these parameters or some of the finer points of SIERRA
               functionality won't work at best, and BAD things will happen at
               worst. Probably.

Examples
--------

- ``exp_setup.T1000``: Experimental run will be 1,000 seconds long and have
  1,000*5=5,000 timesteps, with default (50) # datapoints.

- ``exp_setup.T10000.K10``: Experimental run will be 10,000 seconds long, and
  have 10,000*10=100,000 timesteps with default (50) # datapoints.

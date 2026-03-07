.. _user-guide/vars:

=============================
Configurable SIERRA Variables
=============================

These are non-:term:`Batch Criteria` variables you can use to configure
simulations. The distinction matters: batch criteria define the axes of
variation *across* a batch experiment — each value of a criterion generates a
separate experiment. Variables, by contrast, apply uniformly to every
experiment in the batch. All batch criteria are variables, but not all
variables are batch criteria. See :ref:`usage/bc` for the batch criteria
reference.


- :ref:`Experiment Setup <usage/vars/expsetup>`

.. _usage/vars/expsetup:

Experiment Setup
================

Configures :term:`Experiment` duration, controller cadence (:term:`Tick`
duration/timestep), and the number of datapoints captured per
:term:`Experimental Run`. Supported by the ARGoS and ROS1-based engines; if
your engine does not support it, it has no effect.

.. _usage/vars/expsetup/cmdline:

Cmdline Syntax
--------------

``exp_setup.T{duration}[.K{ticks_per_sec}]``

- ``duration`` — Duration of the experiment in *seconds* (not
  timesteps/ticks).

- ``ticks_per_sec`` — How many times per second each controller outputs data.
  Controllers may execute more frequently internally, but SIERRA uses this
  value to determine how many datapoints to expect per run. The number of
  captured datapoints is approximately ``duration * ticks_per_sec``.

``duration`` must always be specified. ``ticks_per_sec`` is optional.

.. IMPORTANT::

   All :term:`Experimental Runs <Experimental Run>` must produce the expected
   number of datapoints. If a run produces fewer, SIERRA's graph generation
   will produce incorrect results because it computes axis ranges and
   statistics from the expected count.

Examples
--------

- ``exp_setup.T1000``: Run is 1,000 seconds long with the default 5
  ticks/sec, giving 1,000 × 5 = 5,000 timesteps, assuming the engine default
  is capturing one datapoint pe 100 timesteps, giving approximately 50 datapoints per run.

- ``exp_setup.T10000.K10``: Run is 10,000 seconds long with 10 ticks/sec,
  giving 10,000 × 10 = 100,000 timesteps and approximately 50 datapoints
  (same default capture interval of one per 100 timesteps).

.. NOTE:: If you are writing a new engine plugin and your engine models
   experiment time in terms of duration and controller cadence, adopting
   ``--exp-setup`` gives users a consistent interface across engines. See
   :ref:`tutorials/plugin/engine` for details.

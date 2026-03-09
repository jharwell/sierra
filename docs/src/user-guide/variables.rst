.. _user-guide/vars:

=============================
Configurable SIERRA Variables
=============================

Variables configure experiments uniformly across an entire batch — every
experiment in the batch gets the same value. This distinguishes them from
:term:`Batch Criteria`, which define axes of variation that produce *different*
experiments. For the conceptual distinction, see
:ref:`concepts/exp-design/variables`.

- :ref:`Experiment Setup <user-guide/vars/expsetup>`

.. _user-guide/vars/expsetup:

Experiment Setup
================

Configures :term:`Experiment` duration, controller cadence (:term:`Tick`
duration/timestep), and the number of datapoints captured per
:term:`Experimental Run`. Supported by the ARGoS and ROS1-based engines; if
your engine does not support it, it has no effect.

.. _user-guide/vars/expsetup/cmdline:

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
  is capturing one datapoint per 100 timesteps, giving approximately 50
  datapoints per run.

- ``exp_setup.T10000.K10``: Run is 10,000 seconds long with 10 ticks/sec,
  giving 10,000 × 10 = 100,000 timesteps and approximately 50 datapoints
  (same default capture interval of one per 100 timesteps).

.. NOTE:: If you are writing a new engine plugin and your engine models
   experiment time in terms of duration and controller cadence, adopting
   ``--exp-setup`` gives users a consistent interface across engines. See
   :ref:`tutorials/plugins/engine` for details.

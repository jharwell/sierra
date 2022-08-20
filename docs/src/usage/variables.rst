.. _ln-sierra-usage-vars:

=============================
Configurable SIERRA Variables
=============================

Non-:term:`Batch Criteria` variables which you can use to configure
simulations. All batch criteria are variables, but not all variables are batch
criteria.

- :ref:`Experiment Setup <ln-sierra-vars-expsetup>`

.. _ln-sierra-vars-expsetup:

Experiment Setup
================

Configure :term:`Experiment` time: length, controller cadence (:term:`Tick`
duration/timestep), and how many datapoints to capture per :term:`Experimental
Run`.

.. _ln-sierra-vars-expsetup-cmdline:

Cmdline Syntax
--------------

``T{duration}[.K{ticks_per_sec}][.N{n_datapoints}``

- ``duration`` - Duration of timesteps in `seconds` (not timesteps).

- ``ticks_per_sec`` - How many times each controller will be run per second.

- ``n_datapoints`` - # datapoints per :term:`Experimental Run` to be captured;
  the capture interval (if configurable) should be adjusted in
  :term:`Project`\-derived class from the platform "Experiment setup class"
  (e.g., :class:`sierra.plugins.platform.argos.variables.exp_setup.ExpSetup` for
  :term:`ARGoS`).

Examples
--------

- ``exp_setup.T1000``: Experimental run will be 1,000 seconds long and have
  1,000*5=5,000 timesteps, with default (50) # datapoints.

- ``exp_setup.T2000.N100``: Experimental run will be 2,000 seconds long and have
  2,000*5=10,000 timesteps, with 100 datapoints (1 every 20 seconds/100
  timesteps).

- ``exp_setup.T10000.K10``: Experimental run will be 10,000 seconds long, and
  have 10,000*10=100,000 timesteps with default (50) # datapoints.

- ``exp_setup.T10000.K10.N100``: Experimental run will be 10,000 seconds long,
  and have 10,000*10=100,000 timesteps, with 100 datapoints (one every 100
  seconds/1,000 timesteps).

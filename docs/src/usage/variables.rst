.. _ln-vars:

Externally Configurable SIERRA Variables
========================================

Non-:term:`Batch Criteria` variables which you can use to configure
simulations. All batch criteria are variables, but not all variables are batch
criteria.

- :ref:`Time Setup <ln-vars-ts>`

.. _ln-vars-ts:

Time Setup
----------

Configure simulation time: length, controller cadence, and how many datapoints
to capture per simulation.

.. _ln-vars-ts-cmdline:

Cmdline Syntax
^^^^^^^^^^^^^^

``T{duration}[.K{ticks_per_sec}][.N{n_datapoints}``

- ``duration`` - Duration of simulation in `seconds` (not timesteps).

- ``ticks_per_sec`` - How many times each controller will be run per second of
  simulated time.

- ``n_datapoints`` - # datapoints per simulation, to be captured; the capture
  interval (if configurable) should be adjusted in the
  :class:`~sierra.core.variables.time_setup` derived class for the
  ``--project``.

Examples:

- ``time_setup.T1000``: Simulation will be 1,000 seconds long and have
  1,000*5=5,000 timesteps, with default (50) # datapoints.

- ``time_setup.T2000.N100``: Simulation will be 2,000 seconds long and have
  2,000*5=10,000 timesteps, with 100 datapoints (1 every 20 seconds/100
  timesteps).

- ``time_setup.T10000.K10``: Simulation will be 10,000 seconds long, and have
  10,000*10=100,000 timesteps with default (50) # datapoints.

- ``time_setup.T10000.K10.N100``: Simulation will be 10,000 seconds long, and
  have 10,000*10=100,000 timesteps, with 100 datapoints (one every 100
  seconds/1,000 timesteps).

.. _ln-vars:

Variables
=========

.. _ln-vars-ts:

Time Setup
----------

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

- ``T1000``: Simulation will be 1,000 seconds long and have 1,000*5=5,000
  timesteps, with default (50) # datapoints.

- ``T2000.N100``: Simulation will be 2,000 seconds long and have 2,000*5=10,000
  timesteps, with 100 datapoints (1 every 20 seconds/100 timesteps).

- ``T10000.K10``: Simulation will be 10,000 seconds long, and have
  10,000*10=100,000 timesteps with default (50) # datapoints.

- ``T10000.K10.N100``: Simulation will be 10,000 seconds long, and have
  10,000*10=100,000 timesteps, with 100 datapoints (one every 100 seconds/1,000
  timesteps).

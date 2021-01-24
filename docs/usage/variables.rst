.. _ln-vars:

Variables
=========

.. _ln-vars-ts:

Time Setup
----------

.. _ln-vars-ts-cmdline:

Cmdline Syntax
^^^^^^^^^^^^^^

``T{duration}[N{n_datapoints}``

- ``duration`` - Duration of simulation in `seconds` (not timesteps).

- ``n_datapoints`` - # datapoints per simulation, to be captured; the capture
  interval (if configurable) should be adjusted in the
  :class:`~core.variables.time_setup` derived class for the ``--project``.

Examples:

    ``T1000``: Simulation will be 1000 seconds long, default (50) # datapoints.
    ``T2000N100``: Simulation will be 2000 seconds long, 100 datapoints (1 every 20 seconds).

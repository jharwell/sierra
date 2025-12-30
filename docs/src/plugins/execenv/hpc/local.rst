.. _plugins/execenv/hpc/local:

Local HPC Plugin
================

This HPC environment can be selected via ``--execenv=hpc.local``.  This is the
default HPC environment in which SIERRA will run all :term:`Experimental Runs
<Experimental Run>` on the same computer from which it was launched using GNU
parallel.  The # simultaneous simulations will be determined by a number of
factors, including:

- ``--exec-jobs-per-node``

- The selected :term:`Engine`'s parallelism paradigm and its specific
  configuration.

- The # of cores on the machine.

This HPC environment supports both ``per-batch`` and ``per-exp`` parallelism
paradigms. If more simulations are requested than can be run in parallel, SIERRA
will start additional simulations as currently running simulations finish. No
additional configuration/environment variables are needed with this HPC
environment for use with SIERRA.

The following environmental variables are used in the local HPC environment:

.. list-table::
   :header-rows: 1

   * - Environment variable
     - SIERRA context

   * - :envvar:`PARALLEL`
     - Used to transfer environment variables into the GNU parallel
       environment.

   * - :envvar:`PARALLEL_SHELL`
     - Used to set the shell used by GNU parallel to execute all commands
       in. Overwritten by SIERRA to ``/bin/bash``.

   * - :envvar:`LD_LIBRARY_PATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.

   * - :envvar:`PYTHONPATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.

   * - :envvar:`PATH`
     - Exported by SIERRA via :envvar:`PARALLEL` to child GNU parallel
       processes. Can be undefined when SIERRA starts.

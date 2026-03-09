..
   Copyright 2026 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _arch/execution-model:

======================
SIERRA Execution Model
======================

During stage 2, SIERRA translates an abstract batch experiment into one or more
*cmdfiles* — plain text files where each line is a complete shell command for a
single :term:`Experimental Run`. GNU parallel reads these files and executes the
lines in them, up to the concurrency limit set by the execution environment.
The structure of those cmdfiles, and therefore the shape of parallelism, is
determined by the *parallelism paradigm* declared by the engine plugin.

Hook Structure
==============

Every cmdfile line is assembled in stage 1 from three ordered hook calls,
corresponding to the three interfaces in
:mod:`sierra.core.experiment.bindings`:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Hook
     - Purpose

   * - ``pre_*_cmds()``
     - Setup commands run before execution begins at the given scope. Used for
       launching background processes or daemons that should be running before
       any experimental run starts (e.g., ``roscore``, a visualisation daemon).

   * - ``exec_*_cmds()``
     - The command(s) that actually execute the work at the given scope. For a
       run, this is the simulator launch command or the robot controller startup
       command. For a batch or experiment, this is typically the GNU parallel
       invocation itself.

   * - ``post_*_cmds()``
     - Cleanup commands run after execution completes at the given scope. Used
       for stopping background processes, collecting remote outputs, or resetting
       shared state before the next unit of work begins.

All three hooks exist at each of the three scopes described below. The ``pre``
and ``post`` hooks are generated in **stage 1** and written into the cmdfile;
the ``exec`` hook is called in **stage 2** to actually invoke GNU parallel
(or equivalent) on the cmdfile.

Parallelism Paradigms
=====================

The paradigm controls the *granularity* at which cmdfiles are produced and
therefore the granularity at which parallelism is possible. The engine plugin
declares its paradigm via
:meth:`~sierra.core.experiment.bindings.IExpConfigurer.parallelism_paradigm`.

``per-batch``
-------------

A single cmdfile for the entire :term:`Batch Experiment`. Each line contains
the ``{pre, exec, post}`` commands for one :term:`Experimental Run`. GNU
parallel executes all lines across all experiments in the batch concurrently,
up to the limit set by the execution environment.

Implemented by
:class:`~sierra.core.experiment.bindings.IBatchShellCmdsGenerator`. The
``pre_batch_cmds()`` and ``post_batch_cmds()`` hooks bracket the entire batch;
``exec_batch_cmds()`` is the GNU parallel invocation that processes the
cmdfile.

Appropriate when:

- Your engine is a single-threaded simulator. There is no benefit to
  restricting parallelism to experiment boundaries; running all runs
  concurrently is fastest.

- You are submitting executable code directly to the scheduler (e.g., a
  Prefect flow) rather than running a job script that then invokes SIERRA.

- Limiting concurrent resource usage is not a concern.

``per-exp``
-----------

A separate cmdfile per :term:`Experiment`. Each line contains the ``{pre,
exec, post}`` commands for one :term:`Experimental Run` within that experiment.
Experiments run sequentially; runs within each experiment run in parallel up
to the execution environment's concurrency limit.

Implemented by
:class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`. The
``pre_exp_cmds()`` and ``post_exp_cmds()`` hooks bracket each experiment;
``exec_exp_cmds()`` is the GNU parallel invocation for that experiment's
cmdfile.

.. NOTE:: ``exec_exp_cmds()`` is only meaningful on execution environment
   plugins. When defined on an engine plugin, its return value is ignored —
   the execution environment is always responsible for the actual parallel
   dispatch.

Appropriate when:

- Your execution environment is a classic HPC scheduler (SLURM, PBS) that
  grants you exclusive control over a fixed set of nodes for the duration of
  your job. Running one experiment at a time lets you dedicate all allocated
  cores to it before moving to the next.

- Your engine is a multi-threaded simulator. Per-experiment parallelism lets
  you maximise threads per simulation instance — running one simulation with
  24 threads is more efficient than 24 single-threaded simulations when the
  workload per run is large.

- You need to limit concurrent resource usage for any other reason.

``per-run``
-----------

A separate cmdfile per :term:`Experimental Run`. Each cmdfile may contain
multiple lines — one per subprocess required by that run. Parallelism is
*within* a single run rather than across runs; runs themselves execute
sequentially.

Implemented by
:class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`. The
``pre_run_cmds()``, ``exec_run_cmds()``, and ``post_run_cmds()`` hooks each
receive a ``host`` argument identifying the machine the commands will run on,
which enables SIERRA to dispatch subprocesses to different nodes (e.g.,
individual robots) within a single run.

Appropriate when:

- Your engine targets real hardware. A single physical robot cannot
  participate in more than one experimental run simultaneously, so runs must
  be sequential. Each run requires one subprocess per robot, dispatched over
  SSH to each device in the nodefile.

Real-Robot Execution Topology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For real-robot engines, the execution topology during a single run is:

- **Host machine** — the machine SIERRA is invoked from. Acts as the ROS master
  (unless :ref:`--no-master-node<src/reference/cli:sierra-cli---no-master-node>` is
  passed). SIERRA coordinates the entire run from here.

- **Robot nodes** — each robot listed in the nodefile receives its controller
  subprocess via SSH, dispatched by GNU parallel using the ``host`` argument
  passed to each hook.

- **Inter-run pause** — after all subprocesses for a run complete, SIERRA waits
  :ref:`--exec-inter-run-pause<src/reference/cli:sierra-cli---exec-inter-run-pause>` seconds
  before starting the next run, giving time to physically reset robot positions
  and the environment.

How the Execution Environment Controls Concurrency
==================================================

The paradigm determines the *structure* of cmdfiles; the execution environment
determines *how many lines* from those cmdfiles execute simultaneously. The
relevant controls are:

- :ref:`--exec-jobs-per-node<src/reference/cli:sierra-cli---exec-jobs-per-node>` — explicit
  override of concurrent jobs per node.  This is the most direct control if you
  know how many things you want running at once.

- HPC scheduler parameters — for SLURM and PBS environments, SIERRA reads
  :envvar`SLURM_TASKS_PER_NODE` or :envvar:`PBS_NUM_PPN` to set concurrency
  automatically from the resources the scheduler has allocated. See
  :ref:`plugins/execenv` for the full variable list each environment reads.

- Available cores — for ``hpc.local``, SIERRA uses the number of cores on
  the invoking machine.

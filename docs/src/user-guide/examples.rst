.. _user-guide/examples:

================
Usage By Example
================

This page contains annotated ``sierra`` invocations to help you craft your
own. All examples use project plugins from the SIERRA sample project:
:xref:`SIERRA_SAMPLE_PROJECT`. See :doc:`../getting-started/trial` or
:doc:`../getting-started/setup` for how to set up that repository.

In all examples:

- ``$HOME/git/sierra-sample-project`` is cloned and on
  :envvar:`SIERRA_PLUGIN_PATH`
- ``$HOME/git/sierra-sample-project/projects`` contains the project plugins
- ``$HOME/git/mycode`` contains any C++ project code library

Paths in
:ref:`--expdef-template<src/reference/cli:sierra---expdef-template>` are
relative to the directory you invoke ``sierra`` from. All examples assume
invocation from ``$HOME/git/sierra-sample-project``. Adjust paths for your own
setup.

Important Notes:

- :ref:`--execenv=hpc.local<src/reference/cli:sierra---execenv>`
  ``=hpc-local`` runs experiments on the machine SIERRA is invoked from, using
  GNU parallel for concurrency. Despite the ``hpc`` prefix, no cluster is
  required — it is the right choice for laptops and workstations.

- ``--exp-setup`` is supported by the ARGoS and ROS1-based engines.  It is not
  universally required — check your engine's documentation before using it. See
  :ref:`user-guide/vars/expsetup` for details.

- When running with GNU parallel-based execution environments, SIERRA
  automatically forwards :envvar:`LD_LIBRARY_PATH`, :envvar:`PYTHONPATH`, and
  :envvar:`PATH` into the parallel child environment. You only need to set
  :envvar:`PARALLEL` for additional variables your project requires. See the
  documentation for your chosen
  :ref:`--execenv<src/reference/cli:sierra---execenv>` plugin for the full
  list of what it exports automatically.

- To shorten long command lines, SIERRA supports an rcfile via ``--rcfile`` /
  :envvar:`SIERRA_RCFILE`.

.. IMPORTANT:: Examples are grouped by engine and can be pasted directly into a
   terminal. Many flags use SIERRA core functionality that is not
   engine-specific; the absence of a stage 5 example under ROS1+Gazebo does not
   mean stage 5 cannot be used with that engine — it is a limitation of the
   sample project, not SIERRA itself.


ARGoS Examples
==============

Basic Example
-------------

The simplest way to use ARGoS with SIERRA:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/argos/your-experiment.argos \
   --n-runs=3 \
   --engine=engine.argos \
   --project=projects.sample_argos \
   --execenv=hpc.local \
   --physics-n-engines=1 \
   --exp-setup=exp_setup.T10000 \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --batch-criteria population_size.Log64

This runs a batch of 7 experiments varying swarm size from 1–64 by powers of 2
(``Log64`` generates 1, 2, 4, 8, 16, 32, 64). All experiments use the
``LowBlockCount`` scenario in a 10×10×2 arena; the meaning of ``LowBlockCount``
is entirely defined by the project. Within each experiment, 3 independent
simulations are run with different random seeds, for 21 ARGoS simulations total.
On a reasonable machine this takes about 10 minutes. Outputs appear under
``$HOME/exp``; see :ref:`concepts/run-time-tree` for the directory layout.

HPC Example
-----------

To run on a SLURM-managed cluster, invoke SIERRA inside an ``sbatch`` script or
via ``srun``:

.. code-block:: bash

   #!/bin/bash -l
   #SBATCH --time=01:00:00
   #SBATCH --nodes=10
   #SBATCH --tasks-per-node=6
   #SBATCH --cpus-per-task=4
   #SBATCH --mem-per-cpu=2G
   #SBATCH --output=R-%x.%j.out
   #SBATCH --error=R-%x.%j.err
   #SBATCH -J argos-slurm-example

   # Setup environment
   export ARGOS_INSTALL_PREFIX=$HOME/.local
   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARGOS_INSTALL_PREFIX/lib/argos3
   export ARGOS_PLUGIN_PATH=$ARGOS_INSTALL_PREFIX/lib/argos3:$HOME/git/mycode
   export SIERRA_PLUGIN_PATH=$HOME/git/sierra-sample-project
   export PARALLEL="--env ARGOS_PLUGIN_PATH"

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/argos/your-experiment.argos \
   --n-runs=96 \
   --engine=engine.argos \
   --project=projects.sample_argos \
   --execenv=hpc.slurm \
   --exp-setup=exp_setup.T10000 \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --batch-criteria population_size.Log64

This requests 10 nodes with 6 tasks and 4 CPUs per task (24 cores per node, 240
total). :ref:`--physics-n-engines<src/plugins/engine/argos/index:sierra---physics-n-engines>`
is not passed — SIERRA computes it from the SLURM parameters. SIERRA runs
simulations 6 at a time per node (up to 60 concurrently); all 96 runs for each
experiment complete before the next experiment begins. Each simulation runs for
10,000 seconds in the same scenario as the basic example above.

:envvar:`LD_LIBRARY_PATH` does not need to appear in :envvar:`PARALLEL` here —
the ``hpc.slurm`` plugin exports it automatically alongside :envvar:`PATH` and
:envvar:`PYTHONPATH`. Only :envvar:`ARGOS_PLUGIN_PATH` needs to be forwarded
explicitly because it is project-specific.

To support mixed-architecture HPC environments, set :envvar:`SIERRA_ARCH` to a
string such as ``x86`` or ``arm``. SIERRA will then search for
``argos3-x86`` or ``argos3-arm`` rather than the plain ``argos3`` executable,
and you can conditionally set :envvar:`ARGOS_PLUGIN_PATH` to point to the
corresponding compiled libraries.

Rendering Example
-----------------

Use ARGoS's image-capture capability to produce simulation videos:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/argos/your-experiment.argos \
   --engine=engine.argos \
   --project=projects.sample_argos \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --execenv=hpc.local \
   --n-runs=3 \
   --engine-vc \
   --exp-graphs=none \
   --physics-n-engines=1 \
   --batch-criteria population_size.Log8

This runs 3 simulations per experiment under :program:`Xvfb` for headless
rendering. During stage 4 the captured frames are stitched into videos using
:program:`ffmpeg` (see :ref:`concepts/run-time-tree` for where videos
appear). No graphs are generated because ``--exp-graphs=none`` is passed.

The
:ref:`--camera-config<src/plugins/engine/argos/index:sierra---camera-config>`
option lets you specify static or dynamic camera arrangements, such as a
circular pan around the arena.

.. NOTE:: ARGoS can capture many thousands of images per simulation depending on
   run length. Keep :ref:`--n-runs<src/reference/cli:sierra---n-runs>` small
   when rendering to avoid filling the filesystem.

Bivariate Batch Criteria Example
--------------------------------

Vary two parameters jointly across a grid of experiments:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/argos/your-experiment.argos \
   --engine=engine.argos \
   --project=projects.sample_argos \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --execenv=hpc.local \
   --n-runs=3 \
   --exp-graphs=none \
   --physics-n-engines=1 \
   --batch-criteria population_size.Log8 max_speed.1.9.C5

``population_size.Log8`` generates 4 population sizes (1, 2, 4, 8).
``max_speed.1.9.C5`` is defined in the sample project and sets maximum robot
speed to 1, 3, 5, 7, or 9, giving 5 experiments. Together they form a 4×5=20
experiment grid, with population size on the X axis and max speed on the Y.
Swapping the order of the two criteria swaps which is on which axis.

Each experiment still runs 3 independent simulations, for 60 simulations total.
During stages 3 and 4, SIERRA generates heatmaps rather than line graphs by
default, because the experiment space is 2D. Heatmap generation can take a very
long time and can be disabled with ``--project-no-HM``.

``max_speed.1.9.C5`` can also be used on its own as a univariate criterion —
remove the ``population_size`` argument to get a univariate example.

ROS1+Gazebo Examples
====================

Basic Example
-------------

The simplest way to use SIERRA with the ROS1+Gazebo engine:

.. code-block:: bash

   sierra \
   --engine=engine.ros1gazebo \
   --project=projects.sample_ros1gazebo \
   --n-runs=4 \
   --execenv=hpc.local \
   --expdef-template=exp/ros1gazebo/your-experiment.launch \
   --scenario=HouseWorld.10x10x1 \
   --sierra-root=$HOME/exp \
   --batch-criteria population_size.Log8 \
   --controller=turtlebot3_sim.wander \
   --exp-setup=exp_setup.T10 \
   --robot turtlebot3

This runs a batch of 4 experiments varying swarm size from 1–8 by powers of 2
(``Log8`` generates 1, 2, 4, 8). Within each experiment, 4 independent
simulations run with different random seeds, for 16 Gazebo simulations total.
Each run is 10 seconds of simulated time. Outputs appear under ``$HOME/exp``;
see :ref:`concepts/run-time-tree` for the directory layout.

HPC Example
-----------

To run on a SLURM-managed cluster:

.. code-block:: bash

   #!/bin/bash -l
   #SBATCH --time=01:00:00
   #SBATCH --nodes=4
   #SBATCH --tasks-per-node=6
   #SBATCH --cpus-per-task=4
   #SBATCH --mem-per-cpu=2G
   #SBATCH --output=R-%x.%j.out
   #SBATCH --error=R-%x.%j.err
   #SBATCH -J ros1gazebo-slurm-example

   # Setup environment
   export SIERRA_PLUGIN_PATH=$HOME/git/sierra-sample-project

   sierra \
   --engine=engine.ros1gazebo \
   --project=projects.sample_ros1gazebo \
   --n-runs=96 \
   --execenv=hpc.slurm \
   --expdef-template=exp/ros1gazebo/your-experiment.launch \
   --scenario=HouseWorld.10x10x1 \
   --sierra-root=$HOME/exp \
   --batch-criteria population_size.Log8 \
   --controller=turtlebot3_sim.wander \
   --exp-setup=exp_setup.T10000 \
   --robot turtlebot3

This requests 4 nodes with 6 tasks and 4 CPUs per task (24 cores per node, 96
total). SIERRA runs simulations 6 at a time per node (up to 24 concurrently);
all 96 runs for each experiment complete before the next begins. Each simulation
runs for 10,000 seconds in the same scenario as the basic example.

No project-specific variables need to be added to :envvar:`PARALLEL` here
because this example has no engine-specific library paths beyond what
``hpc.slurm`` already exports automatically (:envvar:`LD_LIBRARY_PATH`,
:envvar:`PATH`, :envvar:`PYTHONPATH`). If your ROS project requires additional
paths — for example, a custom :envvar:`ROS_PACKAGE_PATH` entry — add them to
:envvar:`PARALLEL` as shown in the ARGoS HPC example.

Bivariate Batch Criteria Example
--------------------------------

Vary two parameters jointly:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/ros1gazebo/your-experiment.launch \
   --engine=engine.ros1gazebo \
   --project=projects.sample_ros1gazebo \
   --controller=turtlebot3_sim.wander \
   --scenario=HouseWorld.10x10x2 \
   --execenv=hpc.local \
   --n-runs=3 \
   --exp-graphs=none \
   --batch-criteria population_size.Log8 max_speed.1.9.C5

This produces a 4×5=20 experiment grid (4 population sizes from ``Log8``, 5
speed values from ``max_speed.1.9.C5``). See the ARGoS bivariate example for a
full explanation of bivariate batch criteria mechanics — the behaviour is
identical across engines.

ROS1+Robot Examples
===================

Basic Example
-------------

The simplest way to use SIERRA with physical robots:

.. code-block:: bash

   sierra \
   --engine=engine.ros1robot \
   --project=projects.sample_ros1robot \
   --n-runs=4 \
   --expdef-template=exp/ros1robot/your-experiment.launch \
   --scenario=OutdoorWorld.16x16x2 \
   --sierra-root=$HOME/exp \
   --batch-criteria population_size.Linear6.C6 \
   --controller=turtlebot3.wander \
   --robot turtlebot3 \
   --exp-setup=exp_setup.T100 \
   --execenv=robot.turtlebot3 \
   --nodefile=turtlebots.txt \
   --exec-inter-run-pause=60 \
   --no-master-node

This runs a batch of 4 experiments varying swarm size across 1, 2, 3, 4, 5, 6
robots (``Linear6.C6`` generates 6 evenly-spaced sizes from 1 to 6). Within
each experiment, 4 runs are conducted per swarm size. SIERRA pauses 60 seconds
between runs so you can reset robot positions and the environment before the
next run begins.

``turtlebots.txt`` contains the IP addresses of all 6 robots; SIERRA selects
the appropriate subset when the swarm size is less than 6. You can also omit
``--nodefile`` and set :envvar:`SIERRA_NODEFILE` instead.

No ROS master node is needed for this setup, so
:ref:`--no-master-node<src/plugins/engine/index:sierra---no-master-node>` is
passed.  After all runs complete and SIERRA finishes stages 3 and 4, outputs
appear under ``$HOME/exp``; see :ref:`concepts/run-time-tree` for the directory
layout.

JSONSim / YAMLSim Notes
=======================

JSONSim and YAMLSim are lightweight built-in engines that require no external
simulator install. They are meant to show that SIERRA can work with programs
that take JSON/YAML as input. Neither engine uses ``--exp-setup`` timing is
configured through engine-specific means. The ARGoS examples above otherwise
translate directly; replace the engine, project, and template arguments:

.. code-block:: bash

   # JSONSim equivalent of the ARGoS basic example
   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/jsonsim/template.json \
   --n-runs=3 \
   --engine=plugins.jsonsim \
   --project=projects.sample_jsonsim \
   --execenv=hpc.local \
   --controller=default.default \
   --scenario=scenario1 \
   --batch-criteria max_speed.1.9.C3

.. code-block:: bash

   # YAMLSim equivalent of the ARGoS basic example
   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/yamlsim/template.yaml \
   --n-runs=3 \
   --engine=plugins.yamlsim \
   --project=projects.sample_yamlsim \
   --execenv=hpc.local \
   --controller=default.default \
   --scenario=scenario1 \
   --batch-criteria noise_floor.1.9.C3

All other SIERRA flags — :ref:`--execenv<src/reference/cli:sierra---execenv>`,
:ref:`--n-runs<src/reference/cli:sierra---n-runs>`,
:ref:`--batch-criteria<src/reference/cli:sierra---batch-criteria>`, etc. — work identically
across both engines.

Selective Pipeline Examples
===========================

By default SIERRA runs all four stages (1–4) sequentially. Use
:ref:`--pipeline<src/reference/cli:sierra---pipeline>` to run a subset — common when
inspecting generated inputs before committing to a full run, or when
regenerating graphs without re-running experiments.

Inspect Generated Inputs Before Running
----------------------------------------

Run stage 1 only to generate experiment input files without executing anything:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/argos/your-experiment.argos \
   --engine=engine.argos \
   --project=projects.sample_argos \
   --execenv=hpc.local \
   --n-runs=3 \
   --physics-n-engines=1 \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --batch-criteria population_size.Log8 \
   --pipeline 1

After this completes, inspect the generated files under
``$HOME/exp/.../exp-inputs/`` before running stage 2. This is useful for
verifying that batch criteria and controller configuration are producing the
expected input variations.

Regenerate Graphs Without Re-Running Experiments
------------------------------------------------

Run stages 3 and 4 only to reprocess existing experimental outputs and
regenerate all graphs — for example after tweaking graph YAML configuration:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --expdef-template=exp/argos/your-experiment.argos \
   --engine=engine.argos \
   --project=projects.sample_argos \
   --execenv=hpc.local \
   --n-runs=3 \
   --physics-n-engines=1 \
   --exp-setup=exp_setup.T10000 \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --batch-criteria population_size.Log8 \
   --pipeline 3 4

``--exp-setup`` is included here because stage 3 uses it to compute the expected
number of datapoints per run when building statistics. Stages 3 and 4 read from
``exp-outputs/`` (written during stage 2) and are safe to re-run any number of
times without affecting the underlying experimental data.

Stage 5 Examples
================

Stage 5 generates comparative products across multiple batch experiments that
were previously processed by stages 1–4. It is not engine-specific — the
examples below use the ARGoS sample project but the flags work identically with
other engines.

Stage 5 is not part of the default pipeline and must be requested explicitly
with :ref:`--pipeline 5<src/reference/cli:sierra---pipeline>`. SIERRA
derives ``--scenario`` and
:ref:`--batch-criteria<src/reference/cli:sierra---batch-criteria>` from the
existing output tree, so they do not need to be passed.

Scenario Comparison
-------------------

Compare a single controller across all scenarios it has been run on:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --project=projects.sample_argos \
   --pipeline 5 \
   --across=scenarios \
   --spread=conf95 \
   --bc-univar \
   --things=foraging.footbot_foraging

SIERRA finds all scenarios the ``foraging.footbot_foraging`` controller has been
run on and generates comparison graphs according to the configuration in
``graphs.yaml``, with 95% confidence intervals. If the controller was run with
multiple batch criteria in the same scenario, SIERRA generates a unique set of
graphs for each scenario–batch-criteria combination.

Controller Comparison
---------------------

Compare multiple controllers in the scenarios they have all been run on:

.. code-block:: bash

   sierra \
   --sierra-root=$HOME/exp \
   --project=projects.sample_argos \
   --pipeline 5 \
   --across=controllers \
   --spread=conf95 \
   --bc-univar \
   --things=foraging.footbot_foraging,foraging.footbot_foraging-slow

SIERRA finds all scenarios where *both* controllers have been run and generates
per-scenario comparison graphs according to ``graphs.yaml``, with 95% confidence
intervals. If multiple batch criteria were used in the same scenario, a unique
graph set is generated for each scenario–batch-criteria combination.

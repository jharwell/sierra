.. _ln-sierra-usage-examples:

***********************
SIERRA Usage By Example
***********************

This page contains reference examples of SIERRA usage to help you craft your own
SIERRA invocation.

==============
ARGoS Examples
==============

These examples assumes a project named ``fordyca`` which contains a controller
defined in the ``controllers.yaml`` as ``d0.CRW``, with a runtime environment of
the local machine.

In all examples, ``$HOME/git/mycode`` contains the ARGoS C++ library, and
``$HOME/git/sierra-projects`` contains the ``fordyca`` SIERRA project.

Basic Example
=============

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --n-runs=3 \
   --platform=platform.argos\
   --project=fordyca \
   --exec-env=hpc.local \
   --physics-n-engines=1 \
   --exp-setup=exp_setup.T10000 \
   --controller=d0.CRW \
   --scenario=SS.12x6x1 \
   --batch-criteria population_size.Log64

This will run a batch of 7 experiments using a correlated random walk robot
controller (CRW), across which the swarm size will be varied from 1..64, by
powers of 2. Within each experiment, 3 copies of each simulation will be run
(each with different random seeds), for a total of 21 ARGoS simulations. On a
reasonable machine it should take about 10 minutes or so to run. After it
finishes, you can go to ``$HOME/exp`` and find all the simulation outputs. For
an explanation of SIERRA's runtime directory tree, see
:ref:`ln-sierra-usage-runtime-exp-tree`.

HPC Example
===========

In order to run on a SLURM managed cluster, you need to invoke SIERRA within a
script submitted with ``sbatch``, or via ``srun`` with the correspond cmdline
options set.

::

   #!/bin/bash -l
   #SBATCH --time=01:00:00
   #SBATCH --nodes 10
   #SBATCH --tasks-per-node=6
   #SBATCH --cpus-per-task=4
   #SBATCH --mem-per-cpu=2G
   #SBATCH --output=R-%x.%j.out
   #SBATCH --error=R-%x.%j.err
   #SBATCH -J argos-slurm-example

   # setup environment
   export ARGOS_INSTALL_PREFIX=/$HOME/.local
   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARGOS_INSTALL_PREFIX/lib/argos3
   export ARGOS_PLUGIN_PATH=$ARGOS_INSTALL_PREFIX/lib/argos3:$HOME/git/mycode
   export SIERRA_PLUGIN_PATH=$HOME/git/sierra-projects
   export PARALLEL="--env ARGOS_PLUGIN_PATH --env LD_LIBRARY_PATH"

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --n-runs=96 \
   --platform=platform.argos\
   --project=fordyca \
   --exec-env=hpc.slurm \
   --exp-setup=exp_setup.T10000 \
   --controller=d0.CRW \
   --scenario=SS.12x6x1 \
   --batch-criteria population_size.Log64

In this example, the user requests 10 nodes with 24 cores each, and wants to run
ARGoS with 4 physics engines ( 4 * 6 = 24), with 8GB memory per core. Note that
we don't pass ``--physics-n-engines`` -- SIERRA computes this from the SLURM
parameters. SIERRA will run each of the 96 simulations per experiment in
parallel, 6 at a time on each allocated node.

Rendering Example
=================

This example shows how to use ARGoS image capturing ability to create nice
videos of simulations.

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --platform=platform.argos\
   --project=fordyca \
   --controller=d0.CRW \
   --scenario=SS.12x6x1 \
   --exec-env=hpc.local \
   --n-runs=3 \
   --platform-vc \
   --exp-graphs=none \
   --physics-n-engines=1 \
   --batch-criteria population_size.Log8

The runs 3 simulations in parallel with 1 physics engine each, and runs ARGoS
under :program:`Xvfb` to get it to render headless images. During stage 4, these
images are stitched together using :program:`ffmpeg` to create videos (see
:ref:`ln-sierra-usage-runtime-exp-tree` for where the videos will appear). No graphs
are generated during stage 4 in this example.

You may also be interested in the ``--camera-config`` option, which allows you
to specify different static/dynamic camera arrangements (e.g., do a nice
circular pan around the arena during simulation).

.. NOTE:: Because LOTS of images can be captured by ARGoS to create videos,
          depending on simulation length, you usually want to have a very small
          ``--n-runs`` to avoid filling up the filesystem.

Stage 5 Example
===============

This example assumes that stages 1-4 have been run successfully with a project
named ``fordyca`` and that a univariate batch criteria has been used (such as
:ref:`ln-sierra-platform-argos-bc-population-size`).

::

   sierra-cli \
   --project=fordyca \
   --pipeline 5 \
   --scenario-comparison \
   --dist-stats=conf95 \
   --bc-univar \
   --controller=d0.CRW \
   --sierra-root=$HOME/exp


This will compare all scenarios that all controllers with ``$HOME/exp`` which
have been run on the same set of scenarios according to the configuration
defined in ``stage5.yaml``. It will plot the 95% confidence intervals on all
generated graphs for the univariate batch criteria.


====================
ROS1+Gazebo Examples
====================

Basic Example
=============

This examples assumes a project named ``fordyca`` which contains a controller
defined in the ``controllers.yaml`` as ``turtlebot3_sim.wander``, with a runtime
environment of the local machine.

::

   sierra-cli \
   --platform=platform.ros1gazebo \
   --project=fordyca \
   --n-runs=4 \
   --exec-env=hpc.local \
   --template-input-file=exp/your-experiment.launch \
   --scenario=HouseWorld.10x10x1 \
   --sierra-root=$HOME/exp/test \
   --batch-criteria population_size.Log8 \
   --controller=turtlebot3_sim.wander \
   --exp-overwrite \
   --exp-setup=exp_setup.T10 \
   --robot turtlebot3

This will run a batch of 4 experiments using a correlated random walk controller
(CRW) on the turtlebot3. Population size will be varied from 1..8, by powers
of 2. Within each experiment, 4 copies of each simulation will be run (each with
different random seeds), for a total of 16 Gazebo simulations. On a reasonable
machine it should take about 10 minutes or so to run. After it finishes, you can
go to ``$HOME/exp`` and find all the simulation outputs. For an explanation of
SIERRA's runtime directory tree, see :ref:`ln-sierra-usage-runtime-exp-tree`.

HPC Example
===========

In order to run on a SLURM managed cluster, you need to invoke SIERRA within a
script submitted with ``sbatch``, or via ``srun`` with the correspond cmdline
options set.

::

   #!/bin/bash -l
   #SBATCH --time=01:00:00
   #SBATCH --nodes 4
   #SBATCH --tasks-per-node=6
   #SBATCH --cpus-per-task=4
   #SBATCH --mem-per-cpu=2G
   #SBATCH --output=R-%x.%j.out
   #SBATCH --error=R-%x.%j.err
   #SBATCH -J ros1gazebo-slurm-example

   # setup environment
   export SIERRA_PLUGIN_PATH=$HOME/git/sierra-projects

   sierra-cli \
   --platform=platform.ros1gazebo \
   --project=fordyca \
   --n-runs=96 \
   --exec-env=hpc.slurm \
   --template-input-file=exp/your-experiment.launch \
   --scenario=HouseWorld.10x10x1 \
   --sierra-root=$HOME/exp/test \
   --batch-criteria population_size.Log8 \
   --controller=turtlebot3_sim.wander \
   --exp-overwrite \
   --exp-setup=exp_setup.T10 \
   --robot turtlebot3

In this example, the user requests 10 nodes with 24 cores each. SIERRA will run
each of the 96 runs in parallel, 24 at a time on each allocated node.

===================
ROS1+Robot Examples
===================

Basic Example
=============

This examples assumes a project named ``fordyca`` which contains a controller
defined in the ``controllers.yaml`` as ``turtlebot3_sim.wander``, with a runtime
environment of a set of turtlebots.

::

   sierra-cli \
   --platform=platform.ros1robot \
   --project=fordyca \
   --n-runs=4 \
   --template-input-file=exp/your-experiment.launch \
   --scenario=RN.16x16x2 \
   --sierra-root=$HOME/exp/test \
   --batch-criteria population_size.Linear6.C6 \
   --controller=turtlebot3.wander \
   --robot turtlebot3 \
   --exp-setup=exp_setup.T100 \
   --exec-env=robots.turtlebot3 \
   --nodefile=turtlebots.txt
   --exec-inter-run-pause=60 \
   --no-master-node \

This will run a batch of 4 experiments using a correlated random walk controller
(CRW) on the turtlebot3. Population size will be varied from 1,2,3,4,5,6. Within
each experiment, 4 experimental runs will be conducted with each swarm
size. SIERRA will pause for 60 seconds between runs so you can reset the robot's
positions and environment before continuing with the next
run. ``turtlebots3.txt`` contains the IP addresses of all 6 robots in the swarm
(SIERRA may use different combinations of these if the swarm size is < 6). For
these experiments, no master node is needed, so it is disabled. After all runs
have completed and SIERRA finishes stages 3 and 4, you can go to ``$HOME/exp``
and find all the simulation outputs. For an explanation of SIERRA's runtime
directory tree, see :ref:`ln-sierra-usage-runtime-exp-tree`.

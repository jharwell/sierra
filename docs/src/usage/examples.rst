.. _ln-sierra-usage-examples:

***********************
SIERRA Usage By Example
***********************

This page contains reference examples of SIERRA usage to help you craft your own
SIERRA invocation.  These examples use the SIERRA project plugins from the
SIERRA sample project repo: :xref:`SIERRA_SAMPLE_PROJECT`. See
:ref:`ln-sierra-trial` or :ref:`ln-sierra-getting-started` for setting up the
sample project repository.

In all examples:

- ``$HOME/git/mycode`` contains the ARGoS C++ library

- ``$HOME/git/sierra-sample-project/projects`` contains the SIERRA project
  plugin

- ``$HOME/git/sierra-sample-project/projects`` is on
  :envvar:`SIERRA_PLUGIN_PATH`.

If your setup is different, adjust paths in the commands below as needed.

.. IMPORTANT:: The examples are grouped by platform, so they can be pasted into
               the terminal and executed directly. However, parts of many
               commands use common functionality in the SIERRA core; just
               because you don't see stage5 examples for the ROS1+Gazebo
               platform doesn't mean you can't run stage5 with that
               platform. Non-uniformities in which commands are below are more a
               limitation of the sample project than SIERRA itself.

==============
ARGoS Examples
==============


Basic Example
=============

This example illustrates the simplest way to use ARGoS with SIERRA to run
experiments.
::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --n-runs=3 \
   --platform=platform.argos\
   --project=argos_project \
   --exec-env=hpc.local \
   --physics-n-engines=1 \
   --exp-setup=exp_setup.T10000 \
   --controller=foraging.footbot_foraging\
   --scenario=LowBlockCount.10x10x2 \
   --batch-criteria population_size.Log64

This will run a batch of 7 experiments using a correlated random walk robot
controller (CRW), across which the swarm size will be varied from 1..64, by
powers of 2. Experiments will all be run in the same scenario: ``LowBlockCount``
in a 10x10x2 arena; the meaning of ``LowBlockCount`` is entirely up to the
project. In this case, we can infer it has to do with the # of blocks available
for robots to forage for. In fact, whatever is passed to ``--scenario`` is
totally arbitrary from SIERRA's point of view.

Within each experiment, 3 copies of each simulation will be run (each with
different random seeds), for a total of 21 ARGoS simulations. On a reasonable
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
   --project=argos_project \
   --exec-env=hpc.slurm \
   --exp-setup=exp_setup.T10000 \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --batch-criteria population_size.Log64

In this example, the user requests 10 nodes with 24 cores each, and wants to run
ARGoS with 4 physics engines ( 4 * 6 = 24), with 8GB memory per core. Note that
we don't pass ``--physics-n-engines`` -- SIERRA computes this from the SLURM
parameters. SIERRA will run each of the 96 simulations per experiment in
parallel, 6 at a time on each allocated node.  Each simulation will be 10,000
seconds long and use ``LowBlockCount`` scenario in a 10x10x2 arena, as in the
previous example.

.. IMPORTANT:: You need to export :envvar:`PARALLEL` containing all necessary
               environment variables your code uses in addition to those needed
               by SIERRA before invoking it, otherwise some of them might not be
               transferred to the SLURM job and/or the new shell GNU parallel
               starts each simulation in.

Note that if you compile ARGoS for different architectures within the same HPC
environment, you can use a combination of conditionally setting
:envvar:`ARGOS_PLUGIN_PATH` with setting :envvar:`SIERRA_ARCH` to some string to
tell SIERRA to use a given version of ARGoS, depending on where you request
resources from. For example, you could set ``SIERRA_ARCH=x86`` or
``SIERRA_ARCH=arm`` to link to an ``argos3-x86`` or ``argos3-arm`` executable
and libraries, respectively.

Rendering Example
=================

This example shows how to use ARGoS image capturing ability to create nice
videos of simulations.

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --platform=platform.argos\
   --project=argos_project \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --exec-env=hpc.local \
   --n-runs=3 \
   --platform-vc \
   --exp-graphs=none \
   --physics-n-engines=1 \
   --batch-criteria population_size.Log8

The runs 3 simulations in parallel with 1 physics engine each, and runs ARGoS
under :program:`Xvfb` to get it to render headless images. During stage 4, these
images are stitched together using :program:`ffmpeg` to create videos (see
:ref:`ln-sierra-usage-runtime-exp-tree` for where the videos will appear). No
graphs are generated during stage 4 in this example.

You may also be interested in the ``--camera-config`` option, which allows you
to specify different static/dynamic camera arrangements (e.g., do a nice
circular pan around the arena during simulation).

.. NOTE:: Because LOTS of images can be captured by ARGoS to create videos,
          depending on simulation length, you usually want to have a very small
          ``--n-runs`` to avoid filling up the filesystem.

Bivariate Batch Criteria Example
================================

This example shows how to use ARGoS with a bivariate batch criteria (i.e., with
TWO variables/things you want to vary jointly)::

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --platform=platform.argos\
   --project=argos_project \
   --controller=foraging.footbot_foraging \
   --scenario=LowBlockCount.10x10x2 \
   --exec-env=hpc.local \
   --n-runs=3 \
   --platform-vc \
   --exp-graphs=none \
   --physics-n-engines=1 \
   --batch-criteria population_size.Log8 max_speed.1.9.C5

The ``max_speed.1.9.C5`` is a batch criteria defined in the sample project, and
corresponds to setting the maximum robot speed from 1...9 to make 5 experiments;
i.e., 1,3,5,7,9. It can also be used on its own--just remove the first
``population_size`` batch criteria from the command to get a univariate example.

The generated experiments form a grid: population size on the X axis and max
speed on the Y, for a total of 3 * 5 = 15 experiments. If the order of the batch
criteria is switched, then so is which criteria/variable is on the X/Y
axis. Experiments are run in sequence just as with univariate batch
criteria. During stage 3/4, by default SIERRA generates discrete a set of
heatmaps, one per capture interval of simulated time, because the experiment
space is 2D instead of 1D, and you can't easily represent time AND two
variables + time on a plot. This can take a loooonnnggg time, and can be
disabled with ``--project-no-HM``.

The generated sequence of heatmaps can be turned into a video--pass
``--bc-rendering`` during stage 4 to do so.

Stage 5 Scenario Comparison Example
===================================

This example shows how to run stage 5 to compare a single controller across
different scenarios, assuming that stages 1-4 have been run successfully. Note
that this stage does not require you to input the ``--scenario``, or the
``--batch-criteria``; SIERRA figures these out for you from the ``--controller``
and ``--sierra-root``.

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --project=argos_project \
   --pipeline 5 \
   --scenario-comparison \
   --dist-stats=conf95 \
   --bc-univar \
   --controller=foraging.footbot_foraging \
   --sierra-root=$HOME/exp


This will compare all scenarios that the
``foraging.footbot_foraging`` controller has been run on according to
the configuration defined in ``stage5.yaml``. SIERRA will plot the 95%
confidence intervals on all generated graphs for the univariate batch criteria
(whatever it was). If multiple batch criterias were used with this controller in
the same scenario, SIERRA will process all of them and generate unique graphs
for each scenario+criteria combination that the
``foraging.footbot_foraging`` controller was run on.


Stage 5 Controller Comparison Example
=====================================

This example shows how to run stage 5 to compare multiple controllers in a
single scenario, assuming that stages 1-4 have been run successfully. Note that
this stage does not require you to input ``--batch-criteria``; SIERRA figures
these out for you from the ``--controller-list`` and ``--sierra-root``.

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --project=argos_project \
   --pipeline 5 \
   --controller-comparison \
   --dist-stats=conf95 \
   --bc-univar \
   --controllers-list=foraging.footbot_foraging,foraging.footbot_foraging-slow \
   --sierra-root=$HOME/exp


SIERRA will compute the list of scenarios that the ``foraging.footbot_foraging``
and the ``foraging.footbot_foraging_slow`` controllers have *all* been
run. Comparison graphs for each scenario with the
``foraging.footbot_foraging,foraging.footbot_foraging_slow`` controllers will be
generated according to the configuration defined in ``stage5.yaml``. SIERRA will
plot the 95% confidence intervals on all generated graphs for the univariate
batch criteria (whatever it was). If multiple batch criterias were used with
each controller in the same scenario, SIERRA will process all of them and
generate unique graphs for each scenario+criteria combination both controllers
were run on.

====================
ROS1+Gazebo Examples
====================

Basic Example
=============

This examples shows the simplest way to use SIERRA with the ROS1+gazebo platform
plugin::

   sierra-cli \
   --platform=platform.ros1gazebo \
   --project=ros1gazebo_project \
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
different random seeds), for a total of 16 Gazebo simulations. Each experimental
run will be will be 10 seconds of simulated time. On a reasonable machine it
should take about 10 minutes or so to run. After it finishes, you can go to
``$HOME/exp`` and find all the simulation outputs. For an explanation of
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
   --project=ros1gazebo_project \
   --n-runs=96 \
   --exec-env=hpc.slurm \
   --template-input-file=exp/your-experiment.launch \
   --scenario=HouseWorld.10x10x1 \
   --sierra-root=$HOME/exp/test \
   --batch-criteria population_size.Log8 \
   --controller=turtlebot3_sim.wander \
   --exp-overwrite \
   --exp-setup=exp_setup.T10000 \
   --robot turtlebot3

In this example, the user requests 10 nodes with 24 cores each. SIERRA will run
each of the 96 runs in parallel, 24 at a time on each allocated node.  Each
simulation will be 1,000 seconds long and use same scenario as before.

.. IMPORTANT:: You need to export :envvar:`PARALLEL` containing all necessary
               environment variables your code uses in addition to those needed
               by SIERRA before invoking it, otherwise some of them might not be
               transferred to the SLURM job and/or the new shell GNU parallel
               starts each simulation in.

Bivariate Batch Criteria Example
================================

This example shows how to use ROS1+gazebo with a bivariate batch criteria (i.e.,
with TWO variables/things you want to vary jointly)::

::

   sierra-cli \
   --sierra-root=$HOME/exp \
   --template-input-file=exp/your-experiment.argos \
   --platform=platform.ros1gazebo\
   --project=ros1gazebo_project \
   --controller=turtlebot3_sim.wander \
   --scenario=HouseWorld.10x10x2 \
   --exec-env=hpc.local \
   --n-runs=3 \
   --exp-graphs=none \
   --batch-criteria population_size.Log8 max_speed.1.9.C5

The ``max_speed.1.9.C5`` is a batch criteria defined in the sample project, and
corresponds to setting the maximum robot speed from 1...9 to make 5 experiments;
i.e., 1,3,5,7,9. It can also be used on its own--just remove the first
``population_size`` batch criteria from the command to get a univariate example.

The generated experiments form a grid: population size on the X axis and max
speed on the Y, for a total of 3 * 5 = 15 experiments. If the order of the batch
criteria is switched, then so is which criteria/variable is on the X/Y
axis. Experiments are run in sequence just as with univariate batch
criteria. During stage 3/4, by default SIERRA generates discrete heatmaps of
results instead of linegraphs, because the experiment space is 2D instead of 1D.

===================
ROS1+Robot Examples
===================

Basic Example
=============

This examples shows the simplest way to use SIERRA with the ROS1+robot platform
plugin::

::

   sierra-cli \
   --platform=platform.ros1robot \
   --project=ros1robot_project \
   --n-runs=4 \
   --template-input-file=exp/your-experiment.launch \
   --scenario=OutdoorWorld.16x16x2 \
   --sierra-root=$HOME/exp/test \
   --batch-criteria population_size.Linear6.C6 \
   --controller=turtlebot3.wander \
   --robot turtlebot3 \
   --exp-setup=exp_setup.T100 \
   --exec-env=robot.turtlebot3 \
   --nodefile=turtlebots.txt
   --exec-inter-run-pause=60 \
   --no-master-node \

This will run a batch of 4 experiments using a correlated random walk controller
(CRW) on the turtlebot3. Population size will be varied from 1,2,3,4,5,6. Within
each experiment, 4 experimental runs will be conducted with each swarm
size. SIERRA will pause for 60 seconds between runs so you can reset the robot's
positions and environment before continuing with the next
run. ``turtlebots3.txt`` contains the IP addresses of all 6 robots in the swarm
(SIERRA may use different combinations of these if the swarm size is < 6).  You
could also omit ``--nodefile`` and set :envvar:`SIERRA_NODEFILE` instead.

For these experiments, no master node is needed, so it is disabled. After all
runs have completed and SIERRA finishes stages 3 and 4, you can go to
``$HOME/exp`` and find all the simulation outputs. For an explanation of
SIERRA's runtime directory tree, see :ref:`ln-sierra-usage-runtime-exp-tree`.

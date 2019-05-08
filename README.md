# SIERRA (Swarm Robotics Simulation Automation Framework)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Python/GNU Parallel framework for running large numbers of ARGoS simulations
in parallel on Minnesota Supercomuting Institute (MSI). Also can run on
non-MSI machines for testing.

It is named thusly because it will save you a LITERAL, (not figurative) mountain
of work.

## Non-MSI Setup

Before trying to use sierra with MSI, you should get it installed and running on
your local machine, and try a few small scale experiments.

1. Install python dependencies with pip3:

        pip3 install pandas similaritymeasures fastdtw

   - pandas (used for .csv file manipulation)
   - similaritymeasures (needed for temporal variance graph generation)
   - fastdtw (needed for temporal variance graph generation)

2. Install OS packages:

   - GNU parallel (`parallel` on ubuntu)

## MSI Setup

Prior to executing these steps you should have gotten *CORRECT* results on your
local machine (you really, really, _really_, don't want to be trying to do
development/debugging on MSI).

1. Get an MSI account (you will need to talk to Maria Gini, my advisor).

2. On an MSI login node, install the same python dependencies as above, but user
   local (you obviously don't have admin priveleges on the cluster):

        pip3 install --user pandas similaritymeasures fastdtw

   This is a one time step.

3. On an MSI login node, run the bash script to clone the project:

        /home/gini/shared/swarm/bin/fordyca-clone-all.sh $HOME/git

   The 1st argument is the path (relative or absolute) to the location where you
   want the project repos to live (they will all be cloned into that level).

   If you need to checkout a particular branch in the repo you can do that after
   running the script (or copy the script and modify it to do this automatically
   if you are going to be doing a lot of work on MSI).

4. On an MSI login node, get an interactive job session so you can build fordyca
   and its dependencies natively to the cluster you will be running on
   (mesabi/itasca) for maximum speed:

        qsub -I -lwalltime=1:00:00,nodes=1:ppn=8,mem=20gb

   The above command, when it returns, will give you 1 hour of time on an actual
   compute node. You know you are running/building on a compute node rather than
   a login node on mesabi/itasca when the hostname is `cnXXXX` rather than
   `nodeXXXX`.

5. Setup the build environment in your interactive job session:

        . /home/gini/shared/swarm/bin/build-env-setup.sh

6. In your interactive session run the bash script to build the project (note
   that you may want to tweak the cmake defines in the script, or use your own
   script, depending on what types of experiments you are running). If you are
   not sure if you need to do this, ask!

        /home/gini/shared/swarm/bin/fordyca-build-default.sh /path/to/project/root

   The argument is the root directory where all repositories should be
   cloned/built. It can be anywhere you have write access to.

7. That's it! You are all setup to run on MSI.

# Running on MSI

1. Copy and modify one of the PBS scripts under `scripts/` in this repo for your
   experiment/batch experiment.

2. Read the documentation for PBS scripts and MSI job submission a queue on your
   chosen cluster:

   https://www.msi.umn.edu/content/job-submission-and-scheduling-pbs-scripts
   https://www.msi.umn.edu/queues


3. Have your .pbs script script reviewed before submission (will likely save you
   a lot of time fighting with the job submission system).

4. Submit your job via:

        qsub your-pbs-script.pbs

5. Reap the rewards of research!


*WARNING: SIERRA DOES NOT DELETE DIRECTORIES FOR YOU. ALWAYS MAKE SURE YOU RUN
DIFFERENT EXPERIMENTS (BATCH OR NOT) IN DIFFERENT DIRECTORIES OR ODIN'S WRATH
MAY FALL UPON THEE.*

## Directory Structure

`generators/` - Controller and scenario generators used to modify template
                .argos files to provide the setting/context for running
                experiments with variables.

`graphs/` - Generic code to generate graphs of different types.

`perf_measures/` - Measures to compare performance of different controllers
                   across experiments.

`pipeline/` - Core pipline code in 5 stages:

              1. Generate inputs
              2. Run experiments
              3. Average results
              4. Generate graphs within a single experiment and between
                 experiments in a batch.
              5. Generate graphs comparing batched experiments (not part of
              default pipeline).

`scripts/` - Contains example `.pbs` scripts to be run on MSI.

`templates/` - Contains template .argos files. Really only necessary to be able
               to change configuration that is not directly controllable via
               generators, and the # of templates should be kept small, as they
               need to be manually kept in sync with the capabilities of
               fordyca.

`variables/` - Generators for experimental variables to modify template .argos
               files in order to run experiments with a given controller.

## General Usage

- There are 5 pipeline stages, though only the first 4 will run automatically.

- If you run stages individually, then before stage X will run without crashing,
  you need to run stage X-1.

## Contributing

For contributing to `SIERRA`, see [CONTRIBUTING](docs/CONTRIBUTING.md).

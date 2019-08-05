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

        pip3 install pandas similaritymeasures fastdtw matplotlib

   - pandas (used for .csv file manipulation)
   - similaritymeasures (needed for temporal variance graph generation)
   - fastdtw (needed for temporal variance graph generation)

2. Install OS packages:

   - GNU parallel (`parallel` on ubuntu)

*IMPORTANT*: When running sierra, unless you have added the sierra repo to your
`PYTHONPATH` and/or `sierra.py` to your `PATH`, you will only be able to launch
sierra from the root of the sierra repo.

## MSI Setup

Prior to executing these steps you should have gotten *CORRECT* results on your
local machine (you really, really, _really_, don't want to be trying to do
development/debugging on MSI).

1. Get an MSI account (you will need to talk to Maria Gini, my advisor), and
   verify that you can login to `itasca` via the following commands, run from
   your laptop on a UMN computer/UMN wifi (will not work from outside UMN campus
   without a VPN):

        ssh <x500>@login.msi.umn.edu
        ssh itasca.msi.umn.edu


   Where `<x500>` is your umn x500. If the commands are successful, you have
   logged into a `itasca` login node (this is different than a `itasca` compute node).

   A similar check for `mesabi` via the following commands, run from your laptop
   on a UMN computer/UMN wifi (will not work from outside UMN campus without a
   VPN):

        ssh <x500>@login.msi.umn.edu
        ssh mesabi.msi.umn.edu

   If the commands are successful, you have logged into a `mesabi` login node
   (this is different than a `mesabi` compute node).

2. Once you can login, you can begin the setup by sourcing the environment
   definitions:

        . /home/gini/shared/swarm/bin/msi-env-setup.sh

    *ANYTIME you log into an MSI node (login or compute) to build/run ANYTHING
    you MUST source this script otherwise things will (probably) not work.*


3. On an MSI login node (can be any type, as the filesystem is shared across all
   clusters), install the same python dependencies as above, but user
   local (you obviously don't have admin priveleges on the cluster):

        pip install --user pandas similaritymeasures fastdtw matplotlib

   This is a one time step. Must be done on a login node, as compute nodes do
   not have internet access.

4. On an MSI login node (can be any type, as the filesystem is shared across all
   clusters), run the bash script to clone the project:

        /home/gini/shared/swarm/bin/msi-clone-all.sh $HOME/git

   The 1st argument is the path (relative or absolute) to the location where you
   want the project repos to live (they will all be cloned into that level).

   If you need to checkout a particular branch in the repo you can do that after
   running the script (or copy the script and modify it to do this automatically
   if you are going to be doing a lot of work on MSI).

5. On an MSI login node, get an interactive job session so you can build fordyca
   and its dependencies natively to the cluster you will be running on
   (mesabi/itasca) for maximum speed:

        qsub -I -lwalltime=1:00:00,nodes=1:ppn=8,mem=20gb

   The above command, when it returns, will give you 1 hour of time on an actual
   compute node. You know you are running/building on a compute node rather than
   a login node on mesabi/itasca when the hostname is `cnXXXX` rather than
   `nodeXXXX`.

6. In your interactive session run the bash script to build the project (note
   that you may want to tweak the cmake defines in the script, or use your own
   script, depending on what types of experiments you are running). If you are
   not sure if you need to do this, ask!

        /home/gini/shared/swarm/bin/msi-build-default.sh $HOME/git 8

   - 1st arg: The root directory where all where cloned into with the
     `msi-clone-all.sh` script. In the example above, this is `$HOME/git`.`
   - 2nd arg: How many cores to use when building (should be the same # as the
     ppn when you submitted your interactive job session). In the example above
     this is 8.

7. That's it! You are all setup to run on MSI.

## Running on MSI

1. Read the documentation for PBS scripts and MSI job submission a queue on your
   chosen cluster:

   https://www.msi.umn.edu/content/job-submission-and-scheduling-pbs-scripts
   https://www.msi.umn.edu/queues

   Seriously--READ THEM.

2. Copy and modify the `example.pbs` script under `scripts/` in the sierra repo
   for your experiment/batch experiment. You will need to change:

   - `FORDYCA`: To the location of the where you cloned the fordyca repo
   - `SIERRA`: To the location of the where you cloned the sierra repo
   - The contact email, number of requested nodes, etc. for the PBS script.

3. Have your .pbs script script reviewed before submission (will likely save you
   a lot of time fighting with the job submission system).

4. Submit your job via:

        qsub your-pbs-script.pbs

    Note the job number--it is important to track job progress and to figure out
    what happened when things go wrong.

5. Reap the rewards of research! You will get an email when your job starts, and
   when it finishes/crashes. To view the in-progress output of the job, look in
   the file called `your-pbs-script.pbs.o1234` where `1234` is the job number of
   your job. MSI will create this file in the directory you submit the job
   from, and direct your job's stdout to it. To view the stderr for your job,
   look in the file `your-pbs-script.pbs.e1234` where `1234` is the job number
   of your job. MSI will create this file in the directory you submit the job
   from, and direct your job's stderr to it.


*WARNING: SIERRA DOES NOT DELETE DIRECTORIES FOR YOU. ALWAYS MAKE SURE YOU RUN
DIFFERENT EXPERIMENTS (BATCH OR NOT) IN DIFFERENT DIRECTORIES OR ODIN'S WRATH
MAY FALL UPON THEE.* ...Dependending on what you are doing of course. Are you
feeling lucky and want to roll the dice?

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
              3. Process results of running experiments (averaging, etc.)
              4. Generate graphs within a single experiment and between
                 experiments in a batch.
              5. Generate graphs comparing batched experiments (not part of
              default pipeline).

`scripts/` - Contains some `.pbs` scripts that can be run on MSI. Scripts become
             outdated quickly as the code base for this project and its upstream
             projects changes, so scripts should not be relied upon to work as
             is. Rather, they should be used to gain insight into how to use
             sierra and how to craft your own script.

`templates/` - Contains template .argos files. Really only necessary to be able
               to change configuration that is not directly controllable via
               generators, and the # of templates should be kept small, as they
               need to be manually kept in sync with the capabilities of
               fordyca.

`variables/` - Generators for experimental variables to modify template .argos
               files in order to run experiments with a given controller.


## Basic Usage

When using sierra, you need to tell it the following:

- When template input file to use (`--template-config-file`). See `sierra
  --help` for specifics.

- How many copies of each simulation to run per experiment (`--n-sims`). See
  `sierra --help` for specifics.

- Where it is running (`--exec-method`). See `sierra --help` for specifics.

- How long simulations should be (`--time-setup`). See `sierra --help` for
  specifics.

- What controller to run with, what block distribution type to use, and how
  large the arena should be (`--generator`). See `sierra --help` for specifics.

- What you are investigating; that is, what variable are you interested in
  varying (`--batch-criteria`). Valid variables are files found in the
  `variables/` directory, though not *ALL* files in there are valid. Valid ones
  are:

  - `swarm_size`
  - `swarm_density`
  - `temporal_variance`

  Look in the `.py` files for the variable+parsers for each of the above to see
  how to use them.

## Usage Tips

- The best way to figure out what sierra can do is via the `--help`
  option. Every option is very well documented. The second best way is to look
  at the scripts under `scripts/`.

- There are 5 pipeline stages, though only the first 4 will run automatically.

- If you run stages individually, then before stage X will (probably) run
  without crashing, you need to run stage X-1.

- If you are using a `quad_source` block distribution, the arena should be at
  least 16x16 (smaller arenas don't leave enough space for caches and often
  cause segfaults).

## Contributing

For contributing to `SIERRA`, see [CONTRIBUTING](docs/CONTRIBUTING.md).

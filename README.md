# SIERRA (Swarm Robotics Simulation Automation Framework)

Python/GNU Parallel framework for running large numbers of ARGoS simulations
in parallel on Minnesota Supercomuting Institute (MSI). Also can run on
non-MSI machines for testing.

It is named thusly because it will save you a LITERAL, (not figurative) mountain
of work.

## Setup

Setup instructions can be found on the the `devel` branch, as that hs not only
the latest semi-stable release, but also the most up-to-date documentation,
including this README.


    git checkout devel

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
              4. Generate graphs within a batched experiment
              5. Generate graphs comparing controllers within/across scenarios

`scripts/` - Contains `.pbs` scripts to be run on MSI.

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

*WARNING: SIERRA DOES NOT DELETE DIRECTORIES FOR YOU. ALWAYS MAKE SURE YOU RUN
DIFFERENT EXPERIMENTS (BATCH OR NOT) IN DIFFERENT DIRECTORIES OR ODIN'S WRATH
MAY FALL UPON THEE.*

## How to Add A Controller

If you have created a new robot controller and you want to be able to use it
with sierra from the command line you have to:

1. Create a generator for it under `generators/`. For a controller named
   `FizzBuzz` it must be called `fizzbuzz.py` in order to be able to invoke it
   via the sierra command line.

2. The generator must derive from `ExpInputGenerator`, and be called
   `BaseGenerator`.

3. It must define 3 functions:

   `init_sim_defs()` - Initial simulation definitions common to ANY simulation
   that uses the controller (this usually is just changing the controller/loop
   function labels). See the stateful/CRW controllers for examples.

   `generate()` - Generate simulation definitions without saving the file
   (non-terminal generator).

   `generator_and_save()` - Generate simulation definitions AND save the file
   (terminal generator).

4. Add an import of `fizzbuzz.py` to `factory.py` so that it can be instantiated
   via information passed on the command line.

5. Update the help in `sierra.py` to reflect the new class that you have instantiated.

6. Once finished, open a pull request with your new controller.

## How to Add A Variable

If you have a new experimental variable that you have added to the main fordyca
library, *AND* which is exposed via the input `.argos` file, then you need to do
the following to get it to work with sierra:

1. Make your variable inherit from `BaseVariable` and place your `.py` file
   under `variables/`.

2. Define 2 functions:

   `get_attr_changelist()` - Given whatever parameters that your variable was
   passed during initialization (e.g. the boundaries of a range you want to vary
   it within), produce a list of sets, where each set is all changes that need
   to be made to the .argos template file in order to set the value of your
   variable to something.

   `gen_tag_rmlist()` - Given whatever parameters that your variable was passed
   during initialization, generate a list of sets, where each set is all tags
   that need to be removed from the .argos template file in order to set the
   value of your variable to something.

3. TEST YOUR GRAPH TO VERIFY IT DOES NOT CRASH.

4. Once finished open a pull request with your new variable.

## How to Add A New Graph

If you would like to define a new intra-experiment graph (i.e. a graph that
should be generated for each set of simulation runs that are averaged together),
or a new inter-experiment graph (i.e. a graph that should only be generated for
batch experiments) then you need to do the following:

1. Add an entry in the list of graphs found in `exp_pipeline.py` in an
   appropriate category (notice that the categories map back to the
   collectors/generate .csv files in FORDYCA) in either `inter_exp_targets()` or
   `intra_exp_targets()`.

2. TEST YOUR GRAPH TO VERIFY IT DOES NOT CRASH.

3. Once finished, open a pull request with your new graph.

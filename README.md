# SIERRA (Swarm Robotics Simulation Automation Framework)

Python/GNU Parallel framework for running large numbers of ARGoS simulations
in parallel on Minnesota Supercomuting Institute (MSI). Also can run on
non-MSI machines for testing.

It is named thusly because it will save you a LITERAL, (not figurative) mountain
of work.

## Setup

1. Install python dependencies with pip3:

   - pandas
   - similaritymeasures (needed for temporal variance graph generation)
   - fastdtw (needed for temporal variance graph generation)

2. Install packages:

   - GNU parallel (`parallel` on ubuntu)

## Quick start

1. Get an MSI account (you will need to talk to Maria Gini, my advisor).

2. Login to MSI and setup the build environment:

        . /home/gini/shared/swarm/bin/build-env-setup.sh

3. Clone and build the devel branch of the project and all its sub
   repositories:

         /home/gini/shared/swarm/bin/fordyca-clone-all.sh $HOME/git
         /home/gini/shared/swarm/bin/fordyca-build-default.sh $HOME/git

   The argument is the root directory where all repositories should be
   cloned/built. It can be anywhere you have write access to. You may need to
   copy/update the default build script in order to get it to build your branch.

4. Copy and modify one of the PBS scripts under `scripts/` file in this repo for
   your experiment/batch experiment.

5. Submit your job on MSI itasca/mesabi with:

        qsub your-pbs-script.pbs

6. Reap the rewards of research!

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

## How to Add A Controller

If you have created a new robot controller and you want to be able to use it
with sierra from the command line you have to:

1. Create a generator for it under `generators/`. For a controller named
   `FizzBuzz` it must be called `fizzbuzz.py` in order to be able to invoke it
   via the sierra command line via `fizzbuzz.FizzBuzz`. The generator must
   derive from `ExpInputGenerator`.

2. Define `generate()`, which should generate simulation definitions without
   saving the file (non-terminal generator). It will need to call
   `ExpInputGenerator.generate_common_defs()` in order to also generate the
   changes common to all simulations (e.g. duration, # threads, etc.).

3. Add an import of `fizzbuzz.py` to `generator_factory.py` so that it can be
   instantiated via information passed on the command line.

5. Update the help in `cmdline.py` for the `--generator` option to reflect the
   new class that you have instantiated.

6. Once finished, open a pull request with your new controller.

Usually the set of changes that need to be applied to template input files for a
specific controller is quite small, and may possibly be just changing the name
of the controller tag.

## How to Add A Variable For Batch Criteria

If you have a new experimental variable that you have added to the main fordyca
library, *AND* which is exposed via the input `.argos` file, then you need to do
the following to get it to work with sierra:

1. Make your variable inherit from `BaseVariable` and place your `.py` file
   under `variables/`. The "base class" version of your variable should take in
   parameters, and NOT have any hardcoded values in it anywhere.

2. Define the parser for your variable in order to parse the command line string
   of the specific configuration of it into a dictionary of attributes that can
   then be used by the `Factory()` function below.

3. Define the functions for generating changes to be applied to the template
   input file according to the selected batch criteria.

   In order to change attributes, add/remove tags, you will need to understand
   the XPath syntax for search in XML files; tutorial is
   [here](https://docs.python.org/2/library/xml.etree.elementtree.html).

   `get_attr_changelist()` - Given whatever parameters that your variable was
   passed during initialization (e.g. the boundaries of a range you want to vary
   it within), produce a list of sets, where each set is all changes that need
   to be made to the .argos template file in order to set the value of your
   variable to something. Each change is a tuple with the following elements:

   0. XPath search path for the *parent* of the attribute that you want to
      modify.

   1. Name of the attribute you want to modify within the parent element.

   2. The new value as a string (integers will throw an exception).

   `gen_tag_rmlist()` - Given whatever parameters that your variable was passed
   during initialization, generate a list of sets, where each set is all tags
   that need to be removed from the .argos template file in order to set the
   value of your variable to something.

   Each change is a tuple with the following elements:

   0. XPath search path for the *parent* of the tag that you want to
      remove.

   1. Name of the attribute you want to remove within the parent element.

   `gen_tag_addlist()` - Given whatever parameters that your variable was passed
   during initialization, generate a list of sets, where each set is all tags
   that need to be added to the .argos template file.

   Each change is a tuple with the following elements:

   0. XPath search path for the *parent* of the tag that you want to
      add.

   1. Name of the tag you want to add within the parent element.

   2. A dictionary of (attribute, value) pairs to create as children of the
      tag when creating the tag itself.

   `Factory(criteria_str)` - Given the string of the your batch
   criteria/variable you have defined that was passed on the command line,
   creates specific instances of your variable that are derived from your "base"
   variable class. This is to provide maximum flexibility to those using sierra,
   so that they can create _any_ kind of instance of your variable, and not just
   the ones you have made pre-defined classes for.

   This function is a class factory method, and should (1) call the parser for
   your variable, (2) return a custom instance of your class that is named
   according to the specific batch criteria string passed on the command line,
   inherits from the "base" variable class you defined above, and that has an
   `__init__()` function that calls the `__init__()` function of your base
   variable class that takes *NO* arguments and populates the arguments to your
   base variable class `__init__()` according to the dictionary of parsed
   batch criteria definitions.

   See `variables/swarm_size.py` for a simple example of this.

4. Once finished open a pull request with your new variable.

## How to Add A New Intra-Experiment Graph

Add an entry in the list of linegraphs found in `intra_exp_targets.py` in an
appropriate category (notice that the categories map back to the
collectors/generate .csv files in FORDYCA) if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single .csv file (multiple
  columns in the same .csv file can be graph simultaneously).

- The data you want to graph can be represented by a histogram.

Add an entry in the list of heatmaps found in `intra_exp_targets.py` in an
appropriate category if:

- The data you want to graph is two dimensional (i.e. a spatial representation
  of the arena is some way).

TEST YOUR GRAPH TO VERIFY IT DOES NOT CRASH. If it does, that likely means that
the .csv file the graph is build from is not being generated properly in
FORDYCA.

Once finished, open a pull request with your changes.

## How to Add A New Inter-Experiment Graphs

Add an entry in the list of linegraphs found in `inter_exp_targets.py` in an
appropriate category (notice that the categories map back to the
collectors/generate .csv files in FORDYCA) if:

- The data you want to graph can be represented by a line (i.e. is one
  dimensional in some way).

- The data you want to graph can be obtained from a single column from a single
  .csv file.

- The data you want to graph requires comparison between multiple experiments in
  a batch.

TEST YOUR GRAPH TO VERIFY IT DOES NOT CRASH. If it does, that likely means that
the .csv file the graph is build from is not being generated properly in
FORDYCA.

Once finished, open a pull request with your changes.

# SIERRA (Swarm Robotics Simulation Automation Framework)

Python/GNU Parallel framework for running large numbers of ARGoS simulations
in parallel on Minnesota Supercomuting Institute (MSI). Also can run on
non-MSI machines for testing.

It is named thusly because it will save you a LITERAL, (not figurative) mountain
of work.

## Quick Setup

1. Get an MSI account (you will need to talk to Maria Gini, my advisor).

2. Login to MSI and setup the build environment:

        . /home/gini/shared/swarm/bin/build-env-setup.sh

3. Clone and build the devel branch of the project and all its sub
   repositories:

         /home/gini/shared/swarm/bin/clone-and-build-clean.sh $HOME/git

   The argument is the root directory where all repositories should be
   cloned/built. It can be anywhere you have write access to.

   If you want to squeeze maximum performance out of the code, then you can
   recompile also pass `-DWITH_ER_NREPORT=yes` (in addition to the other
   arguments the script passes to cmake) which will turn off ALL diagnostic
   logging (metrics are still logged). It can be significantly faster, but if
   the results look weird/something goes wrong you will not have the usual
   logs available to troubleshoot/debug.

4. Modify one of the PBS scripts under `scripts/` file in this repo for your
   experiment/batch experiment.

6. Submit your job on MSI with:

        qsub your-pbs-script.pbs

7. Reap the rewards of research!

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

## How to use the XMLLuigi class

### What it can do

The XMLLuigi class is the main class for editing Argos configuration files.
It allows you to do three things:

1. Change attributes
2. Change tags
3. Remove elements (and all subelements)

### Paths

Attributes, tags, and elements are all found via *paths*.

Paths are strings and look like
`argos-configuration.arena.wall_south.body`. Each part of the path is separated
by a period (instead of a slash like usual filesystems).  Each part of the path
is either a tag or an id, and they can be used interchangeably.  For example, if
we wanted to specify the element `<stateful_foraging_controller id="ffc"
library="libfordyca">`, we could either use `stateful_foraging_controller` or
`ffc` in the path, and the code will work in the exact same way.

The type of path is specified by the last part of the path.  If the last part of
the path is an *attribute* (for example "max\_speed" in <differential\_drive
max\_speed="10" soft\_turn_max="30" />), then it's called an *attribute path*
because the path leads to an attribute.  If the last part of the path is a *tag*
or *id*, then it's called an *element path* because the path leads to the
element with that given tag or id.  When changing attributes, *attribute paths*
are used, and when editing tags or removing elements, *element paths* are used.

### Searching Algorithms

There are two different search algorithms that the XMLLuigi class uses to
figure out what your path leads to.  The first is a *loose search* and the
second is a *strict-loose search*.  Loose searches are always used for attribute
paths, and strict-loose searches are always used for element paths.

In a *loose search*, the program will fill in any gaps between parts of the path
you specified, and look for the first thing that it can find works. For example,
if the attribute "block\_fname" is only used once in your configuration file, and
you specify just "block_fname" as the attribute path, the loose search will fill
in the gaps and come up with the strict path
"argos-configuration.loop-functions.output.metrics.block\_fname". This makes it
so you don't really have to specify what thing you're looking for: you can just
specify enough so that the program doesn't mistake it for something else.  For
example, let's say there was another block\_fname attribute, that was under an
"output2" element (which is at the same level as the "output" element). Instead
of having to type
"argos-configuration.loop-functions.output2.metrics.block\_fname", you can just
type "output2.block\_fname" and it will find the correct attribute, skipping over
the first "block_fname" because it doesn't have "output2" as its parent.

In a *loose-strict search*, the program will search the entire XML tree for the
first part of the path, and once it finds it, it will expect everything to be
specified explicitly from there on. (Ideally, if it didn't find anything that
matched, it would look for the next occurrence of the first part of the path and
try again from there, but that's not how I implemented it, so that's not how it
works. (This functionality is listed as a "TODO".)) So, for example, if you
wanted to edit the metrics tag found at
"argos-configuration.loop-functions.output.metrics", you could use the path
"argos-configuration.loop-functions.output.metrics" or
"loop-functions.output.metrics" or "output.metrics" or just "metrics", whichever
one best specifies the metrics element you want. However, unlike loose
searching, you can't do "loop-functions.metrics"; a loose-strict search will not
fill in the gaps after the first part of the path. It will fill in the start of
the full path, but nothing more.

Overall, the class was designed to be as easy to use as possible, making it
extremely simple and quick to specify which element you're talking about and
then move on to the more interesting parts of actually running your experiment.

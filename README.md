# SIERRA (Swarm robotics simulation automation framework)

Python/GNU Parallel framework for running large numbers of ARGoS simulations
in parallel on Minnesota Supercomuting Institute (MSI). Also can run on
non-MSI machines for testing.

## Setup

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

4. Modify the `template.pbs` file in this repo for your experiment/batch
   experiment. `sierra` has a lot of options, and the help for each is fairly
   intuitive.

6. Submit your job on MSI with:

        qsub your-pbs-script.pbs

7. Reap the rewards of research!

## How to use the XMLHelper class

### What it can do

The XMLHelper class is the main class for editing Argos configuration files.
It allows you to do three things:

1. Change attributes
2. Change tags
3. Remove elements (and all subelements)

### Paths
Attributes, tags, and elements are all found via *paths*.

Paths are strings and look like "argos-configuration.arena.wall_south.body". Each part of the path is separated by a period (instead of a slash like usual filesystems).
Each part of the path is either a tag or an id, and they can be used interchangeably.
For example, if we wanted to specify the element <stateful_foraging_controller id="ffc" library="libfordyca">, we could either use "stateful_foraging_controller" or "ffc" in the path, and the code will work in the exact same way.

The type of path is specified by the last part of the path.
If the last part of the path is an *attribute* (for example "max_speed" in <differential_drive max_speed="10" soft_turn_max="30" />), then it's called an *attribute path* because the path leads to an attribute.
If the last part of the path is a *tag* or *id*, then it's called an *element path* because the path leads to the element with that given tag or id.
When changing attributes, *attribute paths* are used, and when editing tags or removing elements, *element paths* are used.

### Searching Algorithms
There are two different search algorithms that the XMLHelper class uses to figure out what your path leads to.
The first is a *loose search* and the second is a *strict-loose search*.
Loose searches are always used for attribute paths, and strict-loose searches are always used for element paths.

In a *loose search*, the program will fill in any gaps between parts of the path you specified, and look for the first thing that it can find works. For example, if the attribute "block_fname" is only used once in your configuration file, and you specify just "block_fname" as the attribute path, the loose search will fill in the gaps and come up with the strict path "argos-configuration.loop-functions.output.metrics.block_fname". This makes it so you don't really have to specify what thing you're looking for: you can just specify enough so that the program doesn't mistake it for something else.
For example, let's say there was another block_fname attribute, that was under an "output2" element (which is at the same level as the "output" element). Instead of having to type "argos-configuration.loop-functions.output2.metrics.block_fname", you can just type "output2.block_fname" and it will find the correct attribute, skipping over the first "block_fname" because it doesn't have "output2" as its parent.

In a *loose-strict search*, the program will search the entire XML tree for the first part of the path, and once it finds it, it will expect everything to be specified explicitly from there on. (Ideally, if it didn't find anything that matched, it would look for the next occurrence of the first part of the path and try again from there, but that's not how I implemented it, so that's not how it works. (This functionality is listed as a "TODO".)) So, for example, if you wanted to edit the metrics tag found at "argos-configuration.loop-functions.output.metrics", you could use the path "argos-configuration.loop-functions.output.metrics" or "loop-functions.output.metrics" or "output.metrics" or just "metrics", whichever one best specifies the metrics element you want. However, unlike loose searching, you can't do "loop-functions.metrics"; a loose-strict search will not fill in the gaps after the first part of the path. It will fill in the start of the full path, but nothing more.

Overall, the class was designed to be as easy to use as possible, making it extremely simple and quick to specify which element you're talking about and then move on to the more interesting parts of actually running your experiment.

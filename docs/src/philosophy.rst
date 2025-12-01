.. _philosophy:

========================
SIERRA Design Philosophy
========================

This document outlines the main philosophy behind SIERRA's design, how it can be
used, and so forth. It really boils down to a few core ideas.

Single Input, Multiple Output
=============================

During stage 1, SIERRA generates multiple experiments via multiple experimental
run input files all from a single template input file, which must be specified
on the command line. SIERRA does not follow any references/links to other input
files in this template input file, greatly simplifying the generation process
and improving reproducability of experiments (e.g., less cryptic/subtle errors
because of a ROS ``<include>`` which is different between the package versions
installed on one system and another). SIERRA *does* support flattening an input
file tree into a single file, per :ref:`plugins/expdef`.

Don't Modify User Directory Structures
======================================

:term:`Experimental Runs <Experimental Run>` will generate some sort of
directory structure in their output directory; it might be flat, it might be
deeply nested. SIERRA maintains this directory structure during stages {3,4} in
the interest of the Principle Of Least Surprise, and to make it easier for
SIERRA outputs to interoperate with other user scripts.

Assert Often, Fail Early
========================

If a condition arises which SIERRA can't easily handle, abort, either via an
uncaught exception or an ``assert()``. Don't try to recover by throwing an
exception which can be caught at a higher level, etc., just abort. This gives
users confidence that `if` SIERRA doesn't crash, then it is probably working
properly. As a result of this, any ``try-catch`` blocks which do exist should
always be in the same function; never rely on raised exceptions to be caught at
higher levels.

Never Delete Things
===================

Because SIERRA is intended for academic/industry research, and experimental data
can be hard fought, SIERRA tries to guard against accidental
deletions/overwrites of said data that users actually want to keep, but forgot
to change parameters to direct SIERRA to keep it. Therefore, we force the user
to explicitly say that deleting/overwriting is OK when it might cause
irreparable damage to experiment results (i.e., only pipeline stages 1 and
2). Overwriting is OK in later pipeline stages since those files are built from
stage 1 and 2 files, and can be easily regenerated if overwritten.

Better Too Much Configuration Than Too Little
=============================================

SIERRA is designed to be as modular and extensible as possible (just like ARGoS,
ROS, Gazebo, etc.), so that it can be adapted for a wide variety of
applications. When in doubt, SIERRA exposes relevant settings as configuration
(even if the average user will never change them from their default values).

Swiss Army Pipeline
===================

SIERRAS 5-stage :ref:`Pipeline<usage/pipeline>` is meant to be like a Swiss
army knife, in that you can run (mostly) arbitrary subsets of the 5 stages and
have everything work as you would expect it to, to help with tweaking
experimental design, generated graphs, etc., with minimal headaches of "Grrr I
have to wait for THAT part to run again before it will get to re-run the part I
just changed the configuration for".

This manifests in some important ways:

- Separating results processing in stage 3 from product generation in stage
  \4.

- Products in stage 4 are sourced from a single input file, rather than
  pulling data from multiple files.

- Each pipeline stage is transactional at the file level; that is, it writes out
  its results to one or more files which can be read by later stages (as opposed
  to keeping things in memory, which makes running arbitrary sets of pipeline
  stages more difficult).

- The :ref:`usage/run-time-tree` is designed to be human readable/copyable/etc,
  so that researchers can use any part of SIERRA\'s pipeline as they wish and
  walk away with the data at any time. That is, the design choice to use a
  directory structure containing elements which were *not* hashed was deliberate
  (looking at you conan).

Maximum Reusability
===================

SIERRA is designed the way it is to maximize reusability. When used properly,
you should 100% *NEVER* have to copy-paste YAML configuration, python code,
etc., between projects/engines/etc. For a beginner user, the amount of
configuration can seeing annoying/daunting, and that is one of the ways in which
SIERRA's usability needs to improve, but for advanced users with lots of
projects, the amount of configuration maximizes reusability.

.. todo:: Provide some concrete details on this.

Separation Of Data Types
========================

Any statistics generated during say stage 3 are stored in *separate* files from
the actual data, even if the chosen ``--storage`` plugin and/or
``--prod`` plugin supports them in a single file. This is for reasons of:

- Readability in the files themselves. For time series/1D data, separating
  doesn't really provide benefits, but for 2D data it does. For 3D data, and
  beyond (e.g., 4D), visualization of the raw numerical data is difficult
  whether stats are in a separate file or in the same file as the actual data,
  so is a net neutral.

- Reducing memory footprint. For example, if a user is generating a 2D heatmap,
  any stddev info present in the source file is ignored if it is present. Thus,
  if it were present, and the source file be large, that could result in large,
  unnecessary memory footprints.

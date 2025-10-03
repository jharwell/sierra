..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _exp/stage3-dataflow:

================
Stage 3 Dataflow
================

At the highest level we have the following in the context of pipeline stages
2-4:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   left to right direction
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateFontStyle bold

   state "2. Execute\nExperiments\n" as stage2 {
      state "Raw Output Data" as raw  #lightcyan
   }

   state "3. Process\nExperiment\nOutputs" as stage3  {
      state "Processed Output Data" as proc #lightcyan
   }

   state "4. Generate\nProducts\n" as stage4  {
      state "Products " as products #lightcyan
   }

   raw --> proc
   proc --> products

The :term:`Raw Output Data` files from experimental runs is processed during
stage 3 into :term:`Processed Output Data` files. In stage 4 those processed
files are turned into :term:`products <Product>` of various sorts. All stage 4
products are sourced from a *single* data file, to encourage and enable
reusability of code across projects. As such, it is the job of active stage 3
plugins to make sure all the data needed to generate a given product appear in
the same file. The process of doing this is called :term:`Data Collation`.

.. IMPORTANT:: Stage 3 operates at the level of :term:`Raw Output Data` files
   and :term:`Experimental Runs <Experimental Run>`, while stage 4 operates at
   the level of :term:`Collated Output Data` files, :term:`Processed Output
   Data` files and :term:`Experiments <Experiment>`.

With that framing in mind, we can dive into the dataflow in detail.

Intra-Experiment Dataflow
=========================

Within stage 3 the first type of data processing that occurs is
*intra*-experiment data processing. If we look at the data from stage 2 for a
single :term:`Experimental Run` :math:`j` from :term:`Experiment` :math:`i` in
:term:`Batch Experiment` which produces :math:`k` raw output files, we could
represent the output data abstractly as:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   left to right direction
   skinparam DefaultFontSize 24
   skinparam DefaultFontColor #black
   skinparam stateFontStyle bold


   state "run j" as runj #skyblue {
      state "file 0" as filej0 #darkturquoise
      state "file 1" as filej1 #limegreen
      state "..." as filejx #green
      state "file k" as filejk #lightseagreen

      filej0 -[hidden]r-> filej1
      filej0 -[hidden]d-> filejx
      filej1 -[hidden]d-> filejk
      filejx -[hidden]r-> filejk
   }

For intra-experiment data processing, all of the per-run outputs are matched
across :term:`Experimental Runs <Experimental Run>` within an
:term:`Experiment`, and processed in some way (e.g., :ref:`generating
statistical distributions <plugins/proc/stat>`). Crucially, the processing is
done at the level of *entire files* (i.e., it is a file-level reduce
operation). For example, if runs produce a ``foo.csv`` file, then every column
in ``foo.csv`` will be present in the corresponding :term:`Processed Output
Data` files as well.

This can be visualized as follows:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateBorderThickness 8
   skinparam stateFontStyle bold

   state "run 0" as run0 #skyblue {
      state "file 0" as file00 #darkturquoise
      state "file 1" as file01 #limegreen
      state "..." as file0x #green
      state "file k" as file0k #lightseagreen

      file00 -[hidden]r-> file01
      file00 -[hidden]d-> file0x
      file01 -[hidden]d-> file0k
      file0x -[hidden]r-> file0k

   }
   state "run 1" as run1  #skyblue {
      state "file 0" as file10 #darkturquoise
      state "file 1" as file11 #limegreen
      state "..." as file1x #green
      state "file k" as file1k #lightseagreen

      file10 -[hidden]r-> file11
      file10 -[hidden]d-> file1x
      file11 -[hidden]d-> file1k
      file1x -[hidden]r-> file1k
   }

   state "..." as runx #skyblue

   state "run j" as runj #skyblue {
      state "file 0" as filej0 #darkturquoise
      state "file 1" as filej1 #limegreen
      state "..." as filejx #green
      state "file k" as filejk #lightseagreen

      filej0 -[hidden]r-> filej1
      filej0 -[hidden]d-> filejx
      filej1 -[hidden]d-> filejk
      filejx -[hidden]r-> filejk
   }

   state "Processed outputs" as intra #skyblue {
      state "file 0" as filep0 #darkturquoise
      state "file 1" as filep1 #limegreen
      state "..." as filepx #green
      state "file k" as filepk #lightseagreen

      filep0 -[hidden]r-> filep1
      filep1 -[hidden]r-> filepx
      filepx -[hidden]r-> filepk
   }

   run0 -[hidden]r-> run1
   run1 -[hidden]r-> runx
   runx -[hidden]r-> runj


   run1 -d-> intra
   run0 -d-> intra
   runx -d-> intra
   runj -d-> intra

Some examples of plugins performing this reduce operation:

- :ref:`plugins/proc/stat`

Inter-Experiment Dataflow
=========================

Within stage 3 the second type of data processing that occurs is
*inter*-experiment data processing. If we look at the data from stage 2 for a
single :term:`Experimental Run` :math:`j` from :term:`Experiment` :math:`i` in
:term:`Batch Experiment` which produces :math:`k` raw output files, we could
represent the output data abstractly as follows, using :term:`Experimental Run`
as SCOPE:

.. figure:: /figures/data-collation.png

An important point here is that within the SIERRA builtin stage3 processing
plugins not all raw output files get processed in this manner, only those which
are going to be used during stage 4 to produce something via a
user-specification. Generally this means that there is a ``.yaml`` file in a
:term:`Project` somewhere which has a list of :term:`Products <Product>` which a
user wants to generate. This list is matched against the raw output files, and
only matching files are processed. Thus, SIERRA is very efficient in its data
processing.

.. TIP:: :term:`Processed Output Data` files can be thought of as time-series
         data at the level of :term:`Experimental Runs <Experimental Run>`.



Some examples of plugins performing this reduce operation:

- :ref:`plugins/proc/collate`

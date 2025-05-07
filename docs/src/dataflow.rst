..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _dataflow:

==================
Dataflow in SIERRA
==================

This page details SIERRA's builtin data model, as it pertains to data generated
in :term:`Experimental Runs <Experimental Run>`. That is, once data is generated
as a result of running things in stage 2, how it is processed and transformed
into deliverables.

Dataflow Architecture
=====================

At the highest level we have the following in the context of pipeline stages
2-4:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   left to right direction
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black


   state "2. Execute\nExperiments\n" as stage2 {
      state "Raw Output Data" as raw  #skyblue
   }

   state "3. Process\nExperiment\nOutputs" as stage3  {
      state "Processed Output Data" as proc #skyblue
   }

   state "4. Generate\nDeliverables\n" as stage4  {
      state "Deliverables " as deliverables #skyblue
   }

   raw --> proc
   proc --> deliverables

The :term:`Raw Output Data` files from experimental runs is processed during
stage 3 into :term:`Processed Output Data` files. In stage 4 those processed
files are turned into deliverables of various sorts. All stage 4 deliverables
are sourced from a *single* data file, to encourage and enable reusability of
code across projects. As such, it is the job of stage 3 (among other things) to
make sure all the data needed to generate a given deliverable appear in the same
file. The process of doing this is called :term:`Data Collation`.

.. IMPORTANT::

   Stage 3 operates at the level of :term:`Raw Output Data`
   files and :term:`Experimental Runs <Experimental Run>`, while stage 4 operates at
   the level of :term:`Collated Output Data` files, :term:`Processed Output
   Data` files and :term:`Experiments <Experiment>`. Access at the level of
   stage 3 in stage 4 is not possible by design.

With that framing in mind, we can dive into the dataflow in detail.


.. _dataflow/stage3/intra-proc:

Stage 3: Intra-Experiment Processing
====================================

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

For *intra*-experiment data processing, all of the per-run outputs are matched
across :term:`Experimental Runs <Experimental Run>` within an
:term:`Experiment`, and processed in some way (e.g., :ref:`generating
statistical distributions <plugins/proc/stat>`). Crucially, the processing is
done at the level of *entire files* (i.e., it is a file-level reduce
operation). For example, if runs produce a ``foo.csv`` file, then every column
in ``foo.csv`` will be present in the corresponding :term:`Processed Output
Data` files as well.  Of course, like all things in SIERRA, if you don't need
thus functionality, you can turn it off by deselecting the plugin.

This can be visualized as follows:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateBorderThickness 8

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


.. TIP:: :term:`Processed Output Data` files can be thought of as time-series
         data at the level of :term:`Experimental Runs <Experimental Run>`.

.. _dataflow/stage3/intra-collate:

Stage 3: Intra-Experiment Collation
===================================

When generating deliverables, it is often necessary to perform some sort of
non-statistical mathematical analysis on the results. These calculations
*cannot* be done on the intra-experiment processed data files, because any
calculated statistical distributions from them will be invalid; this can be
thought of as an average of sums is not the same as a sum of averages.  To
support such use cases, SIERRA can make the necessary parts of the per-run
:term:`Raw Output Data` files available in stage 4 for doing such calculations
via :term:`Data Collation`. Of course, like all things in SIERRA, if you don't
need thus functionality, you can turn it off by deselecting the plugin.

This process in stage 3 can be visualized as follows for a single
:term:`Experiment`:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg

   ' Configuration
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateBorderThickness 8

   state "User\nSpecification" as user #lightcoral

   state "run 0" as run0 {
      state "file0" as file00 #skyblue {
         state "col0" as col000 #darkturquoise
         state "col1" as col001 #limegreen
      }
      state "file 1" as file01  #skyblue {
         state "colA" as col010 #green
         state "colB" as col011 #lightseagreen
      }
      state "..." as file0x #skyblue
   }
   state "run 1" as run1 {
      state "file0" as file10 #skyblue {
         state "col0" as col100 #darkturquoise
         state "col1" as col101 #limegreen
      }
      state "file 1" as file11  #skyblue {
         state "colA" as col110 #green
         state "colB" as col111 #lightseagreen
      }
      state "..." as file1x #skyblue
   }
   state "..." as runx #skyblue

   state "run j" as runj {
      state "file0" as filej0 #skyblue {
         state "col0" as colj00 #darkturquoise
         state "col1" as colj01 #limegreen
      }
      state "file1" as filej1  #skyblue {
         state "colA" as colj10 #green
         state "colB" as colj11 #lightseagreen
      }
      state "..." as filejx #skyblue
   }

   state "Processed outputs" as inter {
      state "col0 file" as filep0 #darkturquoise {
         state "run 0" as colp00
         state "run 1" as colp01
         state "..." as colp0x
         state "run j" as colp0j
      }
      state "col1 file" as filep1 #limegreen {
         state "run 0" as colp10
         state "run 1" as colp11
         state "..." as colp1x
         state "run j" as colp1j
      }
      state "colA file" as filep2 #green {
         state "run 0" as colp20
         state "run 1" as colp21
         state "..." as colp2x
         state "run j" as colp2j
      }
      state "colB file" as filep3 #lightseagreen {
         state "run 0" as colp30
         state "run 1" as colp31
         state "..." as colp3x
         state "run j" as colp3j
      }
   }

   filep0 -[hidden]r-> filep1
   filep2 -[hidden]r-> filep3
   filep0 -[hidden]d-> filep2
   filep1 -[hidden]d-> filep3

   user --> run0
   user --> run1
   user --> runx
   user --> runj

   run0 --> inter
   run1 --> inter
   runx --> inter
   runj --> inter


Here, the user has specified that the ``col{0,1}`` in ``file0`` produced by all
experimental runs should be combined into a single file. Thus the
:term:`Collated Output Data` file generated from that specification will have
:math:`j` columns, one per run. Similarly for ``col{A,B}`` in ``file1``. This is
collation *within* in an experiment (intra-experiment). Collation *across*
experiments (if enabled/configured) is done during stage 4.

.. _dataflow/stage4/intra:

Stage 4: Intra-Experiment Deliverable Generation
================================================

After :ref:`dataflow/stage3/intra-proc`, data is in :term:`Processed Output
Data` files and/or :term:`Collated Output Data` files. In stage 4, the
:term:`Processed Output Data` files can be taken and directly converted to
intra-experiment deliverables such as graphs and videos with appropriate
plugins.  Reminder: these files *cannot* be used as inputs into mathematical
calculations for statistical reasons; the :term:`Collated Output Data` files
should be be used as into mathematical calculations if needed. Of course, like
all things in SIERRA, if you don't need thus functionality, you can turn it off
by deselecting the plugin.

As mentioned earlier, intra-experiment deliverables are time-series based and
generated from processed data *within* each experiment. For example, here is a
very simple time-based graph generated from one of the sample projects
containing estimates of swarm energy over time for one experiment. Note the
confidence intervals automatically added by SIERRA.

.. figure:: /figures/dataflow-intra-graph-ex0.png

.. IMPORTANT:: All configuration for the graph above was specified via YAML--no
               python coding needed!

.. _dataflow/stage4/inter:

Stage 4: Inter-Experiment Deliverable Generation
================================================

After :ref:`dataflow/stage3/intra-collate`, data is in :term:`Collated Output
Data` files and/or :term:`Collated Output Data` files. In stage 4, we can run
:term:`Data Collation` on either of these types of files in order to further
refine their contents, following an analogous process as outlined above, but at
the level of a experiments within a batch rather than experimental runs within
an experiment. Of course, like all things in SIERRA, if you don't need thus
functionality, you can turn it off by deselecting the plugin.

After collation, inter-experiment deliverables can be generated directly. These
deliverables can be time-based, showing results from each experiment, like this:

.. figure:: /figures/dataflow-inter-graph-ex0.png

This is a very messy graph because of the width of confidence intervals, but it
does illustrate SIERRA's ability to combine data across experiments in a batch.

Or they can be summary graphs instead, based on some sort of summary
measure. For example, an inter-experiment summary linegraph complement to the
one above would look like this:

.. figure:: /figures/dataflow-inter-graph-ex1.png

The X-axis labels are populated based on the :term:`Batch Criteria`
used. Obviously, this is for a *single* batch experiment; summary graphs for
multiple batch experiments can be combined in stage 5 (see below).

.. IMPORTANT:: All configuration for the graphs above were specified via
               YAML--no python coding needed!

Stage 5: TODO
=============

.. todo:: Flesh this out.

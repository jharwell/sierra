..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _exp/stage4-dataflow:

================
Stage 4 Dataflow
================

At the highest level we have the following in the context of pipeline stages
3-5:

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg
   ' Configuration
    left to right direction
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateFontStyle bold

   state "3. Process\nExperiment\nOutputs" as stage3  {
      state "Processed Experiment\nOutputs" as proc #lightcyan
   }

   state "4. Generate\nProducts\n" as stage4  {
      state "Products" as products #lightcyan {
         state "Intra-experiment Products" as intra_prod #lightcoral
         state "Inter-experiment Products" as inter_prod #lightcoral
      }
    }
    state "5. Compare\nProducts\n" as stage5 {
       state "Inter-batch Products" as inter_batch  #lightcyan
    }

    stage3 --> stage4
    stage4 --> stage5

After :ref:`exp/stage3-dataflow`, data is in :term:`Processed Output Data` files
and/or :term:`Collated Output Data` files. In stage 4, the :term:`Processed
Output Data` files can be taken and directly converted to products along one of
two paths using appropriate plugins:

- Intra-experiment products such as graphs and videos, which are built from a
  single processed output data file.

- Inter-experiment products such as graphs, which are built by joining together
  identical sections/slices of the processed output data files for a single
  experiment.

Like the stage3 dataflow, generally in stage4 things are file-level.

Intra-Experiment Dataflow
=========================

.. plantuml::

   skinparam defaultTextAlignment center

   !theme cyborg
   ' Configuration
    left to right direction
   skinparam DefaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateFontStyle bold

   state "Processed Experiment\nOutputs" as proc #lightcyan {
      state "file 0" as filep0 #darkturquoise
      state "file 1" as filep1 #limegreen
      state "..." as filepx #green
      state "file k" as filepk #lightseagreen

      filepx -[hidden]r-> filepk
      filep1 -[hidden]r-> filepx
      filep0 -[hidden]r-> filep1

   }

   state "Intra-Experiment\nProducts" as prod #lightcyan {
      state "product 0" as productp0 #darkturquoise
      state "product 1" as productp1 #limegreen
      state "..." as productpx #green
      state "product k" as productpk #lightseagreen

      productpx -[hidden]r-> productpk
      productp1 -[hidden]r-> productpx
      productp0 -[hidden]r-> productp1
   }

   filep0 --> productp0
   filep1 --> productp1
   filepk --> productpk
   filepx --> productpx

There isn't really any dataflow for intra-experiment products, because there is
a 1:1 mapping between the :term:`Processed Output Data` file and the
:term:`Product`: all the data needed to generate a given product is within a
single file.

Inter-Experiment Dataflow
=========================

Inter-experiment processing in stage4 is :term:`Data Collation`, but this time
at the level of :term:`Experiments <Experiment>` rather the :term:`Experimental
Runs <Experimental Run>`:

This process in stage 3 can be visualized as follows for a single
:term:`Batch Experiment`, using :term:`Experiment` as SCOPE. Input files in this case
are :term:`Processed Output Data`, and output files are :term:`Collated Output
Data` at the experiment level. Each output file is a summary of a batch
experiment along some axis of interest.

.. figure:: /figures/data-collation.png

Once processed, products can be generate directly from the inter-experiment
files with a 1:1 mapping as above.

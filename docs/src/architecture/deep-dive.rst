.. _usage/deep-dive:

=================================
SIERRA Pipeline Stages: Deep Dive
=================================

This page dives deeps into the high level design of each of the SIERRA pipeline
stages. You don't need to know any of this in order to use SIERRA successfully,
but it doesn't hurt.

.. _usage/deep-dive/stage1:

Stage 1
=======

To begin, take note of the following terminology:

- There are :math:`i` :term:`Experiments <Experiment>` in a :term:`Batch
  Experiment`.

- There are :math:`j` experimental runs in an experiment (for a total of
  :math:`i\times{j}` executable experimental runs).

- The "Generator Factory" abstractly refers to the various parts of the code
  that map cmdline arguments from strings into *Generators*. Generators are
  objects which can make modications to expdef files: removing elements, adding
  elements, and modifying element attributes. See :ref:`plugins/expdef` for for
  details.

Below is the execution flow of the first phase of stage 1: scaffolding the
batch experiment. The outputs of this phase include:

- A unique directory for each experiment in the batch experiment containing all
  inputs.

- A modified expdef template file unique to each experiment in the batch which
  contains modifications to the original ``--expdef-template`` from the
  ``--batch-criteria`` This file (probably) *cannot* be actually run by the
  selected engine (i.e., it is not well formed, yet).

.. plantuml::

   skinparam defaultTextAlignment center

   !theme reddress-lightblue

   ' Title configuration
   skinparam titleFontSize 48
   skinparam titleFontColor #black
   skinparam defaultFontolor #black
   skinparam ArrowThickness 3
   skinparam sequenceArrowThickness 3
   skinparam DefaultFontSize 32
   skinparam databaseFontStyle bold
   skinparam participantFontStyle bold
   skinparam sequenceMessageFontStyle bold
   skinparam actorFontStyle bold
   skinparam collectionsFontStyle bold
   skinparam backgroundcolor #transparent

   title Stage1 Execution: Scaffolding A Batch Experiment

   actor "User Inputs" as input
   [-> input: Cmdline Args
   [-> input: .yaml config
   participant "Generator Factory" as factory

   input --> factory: ~--batch-criteria

   collections "Plugins" as plugins
   create expdef as "In-memory\nExperiment Definition"
   input --> expdef : Read --expdef-template
   factory -> expdef : expdef changes from\n~--batch-criteria generator

   database  "Filesystem" as filesystem
   expdef -> filesystem : Write per-experiment\ntemplate


Below is the execution flow of the second phase of stage 1: generating each
experiment *within* the parent batch experiment, using the generated
per-experiment template from the previous phase. The outputs from this phase
include:

- A unique directory for each :term:`Experimental Run` in each experiment
  containing all inputs. These are files which can actually be *run* by the
  selected engine.

- A modified expdef template file unique to each experimental run in the
  experiment containing all modifications that SIERRA was directed to make
  through a combination of:

  - ``--controller``

  - ``--batch-criteria``

  - ``--engine``

  - ``--project``

  - ``controllers.yaml``


.. plantuml::

   !theme reddress-lightblue
   hide empty description

   ' Title configuration
   skinparam titleFontSize 48
   skinparam titleFontColor #black
   skinparam defaultFontolor #black
   skinparam ArrowThickness 3
   skinparam sequenceArrowThickness 3
   skinparam DefaultFontSize 32
   skinparam databaseFontStyle bold
   skinparam participantFontStyle bold
   skinparam sequenceMessageFontStyle bold
   skinparam actorFontStyle bold
   skinparam collectionsFontStyle bold
   skinparam backgroundcolor #transparent

   title Stage1 Execution: Generating Experiment 0...i Within A Batch

   actor "User Inputs" as input
   [-> input: Cmdline Args
   [-> input: Controller\n.yaml config

   participant "Generator\nFactory" as factory
   input --> factory: ~--controller
   input --> factory: ~--scenario

   participant "In-memory\nExperiment Definition" as expdef
   database  "Filesystem" as filesystem
   filesystem --> expdef : Read scaffolded\ntemplate file

   collections "Plugins" as plugins

   factory --> expdef : Controller support\nfrom .yaml config
   factory --> expdef : Joint\n~--controller + --scenario generator\nexpdef changes

   plugins --> expdef : Per-experiment --engine\nexpdef changes
   plugins --> expdef : Per-experiment --execenv\nexpdef changes

   plugins --> expdef : Per-run ~--engine\nexpdef changes
   plugins --> expdef : Per-run ~--project\nexpdef changes
   expdef -> filesystem: Write for each run 0...j

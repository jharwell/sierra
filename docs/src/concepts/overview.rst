.. SPDX-License-Identifier: MIT

.. _concepts/overview:

=================
Concepts Overview
=================

SIERRA's core concepts build on each other. This page explains how they fit
together; the linked pages go deeper on each one.

The Short Version
=================

You define **what to vary** (:ref:`experimental design <concepts/exp-design>`),
SIERRA instantiates that variation as a **batch of experiments** (:ref:`batch
criteria <concepts/batch-criteria>`), runs the batch through a **five-stage
pipeline** (:ref:`concepts/pipeline`), writes everything to a predictable
**directory tree** (:ref:`concepts/run-time-tree`), and passes data between
stages according to a consistent **dataflow model** (:ref:`concepts/dataflow`).

.. plantuml::
   :caption: How SIERRA's core concepts relate to one another.

   @startuml
   !theme cerulean
   skinparam backgroundColor transparent
   skinparam defaultFontSize 48
   skinparam DefaultFontColor #black
   skinparam stateFontStyle bold

   skinparam defaultFontName sans-serif
   skinparam defaultFontStyle bold
   skinparam ArrowThickness 3
   skinparam RectangleBorderThickness 3

   rectangle "Experimental Design" as ED {
     rectangle "--controller"     as CTRL
     rectangle "--scenario"       as SCEN
     rectangle "--batch-criteria" as BC
   }

   rectangle "Batch Experiment" as BATCH {
     rectangle "exp0" as E0
     rectangle "exp1" as E1
     rectangle "expN" as EN
   }

   rectangle "Pipeline" as PIPE {
     rectangle "1. Generate"          as S1
     rectangle "2. Execute"           as S2
     rectangle "3. Post-process"      as S3
     rectangle "4. Generate products" as S4
     rectangle "5. Compare"           as S5
   }

   rectangle "Runtime Tree\n(--sierra-root)" as RT

   ED     --> BATCH : "instantiates"
   BATCH  --> S1    : "feeds"
   S1     --> S2
   S2     --> S3
   S3     --> S4
   S4     --> S5    : "optional"
   S1     --> RT    : "writes inputs"
   S2     --> RT    : "writes outputs"
   S3     --> RT    : "writes stats"
   S4     --> RT    : "writes graphs"

How the Concepts Relate
=======================

**Experimental design** is the starting point. You choose three things:

- A *controller* — the algorithm or configuration under test.
- A *scenario* — the environment or context it runs in.
- A *batch criteria* — the independent variable(s) to sweep.

The batch criteria is the active ingredient. It takes your experiment template
and applies a range of modifications to it — one per experiment — producing a
:term:`Batch Experiment`. A single criterion produces a 1-D sweep; two combined
criteria produce a 2-D Cartesian product.

**The pipeline** then takes over. It has five ordered stages, each consuming
what the previous stage produced:

1. **Generate** — transforms the template and batch criteria into individual
   experiment input files.
2. **Execute** — runs those inputs on the configured engine and execution
   environment, producing raw output files.
3. **Post-process** — reduces raw outputs across runs within each experiment
   into processed statistical files.
4. **Generate products** — turns processed files into graphs, videos, and other
   deliverables.
5. **Compare** — overlays products from multiple batch experiments for
   cross-controller or cross-scenario comparison. Not part of the default
   pipeline; run explicitly with ``--pipeline 5``.

Stages 1–4 are the default pipeline. Each stage is driven by one or more
plugins selected on the command line; the pipeline itself is just the
orchestrator.

**The runtime tree** is where all of this lands on disk. Every output from
every stage — inputs, raw outputs, statistics, graphs — goes under
``--sierra-root``, organized by project, controller, scenario, and batch
criteria. The directory names are deterministic, so re-running the same
invocation always maps to the same path. This is what makes SIERRA
reproducible: the full provenance of any result is encoded in its path.

**Dataflow** describes the transformations between stages. The key distinction
is scope: stage 3 operates at the level of *experimental runs* (reducing N runs
into one set of statistics per experiment), while stage 4 operates at the level
of *experiments* (collating across experiments in a batch to produce
inter-experiment products). Stage 5 then collates across batch experiments.

Where to Go Next
================

If you're new, read the concepts in this order:

1. :ref:`concepts/exp-design` — controllers, scenarios, and how batch criteria
   define the parameter space.
2. :ref:`concepts/pipeline` — what happens in each stage and which plugins are
   active.
3. :ref:`concepts/run-time-tree` — how to find your outputs on disk.
4. :ref:`concepts/dataflow` — how data is transformed between stages.
5. :ref:`concepts/batch-criteria` — the full detail on batch criteria syntax,
   directory naming, and graph types.

Once you have a mental model, :ref:`user-guide/running-experiments` shows how
to put it into practice.

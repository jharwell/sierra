.. _concepts/philosophy:

=================
Design Philosophy
=================

This document outlines the core ideas behind SIERRA's design. Understanding
these helps explain *why* SIERRA works the way it does — including choices that
might initially seem overly rigid or opinionated.

Single Input, Multiple Output
=============================

During stage 1, SIERRA generates multiple experiments from a single template
input file specified on the command line. It does not follow any
references or includes within that file, which simplifies generation and
improves reproducibility (for example, it avoids subtle errors caused by a ROS
``<include>`` resolving differently across systems). SIERRA *does* support
flattening an input file tree into a single file; see :ref:`plugins/expdef`.

Low Floor, No Ceiling
=====================

SIERRA is designed so that things work as much out-of-the-box as possible (low
floor), while not compromising configurability/extensibility for more advanced
users (no ceiling).

.. list-table::
   :header-rows: 1

   * - Decision
     - Rationale
     - Supports

   * - Don't modify user directory structures
     - :term:`Experimental Runs <Experimental Run>` produce their own directory
       structure — flat or deeply nested. SIERRA preserves that structure during
       stages {3,4}, following the Principle of Least Surprise and making it
       easy to pipe SIERRA outputs into existing scripts with minimal changes.
     - Low floor

   * - Wrap engine CLIs rather than reimplementing them
     - For :ref:`plugins/engine` and :ref:`plugins/execenv`, SIERRA translates
       users' original invocation commands rather than reimplementing engine
       APIs. All engines and execution environments have a CLI; not all have
       Python bindings. This choice keeps integration predictable.
     - Low floor

   * - Maximally configurable
     - SIERRA exposes relevant settings as configuration wherever possible,
       even if most users will never change the defaults. This ensures nothing
       is hardwired that a sufficiently advanced project might need to control.
     - No ceiling

   * - Maximize reusability
     - When used properly, you should *never* need to copy-paste YAML
       configuration or Python code between projects, engines, or scenarios.
       The upfront configuration investment pays off at scale.
     - No ceiling

   * - Separate processing from product generation
     - Stage 3 post-processes raw run outputs into normalised,
       statistics-bearing files. Stage 4 reads *only* those files to generate
       graphs and deliverables. This means you can re-run stage 4 with
       different graph configuration (title, axis range, additional lines) in
       seconds, without re-running experiments or reprocessing data. Each stage
       4 deliverable has a single, well-defined input source.
     - Low floor, No ceiling

**Internal implementation conventions** (relevant to contributors):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Convention
     - Rationale

   * - Assert often, fail early
     - If SIERRA encounters a condition it cannot handle, it aborts via an
       uncaught exception or ``assert()`` rather than attempting recovery. This
       gives users confidence that a non-crashing run is likely correct. As a
       corollary, any ``try``/``except`` blocks should catch and handle errors
       locally — never rely on exceptions propagating up to be caught at a
       higher level.

Never Delete Things
===================

Experimental data is hard-won. SIERRA therefore refuses to delete or overwrite
anything in stages {1,2} without explicit permission, because losing those
outputs in a later stage would be irreversible. Files generated in stages
{3,4,5} are derived from stage {1,2} outputs and can be safely regenerated, so
SIERRA will overwrite them freely. To override the protection on stages {1,2},
pass :ref:`--exp-overwrite<src/reference/cli:sierra---exp-overwrite>`.

Swiss Army Pipeline
===================

SIERRA's 5-stage :ref:`pipeline <concepts/pipeline>` is designed to be run in
any subset. You should be able to re-run only stage 4 after tweaking a graph
config, or only stages {3,4} after a fresh post-processing pass, without
friction.

This is achieved through several structural choices:

- Stage 3 (processing) and stage 4 (product generation) are kept separate, so
  re-generating products never requires re-processing raw data.

- Stage 4 products are each sourced from a single input file, not assembled
  from multiple files at generation time.

- Each pipeline stage is transactional at the file level: it reads from and
  writes to files on disk, rather than keeping state in memory. This makes
  arbitrary stage subsets composable.

- The :ref:`concepts/run-time-tree` uses human-readable, non-hashed directory
  names, so researchers can inspect, copy, or hand off data at any stage
  without needing SIERRA to interpret it.

Separation of Data Types
========================

Statistics generated during stage 3 are stored in *separate* files from the
underlying data, even when the chosen
:ref:`--storage<src/reference/cli:sierra---storage>` or
:ref:`--prod<src/reference/cli:sierra---prod>` plugin could accommodate them
in a single file. The reasons are:

- **Readability.** For 2D and higher-dimensional data, separating statistics
  from raw values makes both files easier to inspect.

- **Memory footprint.** If a user is generating a 2D heatmap, any standard
  deviation columns in the source file are irrelevant and would waste memory
  unnecessarily if co-located with the data.

Logo Design Rationale
=====================

The logo is actually well-thought out/not something random which "looked cool".

**Core Concept: "Research Compiler"**

SIERRA turns research queries into executable experiments and reproducible
outputs.  The logo represents a structured system that transforms research
inputs into deterministic results. It encodes the transformation pipeline::

   Research Inputs -> SIERRA Compiler   -> Structured Experiments
        (nodes)      (segmented system)      (grid)

Or more simply::

   Research Intent -> Automated Experiments -> Reproducible Results


And communicates (hopefully):

- serious research tooling
- automation infrastructure
- deterministic pipelines
- modular architecture
- reproducibility

**Circular Frame -> Execution Environment**

The outer segmented circle represents the controlled framework environment.

Meaning:

- Encapsulation of the research pipeline
- Deterministic system boundaries
- Reproducible execution

The segmentation hints at:

- pipeline stages
- modular plugin architecture
- execution phases

It suggests ordered computation happening inside a system.


**Arc Segments -> Pipeline Stages**

The curved arcs represent progressive transformation through the pipeline
stages. The arcs imply motion and flow, but within a controlled system rather
than a loose pipeline. This reinforces:

- deterministic automation
- reproducible research workflows

**Grid of Squares -> Structured Outputs**

The central grid represents compiled experimental artifacts.  Interpretations
include:

- parameter sweep results
- experiment matrices
- structured datasets
- reproducible experiment outputs

The squares are uniform, aligned, and deterministic. They contrast with
incoming nodes (inputs). Visually this communicates::

   unstructured ideas -> structured results

**Node Dots -> Research Inputs**

The dots on the left represent incoming research queries or parameters.  They
symbolize:

- experiment parameters
- datasets
- configuration inputs
- plugin modules

Different sizes suggest different input types and expanding parameter sweeps.
The dots converge toward the structured grid.


**Directional Flow -> Compilation**

The overall layout subtly moves left to right::

   inputs -> compilation -> results

Nodes appear on the left and structured outputs appear on the right.

This visually encodes the concept::

   Research idea -> SIERRA compilation -> Reproducible experiments

**Blue Color Palette -> Engineering and Research**

The color scheme reinforces the technical positioning.

Blue suggests:

- scientific rigor
- trust
- infrastructure software
- engineering systems

Gradients subtly suggest transformation and computation.

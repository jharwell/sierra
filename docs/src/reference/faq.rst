.. _faq:

===
FAQ
===

Getting Started
===============

#. Q: I'm really confused by all the terminology that SIERRA uses — how can I
   better understand the documentation?

   A: See the :doc:`/src/glossary` for all terms SIERRA defines specific names
   for. Reading it before anything else is strongly recommended.

#. Q: I'm getting an error about the output directory for my simulation run
   being missing. I told SIERRA where outputs should be created by following
   :ref:`tutorials/project/config`.

   A: SIERRA does *not* create the output directory for a simulation run — that
   is the responsibility of the :term:`Engine` and/or :term:`Project`. SIERRA
   only reads outputs from the specified location.

Running The Pipeline
====================

#. Q: How do I run a non-default set of pipeline stages, such as {3,4}?

   A: ``sierra-cli ... --pipeline 3 4``

   .. IMPORTANT:: Before stage X can run without crashing, you (probably) need
                  to have successfully completed stage X-1. Pipeline stages
                  build on each other — this is a logical limitation, not a bug.

#. Q: Do I need to re-run my experiments if I want to tweak a generated graph?

   A: No. Experiment execution is stage 2; graph generation is stage 4. To
   adjust a graph's title, formatting, or lines, just re-run stage 4 via
   ``--pipeline 4``. See :ref:`usage/pipeline` for details.

#. Q: How do I resume an experiment killed by an HPC scheduler for exceeding
   its time limit?

   A: Re-run SIERRA with the same arguments, adding ``--exec-resume``. SIERRA
   will pick up where it left off. See :ref:`usage/cli` for more info.

#. Q: SIERRA does not overwrite the input configuration for my experiment /
   SIERRA won't run my experiments again after they ran the first time — why?

   A: This is by design. SIERRA never deletes data in stages {1,2} that could
   result in lost experimental results in later stages. Files generated in
   stages {3,4,5} are derived from earlier results and can be safely
   overwritten. If you are sure you want to overwrite stages {1,2} outputs, pass
   ``--exp-overwrite``. See also :ref:`philosophy`.

Debugging
=========

#. Q: SIERRA crashed or hung — why?

   A: The most common cause of a crash is that stage X-1 of the pipeline did
   not successfully complete before you ran stage X. Check that all prior stages
   finished cleanly.

   If SIERRA hangs specifically during stage {3,4}, the most likely cause is
   inconsistent run outputs: not all runs produced CSV files of the same shape
   (same number of rows and columns). SIERRA does not sanitize run outputs
   before processing and relies on uniform CSV shapes for statistics generation.
   Depending on the inconsistency, you may see a hang or a crash as it waits for
   a subprocess that already failed.

#. Q: SIERRA fails to run on my HPC environment?

   A: The most likely reason is missing environment variables. See
   :ref:`plugins/execenv/hpc` for details on what is required.

#. Q: SIERRA doesn't generate any graphs during stage 4 / the graph I want is
   missing.

   A: SIERRA matches the stem of an output CSV file against the stem in a
   ``.yaml`` configuration file — if they differ, no graph is generated. Run
   SIERRA with ``--log-level=TRACE`` during stage 4 to see exactly which graphs
   are being generated and which are skipped due to a missing source CSV.

#. Q: SIERRA can't find a module it should be able to find via
   :envvar:`SIERRA_PLUGIN_PATH` or :envvar:`PYTHONPATH`. I know the module path
   is correct — why?

   A: If both environment variables are set correctly, the cause is likely a
   failing import *inside* the module. Diagnose it with::

     python3 -m full.path.to.module

   When Python loads modules dynamically it suppresses import errors, saying
   only "can't find the module" rather than printing the real cause. This
   command surfaces those hidden errors.

ARGoS-Specific
==============

#. Q: How do I prevent SIERRA from stripping ARGoS XML tags for
   sensors/actuators?

   A: Use ``--with-robot-leds``, ``--with-robot-rab``, or
   ``--with-robot-battery``. Additional options may be added in the future.

Project & Plugin Design
=======================

#. Q: I need to apply very precise configuration that is too specific for a
   :term:`Batch Criteria`. How can I do this?

   A: Create one or more controller categories/controllers in
   ``controllers.yaml``. Within each category and controller you can specify
   arbitrary changes to the ``--expdef-template`` (adding, removing, or
   modifying tags). This is a good way to apply tricky configuration that
   doesn't fit a batch criteria, or to try "quick and dirty" changes before
   codifying them as a Python class. See :ref:`tutorials/project/config` for
   details.

#. Q: I have multiple projects that share batch criteria/generators/etc. How
   can I share code between them?

   A: There are three approaches depending on what you need to share and whether
   it must be selectable via ``--batch-criteria``. See
   :ref:`tutorials/project/project` for a full walkthrough of each option,
   including a "common project" pattern, a separate Python package approach, and
   a namespace-lifting technique for ``--batch-criteria``-selectable classes.

.. _reference/faq:

===
FAQ
===

Getting Started
===============

#. Q: I'm really confused by all the terminology that SIERRA uses — how can I
   better understand the documentation?

   A: See the :ref:`reference/glossary` for all terms SIERRA defines specific
   names for. Reading it before anything else is strongly recommended.

#. Q: I'm getting an error about the output directory for my simulation run
   being missing. I told SIERRA where outputs should be created by following
   :ref:`tutorials/project/config`.

   A: SIERRA does *not* create the output directory for a simulation run — that
   is the responsibility of the :term:`Engine` and/or :term:`Project`. SIERRA
   only reads outputs from the specified location.

Running The Pipeline
====================

See :ref:`user-guide/running-experiments` for common invocation patterns,
including running a subset of stages, resuming after a crash, and
discarding and regenerating a batch.

Debugging
=========

See :ref:`user-guide/debugging-and-logging` for common failure patterns,
plugin import diagnostics, and techniques for isolating problems with a
minimal batch.

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
   it must be selectable via
   :ref:`--batch-criteria<src/reference/cli:sierra---batch-criteria>`. See
   :ref:`tutorials/project/project` for a full walkthrough of each option,
   including a "common project" pattern, a separate Python package approach, and
   a namespace-lifting technique for
   :ref:`--batch-criteria<src/reference/cli:sierra---batch-criteria>`-selectable classes.

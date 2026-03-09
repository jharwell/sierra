.. _contributing:

============
Contributing
============

Types of Contributions
======================

All types of contributions are welcome: bug fixes, adding unit/integration
tests, documentation improvements, and more. If you only have a little time
or are new to SIERRA, the issue tracker is a good place to find approachable
tasks. If you want to contribute something more substantial, see :ref:`roadmap`
for big-picture ideas about where the project is headed.

Code Contributions
==================

Writing the Code
----------------

#. Install development packages for SIERRA (from the SIERRA repo root)::

     uv sync . --extra devel

#. Make your changes. For non-trivial changes, open an issue first to discuss
   the approach before writing code.

#. Run the full check suite before committing or pushing. Fix any errors
   *you* have introduced. Some checkers (such as pylint) may still report
   pre-existing warnings — cleaning those up is always ongoing work::

     uv run nox

.. note::

   Two typos to watch for in the existing codebase: "pipline" (should be
   "pipeline") and "layed" (should be "laid"). Fix them if you see them.

Source Code Layout
------------------

Understanding how SIERRA is laid out makes it easier to find implementation
details and see how components fit together.

.. code-block:: text

   sierra/
   ├── core/                    # Engine- and project-independent SIERRA core
   │   ├── experiment/          # Interfaces and bindings for use by plugins
   │   ├── generators/          # Controller and scenario generators
   │   ├── graphs/              # Graph generation (linegraphs, heatmaps, etc.)
   │   ├── models/              # Model interfaces
   │   ├── pipeline/            # 5-stage pipeline implementation
   │   ├── ros1/                # Common ROS1 bindings
   │   └── variables/           # Experimental variable generators
   ├── plugins/                 # Bundled plugins (engines, execenvs, storage, etc.)
   └── docs/                    # Sphinx documentation source

Documentation Contributions
===========================

This section defines the **structure, responsibilities, and contribution rules**
for the SIERRA documentation. Its goal is to ensure that:

- Documentation remains **organized and maintainable**
- New pages are added to the **correct section**
- Content **is not duplicated across sections**
- Readers can follow a **clear learning path**

When contributing new documentation, always consult this guide first. The TL;DR
version to maintain clear and scalable docs:

- **Concepts explain ideas**
- **User Guide explains workflows**
- **Tutorials demonstrate real tasks**
- **Plugins describe system components**
- **Architecture explains implementation**
- **Reference provides lookup documentation**

Following these guidelines will ensure SIERRA documentation remains
clear, consistent, and easy to maintain as the project evolves.

Documentation Philosophy
------------------------

The SIERRA documentation is structured to support a **progressive learning
path**:

::

    Learn → Understand → Use → Extend → Reference

Mapped to documentation sections:

::

    Getting Started
          ↓
    Concepts
          ↓
    User Guide
          ↓
    Tutorials
          ↓
    Plugins
          ↓
    Architecture
          ↓
    Reference

Each section answers a **different type of question**. Contributors should
ensure that new documentation fits the purpose of its section.

Colour Scheme
-------------

This is a general guide so I don't forget--deviate when necessary.

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Role
     - Colour
     - Notes
   * - Stage headers
     - ``#e8daef``
     - Purple; container header, distinct from all data-flow colours
   * - Input artifacts
     - ``#ebf5fb``
     - Near-white blue
   * - Output artifacts
     - ``#5dade2``
     - Mid-dark blue; clearly a step darker than input
   * - Active plugins
     - ``#fdebd0``
     - Amber
   * - Compute resources
     - ``#a9dfbf``
     - Green; distinct from the blue data-flow family

Top-Level Documentation Structure
---------------------------------

::

    docs/

      index

      getting-started/
      concepts/
      user-guide/
      tutorials/
      plugins/
      architecture/
      reference/



Section Responsibilities
========================

Getting Started
---------------

Help new users run SIERRA for the first time. Content should include:

- motivation and goals of SIERRA
- installation instructions
- minimal working examples
- basic environment setup

Content should **not** include:

- deep conceptual explanations
- plugin descriptions
- architecture details


Concepts
--------

Explain the **mental model of SIERRA**.  Concept pages explain **what things
mean**, not how to configure them.

Concepts should describe:

- how SIERRA organizes experiments
- how data flows through the system
- how parameter sweeps work
- how experiments are structured

Concepts should **not** describe:

- CLI commands, *especially* not cross-referencing them
- plugin configuration
- implementation details

Owned by the **Concepts section**::

    pipeline
    runtime tree
    dataflow
    batch criteria
    experimental design

Other sections should **link to concept pages rather than repeating them**.

User Guide
----------

Teach users how to **accomplish tasks with SIERRA**.

User guide pages should follow the **experiment workflow**; that is, *how* to do
things:

- how experiments are defined
- how experiments are run
- how results are processed
- how outputs are generated
- how experiments are debugged

User guide pages should **not** contain:

- plugin internals
- full plugin specifications
- deep architectural explanations

Instead, link to plugin documentation.

Owned by the **User Guide**::

    running experiments
    experiment templates
    variable usage
    experiment debugging
    experiment workflows

Tutorials
---------

Provide **step-by-step walkthroughs** for building real workflows.  Tutorials
should:

- demonstrate realistic tasks
- walk through concrete examples
- include step-by-step instructions

Tutorials should **not** attempt to document every feature.

Plugins
-------

Document the capabilities of **individual plugin types and plugins**.  Each
plugin page should describe:

- purpose of the plugin
- configuration options
- inputs
- outputs
- example usage

Plugin pages should **not explain the pipeline stage** they belong to.  That
explanation belongs in the user guide.

Owned by the **Plugins section**::

    experiment definition plugins
    execution engines
    execution environments
    processor plugins
    product generators
    comparator plugins
    storage plugins



Architecture
------------

Explain **how SIERRA is implemented internally**.  Architecture documentation is
intended for:

- contributors
- maintainers
- advanced users

These pages may reference:

- concepts
- plugins
- internal system design

Owned by the **Architecture section**::

  execution model
  plugin system internals
  system design

Reference
---------

Provide **precise lookup documentation**. Reference documentation should
include:

- command definitions
- environment variables
- terminology definitions

Reference documentation should **not contain tutorials or explanations**.


Rules for Adding New Documentation
==================================

Before adding a new page, ask:

1. Is this explaining a **concept**?
2. Is this teaching a **task or workflow**?
3. Is this documenting a **specific plugin**?
4. Is this explaining **internal implementation**?
5. Is this a **reference lookup page**?

Then place the documentation accordingly.



Common Documentation Mistakes
=============================

Avoid the following problems:

- Duplicate concept explanations: Do not re-explain concepts such as the
  pipeline or runtime tree in multiple places.  Instead, link to the concepts
  section.

- Plugin details in the user guide: User guide pages should not list every
  plugin option. Link to plugin documentation instead.

- Architecture details in user documentation: Avoid describing implementation
  details in the user guide.

- Narrative content in reference pages: reference pages should contain only
  **precise lookup material**.

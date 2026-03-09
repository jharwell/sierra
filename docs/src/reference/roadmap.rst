.. _roadmap:

===================
Development Roadmap
===================

This page outlines big-picture improvements under consideration for SIERRA.
Items are separated into known limitations to fix (SIERRA 2.0) and aspirational
new capabilities (beyond 2.0). For smaller, concrete tasks see the issue
tracker.


Documentation Improvement
=========================

This section outlines recommended structural improvements to the SIERRA
documentation.  The goal is to improve navigation, reader onboarding, and
long‑term maintainability of the documentation. The recommendations focus
specifically on **information architecture** (placement, section
responsibilities, and reader flow), rather than wording or style.

The current documentation contains strong technical content, but the
organization sometimes makes it difficult for new users to understand where to
begin and how different parts of the system relate to one another.

The following recommendations describe structural changes that will improve the
learning path and clarify the role of each section.

1. Clarify the Top‑Level Documentation Structure
------------------------------------------------

Current Structure
~~~~~~~~~~~~~~~~~

The documentation currently contains the following major sections:

- getting-started
- concepts
- architecture
- plugins
- tutorials
- user-guide
- reference

While these are all reasonable categories, the *responsibilities of each section
overlap* in several places.

Recommended Structure
~~~~~~~~~~~~~~~~~~~~~

The documentation should follow a clearer progression:

- getting-started
- concepts
- user-guide
- tutorials
- plugins
- architecture
- reference

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

This structure aligns with the typical user journey:

1. Learn what the system is.
2. Understand the core ideas.
3. Learn how to use it.
4. Follow examples.
5. Extend the system.
6. Understand internal implementation.
7. Look up detailed references.

This creates a **progressive learning model** rather than a set of disconnected pages.



2. Streamline the Getting Started Section
-----------------------------------------

Current Content
~~~~~~~~~~~~~~~

The section currently contains:

- why-sierra
- installation
- setup
- quickstart
- trial

Issue
~~~~~

Some of these pages overlap conceptually, particularly *quickstart* and *trial*.

Recommendation
~~~~~~~~~~~~~~

Reduce the section to:

- why-sierra
- installation
- quickstart
- setup

Quickstart should already produce a working experiment run.

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

A concise getting-started section reduces friction for new users and ensures that
they can quickly run their first experiment without navigating multiple introductory pages.



3. Add a Concepts Overview Page
-------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

The concepts section contains several well-written technical topics:

- pipeline
- dataflow
- runtime-tree
- batch-criteria
- experimental-design

However, there is no single page explaining how these ideas fit together.

Recommendation
~~~~~~~~~~~~~~

Add a page:

::

    concepts/overview

This page should explain:

- the experiment lifecycle
- the runtime tree
- the pipeline stages
- how plugins participate in execution

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Readers often struggle when concepts are introduced independently without showing
their relationships. An overview page provides the **mental model needed to interpret
the rest of the documentation**.



4. Strengthen the User Guide
----------------------------

Current Situation
~~~~~~~~~~~~~~~~~

The user guide currently includes only a small set of operational pages.

However, SIERRA has a complex workflow that includes experiment definition,
parameter sweeps, postprocessing, and result comparison.

Recommendation
~~~~~~~~~~~~~~

Expand the user guide to include:

::

    user-guide/
        project-structure
        running-experiments
        defining-experiments
        experiment-templates
        variables
        batch-criteria
        postprocessing
        product-generation
        comparing-results
        debugging-and-logging

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

The user guide should provide a **complete operational workflow**.
Currently, many usage details are scattered across concepts and plugin pages.
Consolidating them improves discoverability and usability.



5. Improve Tutorial Organization
--------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

The tutorials include material about:

- project plugins
- generators
- hooks
- new batch criteria
- plugin development

However, these tutorials appear more like developer notes than guided learning experiences.

Recommendation
~~~~~~~~~~~~~~

Reframe tutorials around concrete learning goals:

::

    tutorials/
        your-first-project
        creating-batch-criteria
        writing-project-plugins
        writing-sierra-plugins

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Tutorials should walk readers through **real tasks step-by-step**.
Reframing them around tasks rather than internal features makes them more accessible.



6. Introduce a Plugin System Overview
-------------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

Plugin documentation is organized by plugin type:

- engine
- execenv
- expdef
- proc
- prod
- compare
- storage

While this is logical for experienced users, new readers may not understand the role
of each plugin category.

Recommendation
~~~~~~~~~~~~~~

Add a page:

::

    plugins/overview

This page should describe:

- the plugin architecture
- plugin categories
- how plugins participate in the pipeline

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Readers need context before diving into individual plugin categories.
An overview prevents confusion and reduces cognitive load.



7. Separate Plugin Usage from Plugin Implementation
---------------------------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

Plugin documentation currently mixes:

- how to use plugins
- how plugins are implemented internally

Recommendation
~~~~~~~~~~~~~~

Use the following separation:

Plugins Section:
    How users enable and configure plugins.

Architecture Section:
    How plugins are implemented and integrated internally.

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Separating usage from implementation keeps the documentation relevant
to both **users and developers** without overwhelming either group.



8. Clarify the Architecture Section
-----------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

Architecture pages describe:

- execution model
- plugin system
- internal system design

These pages are valuable but are not necessary for new users.

Recommendation
~~~~~~~~~~~~~~

Ensure architecture pages appear later in the documentation hierarchy
and are clearly labeled as **advanced or developer-oriented**.

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Readers who only want to run experiments should not need to understand
internal execution mechanics.



9. Clean Up the Reference Section
---------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

The reference section includes a mix of content types:

- CLI documentation
- environment configuration
- glossary
- FAQ
- philosophy
- roadmap
- contributing
- citing

Recommendation
~~~~~~~~~~~~~~

Keep only true reference material:

::

    reference/
        cli
        subprograms
        environment
        glossary
        citing

Move other pages to more appropriate locations.

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Reference sections should contain **lookup material**, not narrative explanations
or project metadata.



10. Move Philosophy to the Concepts Section
-------------------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

The philosophy page currently lives under reference.

Recommendation
~~~~~~~~~~~~~~

Move it to:

::

    concepts/philosophy

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Philosophy explains design motivations and belongs with conceptual material,
not reference documentation.



11. Add a System Overview Page
------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

Understanding the entire SIERRA system currently requires reading multiple pages
across several sections.

Recommendation
~~~~~~~~~~~~~~

Add a top-level overview page linked from the documentation landing page.

The overview should summarize:

- experiment definitions
- runtime tree structure
- pipeline stages
- plugin roles
- generated outputs

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

A system overview provides readers with the **big picture**, allowing them to
navigate the rest of the documentation with a clear mental model.



12. Add a Project Structure Page
--------------------------------

Current Situation
~~~~~~~~~~~~~~~~~

The documentation does not clearly describe the layout of a typical SIERRA project.

Recommendation
~~~~~~~~~~~~~~

Add a page:

::

    user-guide/project-structure

This page should explain:

- expected directory layout
- experiment configuration files
- template locations
- batch definitions
- output directories

Why This Change Helps
~~~~~~~~~~~~~~~~~~~~~

Most users begin by exploring example projects.
Providing a clear explanation of project layout helps users understand how
to organize their own experiments.

SIERRA 2.0
==========

These are known limitations of the current design that need addressing before
a 2.0 release can be cut.

High-Dimension Batch Criteria Support
-------------------------------------

This is in the code already for 2D->1D slicing, in a very hacky/brittle way
which probably doesn't work anymore. This needs to be reworked, tested, and
documented. Being able to e.g., slice a 3D batch criteria along 2 dimensions to
generate heatmaps would be an awesome upgrade. This will require changes to some
of the stage 3 statistics code too.

Stage {4,5}: Rework Deliverable Configuration
---------------------------------------------

The current mechanism for specifying what data goes on which graphs in stages
{4,5} is clunky — it was developed incrementally for thesis work and patched as
needed since. In practice you *can* slot in arbitrary deliverable generation
code, but it feels like an afterthought rather than a first-class design.

The target state is:

- Deliverable generation for stage 4 is defined on a per-plugin basis. For
  example, the ``hv`` plugin would own its inter/intra-experiment graph
  definitions rather than sharing a single global config.

- Configuration remains YAML-based, but each plugin has its own configuration
  file rather than all plugins sharing one.

Stage {4,5}: New Tutorials
--------------------------

The existing tutorials and examples show nothing of stages {4,5} from a
user workflow perspective. The question *"How do I use SIERRA to generate what
I actually care about?"* is not currently answered anywhere in the docs. Several
new tutorials are needed covering:

- How to write hooks and plugins for stages {4,5}.
- How to configure deliverable generation as an end user.
- Worked examples showing stage 4 output for common research outputs (paper
  figures, comparison tables, videos).

Beyond SIERRA 2.0
=================

Once the 2.0 release is complete, the foundation will be in place for the
following. These are aspirational and not yet scheduled.

New Engine Plugins
------------------

**ROS2** — Would require a new engine plugin for each simulator SIERRA currently
supports under ROS1, plus a new ROS2 real-robot plugin. Since ROS2 retains XML
support, this should be relatively self-contained.

**WeBots** — Would require a single new engine plugin. Self-contained.

**NetLogo** — Would require a single new engine plugin. NetLogo may accept XML
input, which would simplify integration. One non-trivial aspect: NetLogo
handles parallel runs internally, unlike any engine currently supported by
SIERRA, so some additional configuration may be needed. Adding NetLogo support
would also broaden SIERRA's appeal beyond robotics to agent-based modelling
more generally.

Expanded Computational Workflows
---------------------------------

It would be useful to evaluate user code computationally alongside its
scientific outputs. Concrete ideas:

- **Execution timing** — Treat the ``statistics/exec`` folder as first-class
  data; average and graph how long each algorithm/controller takes to run.

- **Performance profiling** — Wrap engine invocations with a profiling tool
  (e.g., vtune, gprof, kcachegrind), average the profiles in stage 3, and
  generate reports in stage 4.

- **Principal component analysis** — For N-dimensional batch criteria,
  decompose the contribution of each dimension to observed performance.

- **Regression testing** — Given a set of CLI arguments and a pointer to
  blessed reference data from a previous experiment, generate a pass/fail
  report. Because the blessed data lives in SIERRA's directory structure,
  this should be straightforward to implement.

Stage 1 Rewrite in Rust
------------------------

Stage 1 (experiment generation) is a good candidate for a Rust rewrite: it
does not depend on any "exotic" third-party libraries like pandas or holoviews,
and a Rust implementation would substantially speed up generating large
experiment batches. Other stages are less clear-cut candidates, since they do
rely on such libraries.

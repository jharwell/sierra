.. _roadmap:

===================
Development Roadmap
===================

This page outlines big-picture improvements under consideration for SIERRA.
Items are separated into known limitations to fix (SIERRA 2.0) and aspirational
new capabilities (beyond 2.0). For smaller, concrete tasks see the issue
tracker.

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

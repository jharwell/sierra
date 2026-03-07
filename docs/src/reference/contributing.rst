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

Mechanics
=========

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

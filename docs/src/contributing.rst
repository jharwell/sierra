.. _contributing:

============
Contributing
============

Types of contributions
======================

All types of contributions are welcome: bugfixes, adding unit/integration tests,
etc. If you're only have a little bit of time and/or are new to SIERRA, looking
at the issues is a good place to look for places to contribute. If you have more
time and/or want to give back to the community in a bigger way, see
:ref:`roadmap` for some big picture ideas about where things might be going, and
help shape the future!

Mechanics
=========

Writing the code
----------------

#. Install development packages for SIERRA (from the SIERRA repo root)::

     uv sync . --extra devel

#. Do development!

#. Run ``nox`` to check most things prior to commiting/pushing your changes. If
   there are errors *you* have introduced, fix them. Some checkers (such as
   pylint), will still report errors, as cleaning up the code is always a work
   in progress::

     uv run nox


SIERRA Source Code Directory Structure
--------------------------------------

It is helpful to know how SIERRA is layed out, so it is easier to see how things
fit together, and where to look for implementation details if (really `when`)
SIERRA crashes. So here is the directory structure, as seen from the root of the
repository.

- ``sierra`` - The SIERRA python package

  - ``core/`` - The parts of SIERRA which independent of the :term:`Project`
    being run.

    - ``experiment/`` - Various interfaces and bindings for use by plugins.

    - ``generators/`` - Generic controller and scenario generators used to
      modify template expdef files to provide the setting/context for running
      experiments with variables.

    - ``graphs/`` - Generic code to generate graphs of different types.

    - ``models/`` - Model interfaces.

    - ``pipeline/`` - Core pipline code in 5 stages (see
      :ref:`usage/pipeline`).

    - ``ros1/`` - Common :term:`ROS1` bindings.

    - ``variables/`` - Generic generators for experimental variables to modify
      template expdef files in order to run experiments with a given controller.

  - ``plugins/`` - Plugins which provide broad customization of SIERRA, and
    enables it to adapt to a wide variety of engines and experiment outputs.

- ``docs/`` - Contains sphinx source code to generate these shiny docs.

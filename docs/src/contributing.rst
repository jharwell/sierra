.. _ln-contributing:

============
Contributing
============

To contribute to the SIERRA core, in you should follow the general workflow
outlined in :xref:`LIBRA`. For the static analysis step:

#. Install additional dependencies::

     pip3 pytype pylint mypy

#. Run the following on the code from the root of SIERRA::

     pytype -k sierra

   Fix ANY and ALL errors that arise, as SIERRA should get a clean bill of health
   from the checker.

#. Run the following on any module directories you changed, from the root of
   SIERRA::

     pylint <directory name>

   Fix ANY errors your changes have introduced (there will probably still be
   errors in the pylint output, because cleaning up the code is always a work in
   progress).

#. Run the following on any module directories you changed, from the root of
   SIERRA::

     mypy --ignore-missing-imports --warn-unreachable sierra

   Fix ANY errors your changes have introduced (there will probably still be
   errors in the my output, because cleaning up the code is always a work in
   progress).

SIERRA Source Code Directory Structure
======================================

It is helpful to know how SIERRA is layed out, so it is easier to see how things
fit together, and where to look for implementation details if (really `when`)
SIERRA crashes. So here is the directory structure, as seen from the root of the
repository.

- ``sierra`` - The SIERRA python package

  - ``core/`` - The parts of SIERRA which are (mostly) agnostic to the project
    being run. This is not strictly true, as there are still many elements that
    are tied to _my_ projects, but decoupling is an ongoing process.

    - ``generators/`` - Generic controller and scenario generators used to
      modify template ``.argos`` files to provide the setting/context for
      running experiments with variables.

    - ``graphs/`` - Generic code to generate graphs of different types.

    - ``perf_measures/`` - Generic measures to compare performance of different
      controllers across experiments.

    - ``config/`` - Contains runtime configuration YAML files, used to fine tune
      how SIERRA functions: what graphs to generate, what controllers are valid,
      what graphs to generate for each controller, etc., which are common to all
      projects.

    - ``pipeline/`` - Core pipline code in 5 stages (see :ref:`ln-usage-pipeline`)

    - ``variables/`` - Genertic generators for experimental variables to modify
      template ``.argos`` files in order to run experiments with a given
      controller.

- ``scripts/`` - Contains some SLURM scripts that can be run on MSI. Scripts
  become outdated quickly as the code base for this project and its upstream
  projects changes, so scripts should not be relied upon to work as is. Rather,
  they should be used to gain insight into how to use SIERRA and how to craft
  your own script.

- ``templates/`` - Contains template ``.argos`` files. Really only necessary to
  be able to change configuration that is not directly controllable via
  generators, and the # of templates should be kept small.

- ``docs/`` - Contains sphinx scaffolding/source code to generate these shiny
  docs.

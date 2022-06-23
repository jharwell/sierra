.. _ln-sierra-contributing:

============
Contributing
============

To contribute to the SIERRA core, in you should follow the general workflow and
python development guide outlined in :xref:`LIBRA`. For the static analysis
step:

#. Install development packages for SIERRA (from the SIERRA repo root)::

     pip3 install .[devel]

#. Run the following on the code from the root of SIERRA::

     pytype -k sierra

   Fix ANY and ALL errors that arise, as SIERRA should get a clean bill of
   health from the checker.

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

  - ``core/`` - The parts of SIERRA which independent of the :term:`Project`
    being run.

    - ``experiment/`` - Various interfaces and bindings for use by plugins.

    - ``generators/`` - Generic controller and scenario generators used to
      modify template XML files to provide the setting/context for running
      experiments with variables.

    - ``graphs/`` - Generic code to generate graphs of different types.

    - ``models/`` - Model interfaces.

    - ``pipeline/`` - Core pipline code in 5 stages (see
      :ref:`ln-sierra-usage-pipeline`).

    - ``ros/`` - Common :term:`ROS` bindings.

    - ``variables/`` - Genertic generators for experimental variables to modify
      template ``.argos`` files in order to run experiments with a given
      controller.

  - ``plugins/`` - Plugins which provide broad customization of SIERRA, and
    enables it to adapt to a wide variety of platforms and experiment outputs.

- ``docs/`` - Contains sphinx source code to generate these shiny docs.

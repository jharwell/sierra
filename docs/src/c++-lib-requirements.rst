.. _ln-c++-lib-requirements:


=====================================
SIERRA Requirements for C++ Libraries
=====================================

SIERRA makes a few assumptions about how :term:`Experimental Runs<Experimental
Run>` using your C++ library can be launched, and how they output data. If your
code does not meet these assumptions, then you will need to make some (hopefully
minor) modifications to it before you can use it with SIERRA.

#. :term:`Experimental Runs<Experimental Run>` can be launched from `any`
   directory; that is, they do not require to be launched from the root of the
   code repository (for example).

#. All outputs for a single :term:`Experimental Run` will reside in a
   subdirectory in the directory that the run is launched from. For example, if
   a run is launched from ``$HOME/exp/research/simulations/sim1``, then its
   outputs need to appear in a directory such as
   ``$HOME/exp/research/simulations/sim1/outputs``. The directory within the
   experimental run root which SIERRA looks for simulation outputs is configured
   via YAML; see :ref:`ln-tutorials-project-main-config` for details.

#. All experimental run outputs are in a format that SIERRA understands within
   the output directory for the run. See :ref:`ln-storage-plugins` for which
   output formats are currently understood by SIERRA. If your output format is
   not in the list, never fear! It's easy to create a new storage plugin, see
   :ref:`ln-tutorials-plugin-storage`.


SIERRA Requirements for ARGoS C++ Libraries
===========================================

#. ``--project`` matches the name of the C++ library for the project
   (i.e. ``--project.so``). For example if you pass
   ``--project=project-awesome``, then SIERRA will tell ARGoS to search in
   ``proj-awesome.so`` for both loop function and controller definitions via XML
   changes. You *cannot* put the loop function/controller definitions in
   different libraries.

#. :envvar:`ARGOS_PLUGIN_PATH` is set up properly prior to invoking SIERRA.

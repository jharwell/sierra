.. _ln-c++-lib-requirements:


===========================================
SIERRA Requirements for ARGoS C++ Libraries
===========================================

SIERRA makes a few assumptions about how ARGoS :term:`Simulations<Simulation>`
using your C++ library can be launched, and how they output data. If your code
does not meet these assumptions, then you will need to make some (hopefully
minor) modifications to it before you can use it with SIERRA.

#. :term:`Simulations<Simulation>` can be launched from `any` directory; that
   is, they do not require to be launched from the root of the code repository
   (for example).

#. All outputs for a single :term:`Simulation` will reside in a subdirectory in
   the directory that the simulation is launched from. For example, if a
   simulation is launched from ``$HOME/exp/research/simulations/sim1``, then its
   outputs need to appear in a directory such as
   ``$HOME/exp/research/simulations/sim1/outputs``. The directory within the
   simulation root which SIERRA looks for simulation outputs is configured via
   YAML; see :ref:`ln-tutorials-project-main-config` for details.

#. All simulation outputs are in a format that SIERRA understands within the
   output directory for the simulation. See :ref:`ln-storage-plugins`
   for which output formats are currently understood by SIERRA. If your output
   format is not in the list, never fear! It's easy to create a new storage
   plugin, see :ref:`ln-tutorials-plugin-storage`.

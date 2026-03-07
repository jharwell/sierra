..
   Copyright 2026 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _user-guide/running-exp:

===================
Running Experiments
===================


Requirements For Project Code
=============================

SIERRA makes a few assumptions about how :term:`Experimental Runs<Experimental
Run>` using your C/C++ library can be launched, and how they output data. If
your code does not meet these assumptions, then you will need to make some
(hopefully minor) modifications to it before you can use it with SIERRA.

#. Project code uses a configurable random seed. While this is not strictly
   required, all code should do this for reproducibility. See
   :ref:`plugins/engine` for engine-specific details about random seeding
   and usage with SIERRA.

#. :term:`Experimental Runs<Experimental Run>` can be launched from *any*
   directory; that is, they do not require to be launched from the root of the
   code repository (for example).

#. All outputs for a single :term:`Experimental Run` will reside in a
   subdirectory in the directory that the run is launched from. For example, if
   a run is launched from ``$HOME/exp/research/simulations/sim1``, then its
   outputs need to appear in a directory such as
   ``$HOME/exp/research/simulations/sim1/outputs``. The directory within the
   experimental run root which SIERRA looks for simulation outputs is configured
   via YAML; see :ref:`tutorials/project/config` for details.

   .. IMPORTANT:: SIERRA does *not* create the output root for each experimental
                  run for you. This is to support workflows where output data is
                  stored in a database. Plus, most programming languages have a
                  "create this directory and all its parents as needed" call
                  which is trivial to add if needed.

#. All experimental run outputs are in a format that SIERRA understands within
   the output directory for the run. See :ref:`plugins/storage` for which output
   formats are currently understood by SIERRA. If your output format is not in
   the list, never fear! It's easy to create a new storage plugin, see
   :ref:`plugins/storage`.

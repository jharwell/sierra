.. SPDX-License-Identifier:  MIT

.. _req:

==========================
Requirements To Use SIERRA
==========================

This page details the parameters you must meet in order to be able to use SIERRA
in a more or less out-of-the-box fashion. Because SIERRA is highly modular, use
cases which don't meet one or more of the parameters described below can likely
still be accommodated with an appropriate plugin.

.. _req/os:

OS Requirements
===============

One of the following:

- Recent linux. SIERRA is tested with Ubuntu 22.04+, though it will probably
  work on less recent versions/other distros as well.

- Recent OSX. SIERRA is tested with OSX 12+, though it *might* work on less
  recent versions.


.. NOTE:: Windows is not supported currently. Not because it can't be supported,
          but because there are not current any engine plugins that which work
          on windows. SIERRA is written in pure python, and could be made to
          work on windows with minimal work.

Python Requirements
===================

Python 3.9+. Tested with 3.9-3.12. It may work for newer versions, probably
won't for older; as older versions become EOL support for them is dropped and no
effort is made at compatibility, in order to take advantage of newer language
features.

For all external plugins (e.g., those which don't come with SIERRA) which you
would want to define/use, they will have to be packaged according to the
guidance in :ref:`plugins/external`, specifically how module imports must be
structured w.r.t. dynamic modifications to ``sys.path`` to support arbitrary
plugin loading at runtime.

.. _req/exp:

Experimental Design Requirements
================================

.. _req/exp/arena-size:

Arena Size
----------

These requires only apply if you want to execute :term:`Experiments
<Experiment>` which have different arena sizes (e.g., you want to put the same #
of agents in increasingly large/small areas to figure out how their behavior
changes).

#. The experimental arena size for each :term:`Experiment` in all :term:`Batch
   Experiments <Batch Experiment>` is defined. For experiments which will run in
   simulation, this is usually obtained from the configured limits on the
   simulated space set in the simulator input files(s). If your simulation
   environment is more of a "treadmill" (i.e., it renders around agents as they
   move and is effectively infinite), then you will have to create some
   mechanism for a set size for the simulation.  For real-world experiments,
   this is usually just an estimate of the lab/test range space size.

   There are two ways in which the arena size used in experiments can be
   communicated to SIERRA, which SIERRA tries in the following order:

   #. Through :term:`Batch Criteria` defining the ``arena_dims()`` function. See
   :ref:`tutorials/project/new-bc` to see how to implement this method. This
   method also requires additional hooks to be defined in the
   :term:`Engine`--see :ref:`plugins/engine` for specifics.

   #. Through the cmdline, by encoding it as part of what is passed to
      ``--scenario``. See :ref:`tutorials/project/generators/scenario` to see
      how to implement this method.

   Both methods can be made to work equivalently, and can be mixed within and
   across engines and batch criteria. That is, you can define some experiments
   where the arena size is pulled from batch criteria, and some where it is
   pulled from ``--scenario`` within the same engine/project.

.. _req/expdef:

Experimental Definition Requirements
====================================

This section details restrictions on how experiments are defined from a provided
template file, with some restrictions depending on the file format (XML, JSON,
etc.).

General
-------

#. Strictly speaking, experimental inputs must be specified as a single file
   (``--expdef-template``); SIERRA uses this to generate multiple input files
   defining :term:`Experiments <Experiment>`; any configuration which isn't in
   the single input file cannot be modified by SIERRA, limiting effectiveness.
   If your experiments use/require/support multiple input files, never fear!
   You can still use SIERRA. you just have to "flatten" your configuration
   hierarchy into a single file; this is typically done at the :term:`Engine`
   level via a simple expdef plugin hook; see :ref:`plugins/engine`.

   See also :ref:`philosophy`.

#. The post-processing pipeline for experimental data generally conforms to
   SIERRA's :ref:`dataflow model <exp/dataflow>`. If your code isn't conformant,
   never fear! You can still use SIERRA--you will just have to define your own
   plugins for :ref:`data processing <plugins/proc>` and :ref:`product
   generation <plugins/prod>`.

.. _req/expef:

Experiment Definition Format-based Restrictions
-----------------------------------------------

SIERRA uses some special XML tokens during stage 1, and although it is unlikely
that including these tokens would cause problems, because SIERRA looks for them
in *specific* places in the ``--expdef-template``. Restrictions differ according
to the active ``--expdef`` plugin.

.. tabs::

   .. tab:: XML

      .. include:: expdef/xml.rst

   .. tab:: JSON

      .. include:: expdef/json.rst

   .. tab:: YAML

      .. include:: expdef/yaml.rst

.. _req/engine:

Engine-based Restrictions
=========================

If you are using a built-in engine, the corresponding restrictions below
apply.


.. tabs::

   .. tab:: :term:`ARGoS` Engine

      .. include:: engine/argos.rst

   .. tab:: :term:`ROS1`-based Engines

      .. include:: engine/ros1.rst

   .. tab:: :term:`ROS1+Robot` Engine

      .. include:: engine/ros1robot.rst

   .. tab:: :term:`ROS1+Gazebo` Engine

      .. include:: engine/ros1gazebo.rst


.. _req/project:

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

   For HPC execution environments (see :ref:`plugins/execenv/hpc`), this
   requirement is easy to meet. For real robot execution environments (see
   :ref:`plugins/execenv/realrobot`), this can be more difficult to meet.


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

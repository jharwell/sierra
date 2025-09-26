.. _plugins/engine/argos:

============
ARGoS Engine
============

`<https://www.argos-sim.info/index.php>`_. Requires ARGoS >= 3.0.0-beta59.

This engine can be selected via ``--engine=engine.argos``.

This is the default engine on which SIERRA will run experiments, and uses the
:term:`ARGoS` simulator. It cannot be used to run experiments on real robots.

.. _plugins/engine/argos/packages:

OS Packages
===========

.. tabs::

      .. group-tab:: Ubuntu

         Install the following optional packages with ``apt install``:

         - ``xvfb``  - Only needed for ``--engine-vc``.

      .. group-tab:: OSX

         Install the following optional packages with ``brew install``:

         - ``--cask xquartz``   - Only needed for ``--engine-vc``.

Note that you also need to install ARGoS.

.. _plugins/engine/argos/usage:

Usage
=====

Batch Criteria
--------------

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you.  The following batch criteria are defined which can be used with any
:term:`Project`.

.. toctree::
   :maxdepth: 1

   bc/population-size.rst
   bc/population-constant-density.rst
   bc/population-variable-density.rst

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/engine/argos/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra-cli


Environment Variables
=====================

This engine respects :envvar:`SIERRA_ARCH`.

Execution Environments
======================

The # threads per :term:`experimental run <Experimental Run>` is defined with
``--physics-n-engines``, and that option is required for the
``--execenv=hpc.local`` environment during stage 1.

Random Seeding For Reproducibility
==================================

ARGoS provides its own random seed mechanism under ``<experiment>`` which SIERRA
uses to seed each experiment. :term:`Project` code should use this mechanism or
a similar random seed generator manager seeded by the same value so that
experiments can be reproduced exactly. By default SIERRA does not overwrite its
generated random seeds for each experiment once generated; you can override with
``--no-preserve-seeds``.

Visual Capture and Rendering
============================

This engine can render it's simulation environment offscreen into a virtual
buffer using :program:`Xvfb`, and output captured frames as PNG images during
stage 2, which can then be rendered into per-run videos during stage 4 (see
:ref:`plugins/prod/render` for more details).

To use:

- Install :program:`Xvfb` so that it can installed/can be found by the shell
  during stage 2.

- Pass ``--engine-vc`` during stage 2. This will slow ARGoS down a LOT, so if
  you use it, ``--n-runs`` should probably be low, unless you have gobs of
  computing power available. ARGoS will output captured frames to ``frames/`` in
  each experimental run output directory.

- Pass ``--engine-vc`` during stage 4, which causes frames captured during stage
  2 to be stitched together into a unique video file using :program:`ffmpeg`
  (precise command configurable via ``--render-cmd-opts``), and output under
  ``<batch_root>/videos/<exp>``.

.. NOTE:: During stage 1 ``--engine-vc`` causes the ARGoS Qt/OpenGL
          ``<visualization>`` subtree to be added to the ``--expdef-template``
          when generating experimental inputs; it is removed otherwise. If
          ``<visualization>`` already exists, it is removed and re-created.

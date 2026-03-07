.. _plugins/engine/argos:

============
ARGoS Engine
============

`<https://www.argos-sim.info/index.php>`_. Requires ARGoS >= 3.0.0-beta59.

This engine can be selected via ``--engine=engine.argos``.

This is the default engine on which SIERRA will run experiments, and uses the
:term:`ARGoS` simulator. It cannot be used to run experiments on real robots.

Requirements
============

#. All swarms are homogeneous (i.e., only contain 1 type of robot) if the size
   of the swarm changes across experiments (e.g., 1 robot in exp0, 2 in exp1,
   etc.). While SIERRA does not currently support multiple types of robots with
   varying swarm sizes, adding support for doing so would not be difficult. As a
   result, SIERRA assumes that the type of the robots you want to use is already
   set in the template input file (e.g., ``<entity/foot-bot>``) when using
   SIERRA to change the swarm size.

#. The distribution method via ``<distribute>`` in the ``.argos`` file is the
   same for all robots, and therefore only one such tag exists (not checked).

#. The ``<XXX_controller>`` tag representing the configuration for the
   ``--controller`` you want to use does not exist verbatim in the
   ``--expdef-template``. Instead, a placeholder ``__CONTROLLER__`` is used
   so that SIERRA can unambiguously set the "library" attribute of the
   controller; the ``__CONTROLLER__`` tag will replaced with the ARGoS name of
   the controller you selected via ``--controller`` specified in the
   ``controllers.yaml`` configuration file by SIERRA. You should have something
   like this in your template input file:

   .. code-block:: XML

      <argos-configuration>
         ...
         <controllers>
            ...
            <__CONTROLLER__>
               <param_set1>
                  ...
               </param_set1>
               ...
            <__CONTROLLER__/>
            ...
         </controllers>
         ...
      </argos-configuration>

   See also :ref:`tutorials/project/config`.

#. ``--project`` matches the name of the C++ library for the project
   (i.e. ``--project.so``), unless ``library_name`` is present in
   ``sierra.main.run`` YAML config. See :ref:`tutorials/project/config` for
   details. For example if you pass ``--project=project-awesome``, then SIERRA
   will tell ARGoS to search in ``project-awesome.so`` for both loop function
   and controller definitions via XML changes, unless you specify otherwise in
   project configuration. You *cannot* put the loop function/controller
   definitions in different libraries.

#. :envvar:`ARGOS_PLUGIN_PATH` is set up properly prior to invoking SIERRA.

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

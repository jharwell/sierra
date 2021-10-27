.. _ln-usage-rendering:

=========
Rendering
=========

SIERRA's capabilities for generating rendered video from ARGoS/simulation
outputs ways are detailed in this section.

.. NOTE:: Using BOTH the ARgoS and project rendering capabilities simultaneously
   IS possible, but discouraged unless you have multiple terrabytes of disk
   space available. In general when using SIERRA's rendering capabilities,
   ``--exp-range`` is your friend.

ARGoS Rendering
===============

.. _ln-usage-rendering-argos:

SIERRA can direct ARGoS to capture simulations frame by frame as they run during
stage 2, and render the captured frames into nice videos during stage 4. To
enable it, you must pass ``--argos-rendering`` on the cmdline when stages
{1,3-4} are run. ``--argos-rendering`` assumes that:

- ``ffmpeg, Xvfb`` are installed/can be found by the shell. This is checked
  during stage 3 if imagizing is run, and stage 1 when generating simulation
  inputs, respectively.

During stage 1 ``--argos-rendering`` causes the ARGoS Qt/OpenGL
``<visualization>`` subtree to be added to to the ``--template-input-file``
before generating experimental inputs; it is removed otherwise if it exists. If
``<visualization>`` already exists, it is removed and re-created.

During stage 4, ``--argos-rendering`` causes `any` files in the
``main.argos_frames_leaf`` (see :ref:`ln-tutorials-project-main-config`)
directory of each simulation (directory path set on a per ``--project`` basis)
to be stitched together into a unique video file using ffmpeg (precise command
configurable via ``--render-cmd-opts``), and output to
``<batch_root>/videos/<exp>``.

.. _ln-usage-rendering-project:

Project Rendering
=================

Projects can generate ``.csv`` files residing in subdirectories within the
``main.sim_metrics_leaf`` (see :ref:`ln-tutorials-project-main-config`)
directory (directory path set on a per ``--project`` basis) for each ARGoS
simulation, in addition to generating ``.csv`` files residing directly in the
``main.sim_metrics_leaf.`` directory. SIERRA can then render these ``.csv``
files into :class:`~sierra.core.graphs.heatmap.Heatmap` graphs, and stitch these
images together to make videos.

To use, do the following:

#. Pass ``--project-imagizing`` during stage 3. When passed, the ``.csv`` files
   residing each subdirectory under the ``main.sim_metrics_leaf`` directory (no
   recursive nesting is allowed) in each simulation are treated as snapshots of
   2D or 3D data over time, and will be averaged together across simulations and
   then turn into image files suitable for video rendering in stage 4. The
   following restrictions apply:

   - A common stem with a unique numeric ID is required for each ``.csv`` must be present
     for each ``.csv``.

   - The directory name within ``main.sim_metrics_leaf`` must be the same as the
     stem for each ``.csv`` file in that directory. For example, if the
     directory name was ``swarm-distribution`` under ``main.sim_metrics_leaf``
     then all ``.csv`` files within that directory must be named according to
     ``swarm-distribution/swarm-distributionXXXXX.csv``, where XXXXX is any
     length numeric prefix (possibly preceded by an underscore or dash).

   .. IMPORTANT::

      Averaging the image ``.csv`` files and generating the images for each
      experiment does not happen automatically as part of stage 3 because it can
      take a LONG time and is idempotent. You should only pass
      ``--project-imagizing`` the first time you run stage 3 after running stage
      2 (unless you are getting paid by the hour).

#. Pass ``--project-rendering`` during stage 4 after running imagizing via
   ``--project-imagizing`` during stage 3, either on the same invocation or a
   previous one. SIERRA will take the imagized ``.csv`` files previously created
   and generate a set of a videos in ``<batch_root>/videos/<exp>`` for each
   experiment in the batch which was run.

   .. IMPORTANT::

      Rendering the imagized ``.csv`` does not happen automatically every time
      as part of stage 4 because it can take a LONG time and is idempotent. You
      should only pass ``--project-rendering`` the first time you run stage 4
      after having run stage 3 with ``--project-rendering`` (unless you are
      getting paid by the hour).

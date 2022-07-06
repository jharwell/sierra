.. _ln-sierra-usage-vc:

==============
Visual Capture
==============

SIERRA's capabilities for capturing frames during :term:`Experimental Runs
<Experimental Run>` and rendering them input video outputs are detailed in this
section.

.. NOTE:: Using BOTH the platform and project rendering capabilities
   simultaneously IS possible, but discouraged unless you have multiple
   terrabytes of disk space available. In general when using SIERRA's rendering
   capabilities, ``--exp-range`` is your friend.

.. _ln-sierra-usage-vc-platform:

Platform Visual Capture
=======================

SIERRA can direct some platforms to capture frames during
experiments. ``--platform-vc`` assumes that:

- :program:`ffmpeg` is installed/can be found by the shell. Checked during stage
  3 if :term:`imagizing` is run.

This is applicable to the following platforms:

- :term:`ARGoS`, selected via ``--platform=platform.argos``.

.. IMPORTANT:: If the selected platform usually runs headless, then this option
               will probably slow things down a LOT, so if you use it,
               ``--n-runs`` should probably be low, unless you have gobs of
               computing power available.


.. _ln-sierra-usage-vc-platform-argos:

ARGos Visual Capture
--------------------

Visual capture in :term:`ARGoS` is done via frame capturing while running, and
then the captured images stitched together into videos during stage 4.

During stage 1 ``--platform-vc`` causes the ARGoS Qt/OpenGL
``<visualization>`` subtree to be added to the ``--template-input-file`` when
generating experimental inputs; it is removed otherwise. If ``<visualization>``
already exists, it is removed and re-created. During stage 1 SIERRA assumes
that:

- :program:`Xvfb` is installed/can be found by the shell (checked). This is
  needed to get ARGoS to "render" its simulation into an offscreen buffer which
  we can output to a file.

During stage 4, ``--platform-vc`` causes frames captured during stage 2 to be
stitched together into a unique video file using :program:`ffmpeg` (precise
command configurable via ``--render-cmd-opts``), and output to
``<batch_root>/videos/<exp>``.

.. _ln-sierra-usage-rendering-project:

Project Rendering
=================

Projects can generate CSV files residing in subdirectories within the
``main.run_metrics_leaf`` (see :ref:`ln-sierra-tutorials-project-main-config`)
directory (directory path set on a per ``--project`` basis) for each
experimental run, in addition to generating CSV files residing directly in
the ``main.run_metrics_leaf.`` directory. SIERRA can then render these CSV
files into :class:`~sierra.core.graphs.heatmap.Heatmap` graphs, and stitch these
images together to make videos.

To use, do the following:

#. Pass ``--project-imagizing`` during stage 3. When passed, the CSV files
   residing each subdirectory under the ``main.run_metrics_leaf`` directory (no
   recursive nesting is allowed) in each run are treated as snapshots of 2D or
   3D data over time, and will be averaged together across runs and then turn
   into image files suitable for video rendering in stage 4. The following
   restrictions apply:

   - A common stem with a unique numeric ID is required for each CSV must
     be present for each CSV.

   - The directory name within ``main.run_metrics_leaf`` must be the same as the
     stem for each CSV file in that directory. For example, if the
     directory name was ``swarm-distribution`` under ``main.run_metrics_leaf``
     then all CSV files within that directory must be named according to
     ``swarm-distribution/swarm-distributionXXXXX.csv``, where XXXXX is any
     length numeric prefix (possibly preceded by an underscore or dash).

   .. IMPORTANT::

      Averaging the image CSV files and generating the images for each
      experiment does not happen automatically as part of stage 3 because it can
      take a LONG time and is idempotent. You should only pass
      ``--project-imagizing`` the first time you run stage 3 after running stage
      2 (unless you are getting paid by the hour).

#. Pass ``--project-vc`` during stage 4 after running imagizing via
   ``--project-imagizing`` during stage 3, either on the same invocation or a
   previous one. SIERRA will take the imagized CSV files previously created
   and generate a set of a videos in ``<batch_root>/videos/<exp>`` for each
   experiment in the batch which was run.

   .. IMPORTANT::

      Rendering the imagized CSV does not happen automatically every time
      as part of stage 4 because it can take a LONG time and is idempotent. You
      should only pass ``--project-vc`` the first time you run stage 4 after
      having run stage 3 with ``--project-vc`` (unless you are getting paid by
      the hour).

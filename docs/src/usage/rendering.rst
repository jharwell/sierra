.. _usage/rendering:

=========
Rendering
=========

SIERRA's capabilities for rendering video outputs are detailed in this
section. SIERRA can render frames (images) into videos from 3 sources:

- Those captured using ``--platform-vc``, details :ref:`here
  <usage/rendering/platform>`.

- Those imagized from project :term:`Raw Output` files via ``--project-imagizing`` using
  ``--project-rendering`` details :ref:`here
  <usage/rendering/project>`. See also :ref:`usage/imagizing/project`.

- Inter-experiment heatmaps from bivariate batch criteria ``--bc-rendering``,
  details :ref:`here <usage/rendering/bc>`.


.. NOTE:: Using BOTH the platform and project rendering capabilities
   simultaneously IS possible (i.e., passing ``--platform-vc`` and
   ``--project-rendering`` during stage 3), but discouraged unless you have
   multiple terrabytes of disk space available. ``--exp-range`` is your friend.

.. _usage/rendering/platform:

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


.. _usage/rendering/platform/argos:

ARGos Visual Capture
--------------------

Visual capture in :term:`ARGoS` is done via frame capturing while running, and
then the captured images stitched together into videos during stage 4.

During stage 1 ``--platform-vc`` causes the ARGoS Qt/OpenGL
``<visualization>`` subtree to be added to the ``--expdef-template`` when
generating experimental inputs; it is removed otherwise. If ``<visualization>``
already exists, it is removed and re-created. During stage 1 SIERRA assumes
that:

- :program:`Xvfb` is installed/can be found by the shell (checked). This is
  needed to get ARGoS to "render" its simulation into an offscreen buffer which
  we can output to a file.

During stage 2, ARGoS outputs captured frames to ``frames/`` in each output
directory.  During stage 4, ``--platform-vc`` causes frames captured during
stage 2 to be stitched together into a unique video file using :program:`ffmpeg`
(precise command configurable via ``--render-cmd-opts``), and output to
``<batch_root>/videos/<exp>``.

.. _usage/rendering/project:

Project Rendering
=================

If a project has generated conforming :term:`Raw Output Data` files and
:ref:`imagized <usage/imagize/project>` them in stage 3 via
``--project-imagizing``, then they can be rendered into videos in stage 4.

To use, pass ``--project-rendering`` during stage 4 after running imagizing via
``--project-imagizing`` during stage 3, either on the same invocation or a
previous one. SIERRA will take the imagized files previously created and
generate a set of a videos in ``<batch_root>/videos/<exp>/<subdir>`` for each
experiment in the batch which was run, where ``<subdir>`` is the name of a
subdirectory in ``main.run_metrics_leaf`` which contained the raw files to
imagize.

.. IMPORTANT::

   Rendering the imagized CSV does not happen automatically every time as part
   of stage 4 because it can take a LONG time and is idempotent. You should only
   pass ``--project-rendering`` the first time you run stage 4 after having run
   stage 3 with ``--project-imagizing``.


.. _usage/rendering/bc:

Batch Criteria Rendering
========================

For bivariate batch criteria, if inter-experiment heatmaps are generated, they
can be stitched together to make videos of how the two variables of interest
affect some aspect of behavior over time.

To use, do the following:

#. Pass ``--bc-rendering`` during stage 4 when inter-experiment heatmaps are
   generated. SIERRA will take the generated PNG files previously created in
   ``<batch_root>/graphs/collated`` and generate a set of a videos in
   ``<batch_root>/videos/<heatmap name>`` for each heatmap.

   .. IMPORTANT::

      Rendering the heatmaps CSV does not happen automatically every time as
      part of stage 4 because it can take a LONG time and is idempotent. You
      should only pass ``--bc-rendering`` the first time you run stage 4 (unless
      you are getting paid by the hour).

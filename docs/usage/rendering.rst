.. _ln-usage-rendering:

SIERRA Rendering
================

SIERRA's capabilities for generating rendered video from ARGoS/simulation
outputs in various ways are detailed in this section.

ARGoS Rendering
---------------
.. _ln-usage-rendering-argos:

SIERRA can direct ARGoS to capture simulations frame by frame as they run during
stage 2, and render the captured frames into nice videos during stage 4. To
enable it, you must pass ``--argos-rendering`` on the
cmdline. ``--argos-rendering`` assumes that:

- ``ffmpeg, Xvfb`` are installed/can be found by the shell.

During stage 1 ``--argos-rendering`` causes the ARGoS Qt/OpenGL visualization
subtree to be retained in the ``--template-input-file`` before generating
experimental inputs; it is removed otherwise if it exists.

During stage 4, ``--argos-rendering`` causes `any` files in the "frames"
directory of each simulation (directory path set on a per ``--project`` will) to
be stitched together into a unique video file using ffmpeg (precise command
configurable via ``--render-cmd-opts``), and output to
``<simulation_root>/videos``.

.. _ln-usage-rendering-project-imagizing:

Project Imagizing
-----------------

Projects can generate ``.csv`` files residing in subdirectories within the the
``<sim_metrics_leaf>`` directory(directory path set on a per ``--project``
basis) for each ARGoS simulation, in addition to generating ``.csv`` files
residing directly in the ``<sim_metrics_leaf>`` directory. SIERRA can render
this ``.csv`` files into :ref:``~core.graphs.heatmap.Heatmap`` graphs.

To enable, pass ``--project-imagizing`` during stage 3. When passed, the
``.csv`` files residing each subdirectory under the ``<sim_metrics_leaf>``
directory (no recursive nesting is allowed) in each simulation are treated as
snapshots of 2D or 3D data over time, and will be averaged together across
simulations and then turn into image files suitable for video rendering in
stage 4. The following restrictions apply:

- A common stem with a unique numeric ID is required for each ``.csv`` must be present
  for each ``.csv``.

- The directory name within ` <sim_metrics_leaf>`` must be the same as the stem
  for each ``.csv`` file in that directory. For example, if the directory name
  was ``swarm-distribution`` under ``<sim_metrics_leaf>`` then all ``.csv``
  files within that directory must be named according to
  ``swarm-distribution/swarm-distributionXXXXX.csv``, where XXXXX is any length
  numeric prefix (possibly preceded by an underscore or dash).

.. IMPORTANT::

   Averaging the image ``.csv`` files and generating the images for each
   experiment does not happen automatically as part of stage 3 because it can
   take a LONG time and is idempotent.

.. _ln-usage-rendering-project:

Project Rendering
-----------------

After running imagizing via ``--project-imagizing``, either on the same
invocation or a previous one, SIERRA can take the imagized ``.csv`` files
previously created should be used to generate a set of a videos in
``<exp_root>/videos/<metric_dir_name>.mp4``.

.. IMPORTANT::

   This does not happen automatically every time as part of stage 4 because it
   can take a LONG time and is idempotent.

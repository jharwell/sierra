.. _plugins/prod/render:

=========
Rendering
=========

SIERRA's capabilities for rendering video outputs are detailed in this
section. SIERRA can render frames (images) into videos from 3 sources:

- Those captured using ``--engine-vc``.

- Those imagized from project :term:`Raw Output Data` files via ``--proc
  proc.imagize`` using ``--project-rendering``. See :ref:`here
  <plugins/proc/imagize>` for details about the project-based imagizing plugin.

.. NOTE:: Using BOTH the engine and project rendering capabilities
   simultaneously IS possible, but discouraged unless you have multiple
   terrabytes of disk space available. ``--exp-range`` is your friend.

This plugin uses :program:`ffmpeg` to do the actual rendering, and so it must be
findable by the shell used to invoke SIERRA; an error will be thrown otherwise.

.. _plugins/prod/render/packages:

OS Packages
===========

.. tabs::

      .. group-tab:: Ubuntu

         Install the following required packages with ``apt install``:

         - ``ffmpeg``


      .. group-tab:: OSX

         Install the following required packages with ``brew install``:

         - ``ffmpeg``


.. _plugins/prod/render/usage:

Usage
=====

This plugin can be selected by adding ``prod.render`` to the list passed to
``--prod`` during stage 4.

This plugin creates ``<batchroot>/videos`` when active. Videos for each
experiment will accrue in subdirectories under here. E.g.::

  | -- <batchroot>
       |-- videos
           |-- c1-exp0
           |-- c1-exp1
           |-- c1-exp2
           |-- c1-exp3
           ...

Which videos will be rendered is read from the ``imagizing`` section of project
``graphs.yaml`` for ``--project-rendering``. For ``engine-vc``, all matching
image directories within each experiment are unconditionally rendered. If you
only care about some of them, you can use ``--exp-range`` to only render videos
for some experiments.

Cmdline Interface
-----------------

.. argparse::
   :filename: ../sierra/plugins/prod/render/cmdline.py
   :func: sphinx_cmdline_stage4
   :prog: sierra-cli


.. _plugins/prod/render/usage/engine:

Execution Engine Visual Capture
-------------------------------

SIERRA can direct execution engines to capture frames during experiments. The
captured frames must:

- Meet all of the :ref:`requirements <plugins/proc/imagize/req>`.

- Output files in PNG format with a ``.png`` extension.

To use, pass ``--engine-vc`` during stage 4.

.. _plugins/prod/render/project:

Project Rendering
-----------------

If a project has generated images using the :ref:`imagize plugin
<plugins/proc/imagize>` in stage 3 via ``--proc proc.imagize``, then they can be
rendered into videos in stage 4.

To use:

- Pass ``--project-rendering`` during stage 4 after running imagizing via
  ``--proc proc.imagize`` during stage 3, either on the same invocation or a
  previous one. SIERRA will take the imagized files previously created and
  generate a set of a videos in ``<batch_root>/videos/<exp>/<subdir>`` for each
  experiment in the batch which was run, where ``<subdir>`` corresponds to the
  ``src_stem`` of a configured imagizing directory.

.. IMPORTANT::

   Rendering the heatmaps does not happen automatically every time as part
   of stage 4 because it can take a LONG time and is idempotent. You should only
   pass ``--project-rendering`` the first time you run stage 4 after having run
   stage 3 with ``--proc proc.imagize``.


Examples
========

From the :xref:`ARGoS sample project <SIERRA_SAMPLE_PROJECT>`, capturing the
arena overhead:


.. video:: figures/render-argos-overhead.mp4
   :autoplay:
   :loop:
   :nocontrols:
   :width: 50%

Or, multiple cameras + interpolation:

.. video:: figures/render-argos-sw+interp.mp4
   :autoplay:
   :loop:
   :nocontrols:
   :width: 50%

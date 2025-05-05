.. _plugins/proc:

=====================================
Experiment Outputs Processing Plugins
=====================================

Experimental output processing plugins tell SIERRA what to do with the
:term:`Raw Data Output` files it reads from each :term:`Experimental Run` in
stage 3. The job of these plugins is to transform or otherwise prepare
experimental outputs so that :term:`Deliverables <Deliverable>` can be generated
from them in stage 4. See :ref:`dataflow` for more details.

Plugins that come with SIERRA are:

- :ref:`plugins/proc/stat`

- :ref:`plugins/proc/collate`

- :ref:`plugins/proc/imagize`

.. _plugins/proc/stat:

Statistics Generation
=====================

- Computing statistics over/about experimental data for stage 4 for use in graph
  generation in stage 4. See :ref:`usage/cli` documentation for
  ``--dist-stats`` for details.

.. _plugins/proc/collate:

Collate
=======

.. _plugins/proc/imagize:

Imagizing
=========

SIERRA's capabilities for imagizing (translating from :term:`Raw Output Data`
files into images) are detailed in this section. Imagize inputs are treated as
snapshots of 2D or 3D data over time, and after being be turned into image files
in stage 3 they can be rendered into videos in stage 4 (see
:ref:`plugins/deliverable/render`).

SIERRA can imagize files from the following sources:

- On a per :term:`Project` basis via ``--project-imagizing``.

See also :ref:`usage/rendering`.

.. _plugins/proc/imagize/project:

Project Imagizing
-----------------

If projects generate files within the ``main.run_metrics_leaf`` (see
:ref:`tutorials/project/main-config`) directory for each experimental run which
meet the following criteria, then SIERRA can turn them into images and
render them:

- The files reside in a 1st-level subdirectory of ``main.run_metrics_leaf``
  (recursion not supported).

- The files have a common stem with a unique numeric ID.

- The stem of all files in a 1st-level subdir of ``main.run_metrics_leaf`` is
  the same as the 1st-level subdir name. For example, if the directory name was
  ``swarm-distribution`` under ``main.run_metrics_leaf`` then all files within
  that directory must be named according to
  ``swarm-distribution/swarm-distributionXXXXX.<ext>``, where ``XXXXX`` is any
  length numeric prefix (possibly preceded by an underscore or dash), and
  ``<ext>`` is any extension supported by the currently selected :ref:`storage
  plugin <plugins/storage>`.

- The name of the 1st-level subdir of ``main.run_metrics_leaf`` has a
  corresponding entry in ``intra-graphs-hm.yaml``. This is to enable selective
  imagizing of graphs, so that you don't get bogged down if you want to capture
  imagizing data en masse, but only render some of it to videos later. See
  :ref:`tutorials/project/graphs-config` for details.

.. IMPORTANT::

   Generating the images for each experiment does not happen automatically as
   part of stage 3 because it can take a LONG time and is idempotent. You should
   only pass ``--project-imagizing`` the first time you run stage 3 after
   running stage 2.

To use, pass ``--project-imagizing`` during stage 3.

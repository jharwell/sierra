.. _usage/imagizing:

=========
Imagizing
=========

 SIERRA's capabilities for imagizing (translating from :term:`Raw Output Data`
files into images are detailed in this section. Imagize inputs are treated as
snapshots of 2D or 3D data over time, and can be turned into image files
suitable for video rendering in stage 4

SIERRA can imagize files from the following sources:

- On a per :term:`Project` basis via ``--project-imagizing``


See also :ref:`usage/rendering`.

.. _usage/imagizing/project:

Project Imagizing
=================

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

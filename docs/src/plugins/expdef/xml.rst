.. _plugins/expdef/xml:

===
XML
===

This expdef plugin can be selected via ``--expdef=expdef.xml``.

This is the default expdef type which SIERRA will use to read input files. This
plugin does not currently support flattening/nested configuration files.

.. IMPORTANT:: If multiple matches for a given xpath string are found, only the
               first one is modified. This may be changed in a future version of
               the plugin.

Requirements
============

- ``__CONTROLLER__`` - Tag used when as a placeholder for selecting which
  controller present in an input file (if there are multiple) a user wants to
  use for a specific :term:`Experiment`. Can appear in XML attributes. This
  makes auto-population of the controller name based on the
  ``--controller`` argument and the contents of
  ``controllers.yaml`` (see :ref:`tutorials/project/config` for details) in
  template input files possible.

- ``__UUID__`` - XPath substitution optionally used when a :term:`ROS1` engine
  is selected in ``controllers.yaml`` (see :ref:`tutorials/project/config`) when
  adding XML tags to force addition of the tag once for every robot in the
  experiment, with ``__UUID__`` replaced with the configured robot prefix
  concatenated with its numeric ID (0-based). Can appear in XML attributes.

- ``sierra`` - Used when the :term:`ROS1+Gazebo` engine is selected.  Should
  not appear in XML tags or attributes.


XML-based Engine Examples
=========================

Examples of the structure/required content of the XML file passed to SIERRA via
:ref:`--expdef-template<src/reference/cli:sierra---expdef-template>` for each built-in
XML-based :term:`Engine` are below. Use them as a starting point/in tandem with
:xref:`SIERRA_SAMPLE_PROJECT` to create your own conforming input files. Note
that the contents shown is what is passed to SIERRA; i.e., prior to any
processing.

.. tab-set::

   .. tab-item:: ARGoS
      :sync: ARGoS

      .. include:: argos-preproc.rst

   .. tab-item:: ROS1 (Using parameter server)
      :sync: ros-param

      .. include:: ros1-paramserver-preproc.rst

   .. tab-item:: ROS1 (Using ``<params>`` tag)
      :sync: ros-noparam

      .. include:: ros1-paramstag-preproc.rst


SIERRA may insert additional elements and split the processed template input
file into multiple template files, depending on the engine. The results of
this processing are shown below for each supported :term:`Engine`. No
additional modifications beyond those necessary to use the engine with SIERRA
are shown (i.e., no :term:`Batch Criteria` modifications).

Any of the following may be inserted:

- A new element for the configured random seed.

- A new element for the configured experiment length in seconds.

- A new element for the configured # robots.

- A new element for the controller rate (ticks per second).

- A new element for the path to a second file containing all controller
  configuration.

.. tab-set::

   .. tab-item:: ARGoS
      :sync: ARGoS

      .. include:: argos-postproc.rst

   .. tab-item:: ROS (Using parameter server)
      :sync: ros-param

      .. include:: ros1-paramserver-postproc.rst

   .. tab-item:: ROS (Not using parameter server)
      :sync: ros-noparam

      .. include:: ros1-paramstag-postproc.rst

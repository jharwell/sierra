.. _tutorials/project/expdef-template:

====================================
Experiment Definition Template Files
====================================

.. _tutorials/project/expdef-template/semantics:

Understanding Semantics
=======================

Before we begin, it is important to clarify terminology around the different
components in files passed to ``--expdef-template``:

- Attribute - The value part of a <key, value> pair within an
  ``--expdef-template`` which maps to a native primitive such as a bool, int, or
  string. Attributes *cannot* contain other attributes.

- Element - The value part of a <key, value> pair within an
  ``--expdef-template`` which maps to a sub-tree of configuration. Thus,
  elements can contain other elements, as well as *attributes* (depending on
  markup format).

- Tag - The key part of a <key, value> pair within an ``--expdef-template``
  which maps either to an *element* or an *attribute*.

The differences between these components is best illustrated with some examples:

.. include:: examples.rst

Template Input Files Passed to SIERRA
=====================================

Examples of the structure/required content of the XML file passed to SIERRA via
``--expdef-template`` for each supported :term:`Platform` are below. Use them as
a starting point/in tandem with :xref:`SIERRA_SAMPLE_PROJECT` to create your own
conforming input files. Note that the contents shown is what is passed to
SIERRA; i.e., prior to any processing.

.. tabs::

   .. group-tab:: ARGoS

      .. include:: argos-preproc.rst

   .. group-tab:: ROS1 (Using parameter server)

      .. include:: ros1-paramserver-preproc.rst

   .. group-tab:: ROS1 (Using ``<params>`` tag)

      .. include:: ros1-paramstag-preproc.rst


Post-Processed Template Input Files
===================================

SIERRA may insert additional elements and split the processed template input
file into multiple template files, depending on the platform. The results of
this processing are shown below for each supported :term:`Platform`. No
additional modifications beyond those necessary to use the platform with SIERRA
are shown (i.e., no :term:`Batch Criteria` modifications).

Any of the following may be inserted:

- A new element for the configured random seed.

- A new element for the configured experiment length in seconds.

- A new element for the configured # robots.

- A new element for the controller rate (ticks per second).

- A new element for the path to a second file containing all controller
  configuration.

.. tabs::

   .. tab:: ARGoS

      .. include:: argos-postproc.rst

   .. tab:: ROS (Using parameter server)

      .. include:: ros1-paramserver-postproc.rst

   .. tab:: ROS (Not using parameter server)

      .. include:: ros1-paramstag-postproc.rst

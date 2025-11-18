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

See the section on XML in :ref:`req/expdef` for restrictions on the contents of
XML input files.

XML-based Engine Examples
=========================

Examples of the structure/required content of the XML file passed to SIERRA via
``--expdef-template`` for each built-in XML-based :term:`Engine` are
below. Use them as a starting point/in tandem with :xref:`SIERRA_SAMPLE_PROJECT`
to create your own conforming input files. Note that the contents shown is what
is passed to SIERRA; i.e., prior to any processing.

.. tabs::

   .. group-tab:: ARGoS

      .. include:: argos-preproc.rst

   .. group-tab:: ROS1 (Using parameter server)

      .. include:: ros1-paramserver-preproc.rst

   .. group-tab:: ROS1 (Using ``<params>`` tag)

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

.. tabs::

   .. tab:: ARGoS

      .. include:: argos-postproc.rst

   .. tab:: ROS (Using parameter server)

      .. include:: ros1-paramserver-postproc.rst

   .. tab:: ROS (Not using parameter server)

      .. include:: ros1-paramstag-postproc.rst

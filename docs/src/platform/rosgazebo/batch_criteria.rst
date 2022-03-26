.. _ln-platform-rosgazebo-bc:

==============
Batch Criteria
==============

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you. The :term:`ROS+Gazebo` :term:`Platform` defines the following batch
criteria which can be used with any :term:`Project`.

- :ref:`ln-platform-rosgazebo-bc-population-size`

.. _ln-platform-rosgazebo-bc-population-size:

System Population Size
======================

Changing the system size to investigate behavior across scales within a static
arena size (i.e., variable density). Systems are homogeneous.

.. _ln-platform-rosgazebo-bc-population-size-cmdline:

Cmdline Syntax
--------------

``population_size.{increment_type}{N}``

- ``increment_type`` - {Log,Linear}. If ``Log``, then system sizes for each
  experiment are distributed 1...N by powers of 2. If ``Linear``, then sizes for
  each experiment are distributed linearly between 1...N, split evenly into 10
  different sizes.

- ``N`` - The maximum system size.

Examples
--------

- ``population_size.Log1024``: Static sizes 1...1024
- ``population_size.Linear1000``: Static sizes 100...1000

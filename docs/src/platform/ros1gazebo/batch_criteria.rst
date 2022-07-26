.. _ln-sierra-platform-ros1gazebo-bc:

==============
Batch Criteria
==============

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you.  The following batch criteria are defined which can be used with any
:term:`Project`.

- :ref:`ln-sierra-platform-ros1gazebo-bc-population-size`

.. _ln-sierra-platform-ros1gazebo-bc-population-size:

System Population Size
======================

Changing the system size to investigate behavior across scales within a static
arena size (i.e., variable density). Systems are homogeneous.

.. _ln-sierra-platform-ros1gazebo-bc-population-size-cmdline:

Cmdline Syntax
--------------

``population_size.{model}{N}[.C{cardinality}]``

- ``model`` - The population size model to use.

  - ``Log`` - Population sizes for each experiment are distributed 1...N by
    powers of 2.

  - ``Linear`` - Population sizes for each experiment are distributed linearly
    between 1...N, split evenly into 10 different sizes.

- ``N`` - The maximum population size.

- ``cardinality`` - If the model is ``Linear``, then this can be used
  to specify how many experiments to generate; i.e, it defines the `size` of the
  linear increment. Defaults to 10 if omitted.

Examples
--------

- ``population_size.Log1024``: Static population sizes 1...1024
- ``population_size.Linear1000``: Static population sizes 100...1000 (10)
- ``population_size.Linear3.C3``: Static population sizes 1...3 (3)
- ``population_size.Linear10.C2``: Static population sizes 5...10 (2)

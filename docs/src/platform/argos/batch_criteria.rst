.. _ln-sierra-platform-argos-bc:

==============
Batch Criteria
==============

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you.  The following batch criteria are defined which can be used with any
:term:`Project`.

- :ref:`ln-sierra-platform-argos-bc-population-size`
- :ref:`ln-sierra-platform-argos-bc-population-constant-density`
- :ref:`ln-sierra-platform-argos-bc-population-variable-density`

You *should* be able to combine any two of the criteria above, or use them
independently. I have not tried all combinations, so YMMV.

.. _ln-sierra-platform-argos-bc-population-size:

Swarm Population Size
=====================

Changing the swarm size to investigate behavior across scales within a static
arena size (i.e., variable density). This criteria is functionally identical to
:ref:`ln-sierra-platform-argos-bc-population-variable-density` in terms of changes to the template XML
file, but has a different semantic meaning which can make generated deliverables
more immediately understandable, depending on the context of what is being
investigated (e.g., swarm size vs. swarm density on the X axis).

.. _ln-sierra-platform-argos-bc-population-size-cmdline:

Cmdline Syntax
--------------

``population_size.{model}{N}[.C{cardinality}]``

- ``model``

  - ``Log`` - Swarm sizes for each experiment are distributed 1...N by powers
    of 2.

  - ``Linear`` - Swarm sizes for each experiment are distributed linearly
    between 1...N, split evenly into 10 different sizes.

- ``N`` - The maximum swarm size.

- ``cardinality`` - If the model is ``Linear``, then this can be used
  to specify how many experiments to generate; i.e, it defines the `size` of the
  linear increment. Defaults to 10 if omitted.

Examples
--------

- ``population_size.Log1024``: Static swarm sizes 1...1024
- ``population_size.Linear1000``: Static swarm sizes 100...1000 (10)
- ``population_size.Linear3.C3``: Static swarm sizes 1...3 (3)
- ``population_size.Linear10.C2``: Static swarm sizes 5...10 (2)


.. _ln-sierra-platform-argos-bc-population-constant-density:

Swarm Constant Population Density
=================================

Changing the swarm size and arena size together to maintain the same swarm
size/arena size ratio to investigate behavior across scales.

.. NOTE:: This criteria is for `constant` density of robots as swarm sizes
          increase. For `variable` robot density, use
          :ref:`ln-sierra-platform-argos-bc-population-size` or
          :ref:`ln-sierra-platform-argos-bc-population-variable-density`.


.. _ln-sierra-platform-argos-bc-population-constant-density-cmdline:

Cmdline Syntax
--------------

``population_constant_density.{density}.I{Arena Size Increment}.C{cardinality}``

- ``density`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``Arena Size Increment`` - Size in meters that the X and Y dimensions should
    increase by in between experiments. Larger values here will result in larger
    arenas and more robots being simulated at a given density. Must be an
    integer.

- ``cardinality`` How many experiments should be generated?

Examples
--------

- ``population_constant_density.1p0.I16.C4``: Constant density of 1.0. Arena
    dimensions will increase by 16 in both X and Y for each experiment in the
    batch (4 total).

.. _ln-sierra-platform-argos-bc-population-variable-density:


Swarm Variable Population Density
=================================

Changing the swarm size to investigate behavior across scales within a static
arena size. This criteria is functionally identical to
:ref:`ln-sierra-platform-argos-bc-population-size` in terms of changes to the template
XML file, but has a different semantic meaning which can make generated
deliverables more immediately understandable, depending on the context of what
is being investigated (e.g., swarm density vs. swarm size on the X axis).

.. NOTE:: This criteria is for `variable` density of robots as swarm sizes
          increase. For `constant` robot density, use
          :ref:`ln-sierra-platform-argos-bc-population-constant-density`.

.. _ln-sierra-platform-argos-bc-population-variable-density-cmdline:

Cmdline Syntax
--------------

``population_variable_density.{density_min}.{density_max}.C{cardinality}``

- ``density_min`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``density_max`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``cardinality`` How many experiments should be generated? Densities for each
  experiment will be linearly spaced between the min and max densities.

Examples
--------

- ``population_variable_density.1p0.4p0.C4``: Densities of 1.0,2.0,3.0,4.0.

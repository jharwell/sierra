.. _plugins/engine/argos/bc/population-variable-density:

===========================
Population Variable Density
===========================

Changing the population size to investigate behavior across scales within a
static arena size. This criteria is functionally identical to
:ref:`plugins/engine/argos/bc/population-size` in terms of changes to the
template XML file, but has a different semantic meaning which can make generated
deliverables more immediately understandable, depending on the context of what
is being investigated (e.g., population density vs. population size on the X
axis).

.. NOTE:: This criteria is for `variable` density of robots as population sizes
          increase. For `constant` robot density, use
          :ref:`plugins/engine/argos/bc/population-constant-density`.


Cmdline Syntax
==============

``population_variable_density.{density_min}.{density_max}.C{cardinality}``

- ``density_min`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``density_max`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``cardinality`` How many experiments should be generated? Densities for each
  experiment will be linearly spaced between the min and max densities.

Examples
========

- ``population_variable_density.1p0.4p0.C4``: Densities of 1.0,2.0,3.0,4.0.

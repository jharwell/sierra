.. _plugins/engine/argos/bc/population-constant-density:

===========================
Population Constant Density
===========================

Changing the population size and arena size together to maintain the same
population size/arena size ratio to investigate behavior across scales.

.. NOTE:: This criteria is for *constant* density of robots as population sizes
          increase. For *variable* robot density, use
          :ref:`plugins/engine/argos/bc/population-size` or
          :ref:`plugins/engine/argos/bc/population-variable-density`.


Cmdline Syntax
==============

``population_constant_density.{density}.I{Arena Size Increment}.C{cardinality}``

- ``density`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``Arena Size Increment`` - Size in meters that the X and Y dimensions should
  increase by in between experiments. Larger values here will result in larger
  arenas and more robots being simulated at a given density. Must be an integer.

- ``cardinality`` How many experiments should be generated?

Examples
========

- ``population_constant_density.1p0.I16.C4``: Constant density of 1.0. Arena
  dimensions will increase by 16 in both X and Y for each experiment in the
  batch (4 total).

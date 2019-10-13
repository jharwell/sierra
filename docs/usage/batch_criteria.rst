Batch Criteria
==============

How get get Sierra to DO stuff for you. A batch criteria can encompass a single
variable definition (univariate), or be defined by two variables
(bivariate). Each variable is a dimension along which one or more parameters in
the template input file provided to sierra can be varied.

Univariate batch criteria have one dimension, and so the graphs produced by them
are (usually) linegraphs with a numerical representation of the range for the
variable on the X axis, and some other quantity of interest on the Y.

Bivariate batch criteria have two deminsions, and so the graphs produced by the
are (usually) heatmaps with the variable of the criteria on the X axis, the
second on the Y, and the quantity of interest on the Z.

Currently valid batch criteria in Sierra are:

  - `swarm_size`
  - `constant_density`
  - `temporal_variance`
  - `oracle`
  - `ta_policy_set`


Base Classes
----------------------------
.. automodule:: variables.batch_criteria
    :members:
    :inherited-members:
    :show-inheritance:


Swarm Size
----------------------------

.. automodule:: variables.swarm_size
    :members:
    :inherited-members:
    :show-inheritance:

Swarm Constant Density
----------------------------

.. automodule:: variables.constant_density
    :members:
    :inherited-members:
    :show-inheritance:

Temporal Variance
----------------------------

.. automodule:: variables.temporal_variance
    :members:
    :inherited-members:
    :show-inheritance:

Oracle
----------------------------

.. automodule:: variables.oracle
    :members:
    :inherited-members:
    :show-inheritance:

Task Allocation Policy
----------------------------

.. automodule:: variables.ta_policy_set
    :members:
    :inherited-members:
    :show-inheritance:


Sphinx_



.. _Sphinx: https://www.youtube.com/watch?v=dQw4w9WgXcQ

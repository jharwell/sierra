.. _ln-batch-criteria:

Batch Criteria
==============

How get get SIERRA to DO stuff for you. A batch criteria can encompass a single
variable definition (univariate), or be defined by two variables
(bivariate). Each variable is a dimension along which one or more parameters in
the template input file provided to sierra can be varied.

Univariate batch criteria have one dimension, and so the graphs produced by them
are (usually) linegraphs with a numerical representation of the range for the
variable on the X axis, and some other quantity of interest on the Y.

Bivariate batch criteria have two deminsions, and so the graphs produced by the
are (usually) heatmaps with the variable of the criteria on the X axis, the
second on the Y, and the quantity of interest on the Z.

Core Batch Criteria
-------------------

The SIERRA core defines the following batch criteria (additional criteria can be
defined by the selected plugin):

  - ``swarm_size``
  - ``swarm_density``
  - ``block_density``
  - ``flexibility``
  - ``oracle``
  - ``ta_policy_set``
  - ``saa_noise``

You *should* be able to combine any two of the criteria above, or use them
independently. I have not tried all combinations, so YMMV.

Base Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: core.variables.batch_criteria
    :members:
    :inherited-members:
    :show-inheritance:

Swarm Size
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.swarm_size
    :members:

Swarm Density
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.swarm_density
    :members:

Block Density
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.block_density
    :members:

Flexibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.flexibility
    :members:

Oracle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.oracle
    :members:

Task Allocation Policy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.ta_policy_set
    :members:

Sensor and Actuator Noise
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: core.variables.saa_noise
    :members:

FORDYCA Plugin Batch Criteria
-----------------------------

None for the moment.

SILICON Plugin Batch Criteria
-----------------------------

None for the moment.

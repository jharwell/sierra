.. _ln-platform-argos-bc:

==============
Batch Criteria
==============

See :term:`Batch Criteria` for a thorough explanation of batch criteria, but the
short version is that they are the core of SIERRA--how to get it to DO stuff for
you.  The following batch criteria are defined which can be used with any
:term:`Project`.

- :ref:`ln-platform-argos-bc-population-size`
- :ref:`ln-platform-argos-bc-population-constant-density`
- :ref:`ln-platform-argos-bc-population-variable-density`
- :ref:`ln-platform-argos-bc-saa-noise`

You *should* be able to combine any two of the criteria above, or use them
independently. I have not tried all combinations, so YMMV.

.. _ln-platform-argos-bc-population-size:

Swarm Population Size
=====================

Changing the swarm size to investigate behavior across scales within a static
arena size (i.e., variable density). This criteria is functionally identical to
:ref:`ln-platform-argos-bc-population-variable-density` in terms of changes to the template XML
file, but has a different semantic meaning which can make generated deliverables
more immediately understandable, depending on the context of what is being
investigated (e.g., swarm size vs. swarm density on the X axis).

.. _ln-platform-argos-bc-population-size-cmdline:

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


.. _ln-platform-argos-bc-population-constant-density:

Swarm Constant Population Density
=================================

Changing the swarm size and arena size together to maintain the same swarm
size/arena size ratio to investigate behavior across scales.

.. NOTE:: This criteria is for `constant` density of robots as swarm sizes
          increase. For `variable` robot density, use
          :ref:`ln-platform-argos-bc-population-size` or
          :ref:`ln-platform-argos-bc-population-variable-density`.


.. _ln-platform-argos-bc-population-constant-density-cmdline:

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

.. _ln-platform-argos-bc-population-variable-density:


Swarm Variable Population Density
=================================

Changing the swarm size to investigate behavior across scales within a static
arena size. This criteria is functionally identical to
:ref:`ln-platform-argos-bc-population-size` in terms of changes to the template
XML file, but has a different semantic meaning which can make generated
deliverables more immediately understandable, depending on the context of what
is being investigated (e.g., swarm density vs. swarm size on the X axis).

.. NOTE:: This criteria is for `variable` density of robots as swarm sizes
          increase. For `constant` robot density, use
          :ref:`ln-platform-argos-bc-population-constant-density`.

.. _ln-platform-argos-bc-population-variable-density-cmdline:

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

.. _ln-platform-argos-bc-saa-noise:

Sensor and Actuator Noise
=========================

Inject sensor and/or actuator noise into the swarm.

Cmdline Syntax
--------------

``saa_noise.{category}.C{cardinality}[.Z{population}]``

- ``category`` - [sensors,actuators,all]

  - ``sensors`` - Apply noise to robot sensors only. The ``sensors`` dictionary
    must be present and non-empty in the ``main.yaml``.

  - ``actuators`` - Apply noise to robot actuators only. The ``actuators``
    dictionary must be present and non-empty in ``main.yaml``.

  - ``all`` - Apply noise to robot sensors AND actuators. [ ``sensors``,
    ``actuators`` ] dictionaries both optional in ``main.yaml``.

- ``cardinality`` - The # of different noise levels to test with between the min
  and max specified in the config file for each sensor/actuator which defines
  the cardinality of the batch experiment.

- ``population`` - The static swarm size to use (optional).

Examples
--------

- ``saa_noise.sensors.C4.Z16``: 4 levels of noise applied to all sensors in a
  swarm of size 16.

- ``saa_noise.actuators.C3.Z32``: 3 levels of noise applied to all actuators in
  a swarm of size 32.

- ``saa_noise.all.C10``: 10 levels of noise applied to both sensors and
  actuators; swarm size not modified.

The values for the min, max noise levels for each sensor which are used along
with ``cardinality`` to define the set of noise ranges to test are set via the
main YAML configuration file (not an easy way to specify ranges in a single
batch criteria definition string). The relevant section is shown below. If the
min, max level for a sensor/actuator is not specified in the YAML file, no XML
changes will be generated for it.

.. IMPORTANT::

   In order to use this batch criteria, you **MUST** have the version of ARGoS
   from `Swarm Robotics Research <https://github.com/swarm-robotics/argos3.git>`_.
   The version accessible on the ARGoS website does not have a consistent noise
   injection interface, making usage with this criteria impossible.

The following sensors can be affected (dependent on your chosen robot's
capabilities in ARGoS):

- light
- proximity
- ground
- steering
- position

The following actuators can be affected (dependent on your chosen robot's
capabilities in ARGoS):

- steering

.. _ln-platform-argos-bc-saa-noise-yaml-config:

YAML Config
-----------

For all sensors and actuators to which noise should be applied, the noise model
and dependent parameters must be specified (i.e. if a given sensor or sensor is
present in the config, all config items for it are mandatory).

The appropriate ``ticks_range`` attribute is required, as there is no way to
calculate in general what the correct range of X values for generated graphs
should be, because some sensors/actuators may have different
assumptions/requirements about noise application than others. For example, the
differential steering actuator ``noise_factor`` has a default value of 1.0
rather than 0.0, due to its implementation model in ARGoS, so the same range of
noise applied to it and, say, the ground sensor, will have different XML changes
generated, and so you can't just average the ranges for all sensors/actuators to
compute what the ticks should be for a given experiment.

.. code-block:: YAML

   perf:
     ...
     robustness:
       # For ``uniform`` models, the ``uniform_ticks_range`` attributes are
       # required.
       uniform_ticks_range: [0.0, 0.1]

       # For ``gaussian`` models, the ``gaussian_ticks_stddev_range`` and
       # ``gaussian_ticks_mean_range`` attributes are required.
       gaussian_ticks_mean_range: [0.0, 0.1]
       gaussian_ticks_stddev_range: [0.0, 0.0]

       # For ``gaussian`` models, the ``gaussian_labels_show``,
       # ``gaussian_ticks_src`` attributes are required, and control what is
       # shown for the xticks/xlabels: the mean or stddev values.
       gaussian_ticks_src: stddev
       gaussian_labels_show: stddev

       # The sensors to inject noise into. All shown sensors are optional. If
       # omitted, they will not be affected by noise injection.
       sensors:
         light:
           model: uniform

           # For a ``uniform`` model, the ``range`` attribute is required, and
           # defines the -[level, level] distribution that injected noise will
           # be drawn from.
           range: [0.0, 0.4]

         proximity:
           model: gaussian
           stddev_range: [0.0, 0.1]
           mean_range: [0.0, 0.0]
         ground:
           model: gaussian
           stddev_range: [0.0, 0.1]
           mean_range: [0.0, 0.0]
         steering: # applied to [vel_noise, dist_noise]
           model: uniform
           range: [0.0, 0.1]
         position:
           model: uniform
           range: [0.0, 0.1]

         # The actuators to inject noise into. All shown actuators are
         # optional. If omitted, they will not be affected by noise injection.
         actuators:
           steering: # applied to [noise_factor]
             model: uniform
             range: [0.95, 1.05]

Uniform Noise Injection Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``range: [0.0,0.1]`` with ``cardinality=1`` will result in two experiments
  with uniform noise distributions of ``[0.0, 0.0]``, and ``[-0.1, 0.1]``.

Gaussian Noise Injection Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``stddev_range: [0.0,1.0]`` and ``mean_range: [0.0, 0.0]`` with
  ``cardinality=2`` will result in two experiments with Guassian noise
  distributions of ``Gaussian(0,0)``, ``Gaussian(0, 0.5)``, and ``Gaussian(0,
  1.0)``.

Experiment Definitions
----------------------

- exp0 - Ideal conditions, in which noise will be applied to the specified
  sensors and/or actuators at the lower bound of the specified ranges for each.

- exp1-expN - Increasing levels of noise, using the cardinality specified on the
  command line and the distribution type specified in YAML configuration.

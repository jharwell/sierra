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

Bivariate batch criteria have two dimensions, and so the graphs produced by the
are (usually) heatmaps with the first variable in the criteria on the X axis,
the second on the Y, and the quantity of interest on the Z.

The SIERRA core defines the following batch criteria (additional criteria can be
defined by the selected project):

  - :ref:`Swarm Population Size <ln-bc-population-size>`
  - :ref:`Swarm Population Dynamics <ln-bc-population-dynamics>`
  - :ref:`Swarm Population Density <ln-bc-population-density>`
  - :ref:`Block Density <ln-bc-block-density>`
  - :ref:`Flexibility <ln-bc-flexibility>`
  - :ref:`Oracle <ln-bc-oracle>`
  - :ref:`Oracle <ln-bc-ta-policy-set>`
  - :ref:`SAA Noise <ln-bc-saa-noise>`

You *should* be able to combine any two of the criteria above, or use them
independently. I have not tried all combinations, so YMMV.

.. _ln-bc-population-size:

Swarm Population Size
---------------------

.. _ln-bc-population-size-cmdline:

Cmdline Syntax
^^^^^^^^^^^^^^
``population_size.{increment_type}{N}``

- ``increment_type`` - {Log,Linear}. If ``Log``, then swarm sizes for each
  experiment are distributed 1...N by powers of 2. If ``Linear`` then swarm
  sizes for each experiment are distributed linearly between 1...N, split evenly
  into 10 different sizes.

- ``N`` - The maximum swarm size.

Examples:
    - ``static.Log1024``: Static swarm sizes 1...1024
    - ``static.Linear1000``: Static swarm sizes 100...1000

.. _ln-bc-population-dynamics:

Swarm Population Dynamics
-------------------------

Cmdline Syntax
^^^^^^^^^^^^^^

``population_dynamics.C{cardinality}.F{Factor}[.{dynamics_type}{prob}[...]]``

- ``cardinality`` - The # of different values of each of the specified dynamics
  types to to test with (starting with the one on the cmdline). This defines the
  cardinality of the batched experiment.

- ``Factor`` - The factor by which the starting value of all dynamics types
  specified on the cmdline are increased for each each experiment (i.e., value
  in last experiment in batch will be ``<start value> + cardinality``; a linear
  increase).

- ``dynamics_type`` - [B,D,M,R]

  - ``B`` - Adds birth dynamics to the population. Has no effect by itself, as
    it specifies a pure birth process with :math:`\lambda=\infty`,
    :math:`\mu_{b}`=``prob`` (a queue with an infinite # of robots in it which
    robots periodically leave from), resulting in dynamic swarm sizes which will
    increase from N...N over time. Can be specified with along with ``D|M|R``,
    in which case swarm sizes will increase according to the birth rate up until
    N, given N robots at the start of simulation.

  - ``D`` - Adds death dynamics to the population. By itself, it specifies a
    pure death process with :math:`\lambda_{d}=prob`, and :math:`\mu_{d}=\infty`
    (a queue which robots enter but never leave), resulting in dynamic swarm
    sizes which will decrease from N...1 over time. Can be specified along with
    ``B|M|R``.

  - ``M|R`` - Adds malfunction/repair dynamics to the population. If ``M``
    dynamics specified, ``R`` dynamics must also be specified, and vice
    versa. Together they specify the dynamics of the swarm as robots temporarily
    fail, and removed from simulation, and then later are re-introduced after
    they have been repaired (a queue with :math:`\lambda_{m}` arrival rate and
    :math:`\mu_{r}` repair rate). Can be specified along with ``B|D``.


.. IMPORTANT:: The specified :math:`\lambda` or :math:`\mu` are the rate
   parameters of the exponential distribution used to distribute the event times
   of the Poisson process governing swarm sizes, *NOT* Poisson process
   parameter, which is their mean; e.g., :math:`\lambda=\frac{1}{\lambda_{d}}`
   for death dynamics.

Examples:
    - ``C10.F2p0.B0p001``: 10 levels of population variability applied using a
      pure birth process with a 0.001 parameter, which will be linearly varied
      in [0.001,0.001*2.0*10]. For all experiments, the initial swarm is not
      controlled directly; the value in template input file will be used if
      swarm size is not set by another variable.

    - ``C4.F3p0.D0p001``: 4 levels of population variability applied using a
      pure death process with a 0.001 parameter, which will be linearly varied
      in [0.001,0.001*3.0*4]. For all experiments, the initial swarm size is not
      controlled directly; the value in template input file will be used if
      swarm size is not set by another variable.

    - ``C8.F4p0.B0p001.D0p005``: 8 levels of population variability applied
      using a birth-death process with a 0.001 parameter for birth and a 0.005
      parameter for death, which will be linearly varied in [0.001,0.001*4.0*8]
      and [0.005, 0.005*4.0*8] respectively. For all experiments, the initial
      swarm is not controlled directly; the value in the template input file
      will be used if swarm size is is not set by another variable.

    - ``C2.F1p5.M0p001.R0p005``: 2 levels of population variability applied
      using a malfunction-repair process with a 0.001 parameter for malfunction
      and a 0.005 parameter for repair which will be linearly varied in [0.001,
      0.001*1.5*2] and [0.005, 0.005*1.5*2] respectively. For all experiments,
      the initial swarm size is not controlled directly; the value in the
      template input file will be used if swarm size is not set by another
      variable.


.. _ln-bc-population-density:

Swarm Population Density
------------------------

.. _ln-bc-population-density-cmdline:

Cmdline Syntax
^^^^^^^^^^^^^^
``population_density.CD{density}.I{Arena Size Increment}``

- ``density`` - <integer>p<integer> (i.e. 5p0 for 5.0)

- ``Arena Size Increment`` - Size in meters that the X and Y dimensions should
  increase by in between experiments. Larger values here will result in larger
  arenas and more robots being simulated at a given density. Must be an integer.

Examples:
    - ``CD1p0.I16``: Constant density of 1.0. Arena dimensions will increase by
      16 in both X and Y for each experiment in the batch.

.. NOTE:: This criteria is for `constant` density of robots as swarm sizes
          increase. For `variable` robot density, use
          :ref:`ln-bc-population-size`.


.. _ln-bc-block-density:

Block Density
-------------

Cmdline Syntax
^^^^^^^^^^^^^^

``block_density.CD{density}.I{Arena Size Increment}``

- ``density`` - <integer>p<integer> (i.e. 5p0 for 5.0)

  - ``Arena Size Increment`` - Size in meters that the X and Y dimensions should
    increase by in between experiments. Larger values here will result in larger
    arenas and more blocks. Must be an integer.

Examples:
    - ``CD1p0.I16``: Constant density of 1.0. Arena dimensions will increase by
      16 in both X and Y for each experiment in the batch.

.. _ln-bc-flexibility:

Flexibility
-----------

.. WARNING::

   Some of the flexibility config via applied temporal variance is very FORDYCA
   specific; hopefully this will change in the future, or be pushed down to a
   project-specific extension of a base flexibility class.

.. _ln-bc-flexibility-cmdline:

Cmdline Syntax
^^^^^^^^^^^^^^

``flexibility.{variance_type}{waveform_type}[step_time][.Z{population}]``

- ``variance_type`` - [BC,BM].

  - ``BC`` - Apply motion throttling to robot speed when it is carrying a
    block according to the specified waveform.

  - ``BM`` - Apply the specified waveform when calculating robot block
    manipulation penalties (pickup, drop, etc.).

- ``waveform_type`` - {Sine,Square,Sawtooth,Step{U,D},Constant}

- ``step_time`` - Timestep the step function should switch (optional)

- ``population`` - The static swarm size to use (optional)

Examples:
- ``BCSine.Z16`` - Block carry sinusoidal variance in a swarm of size 16.
- ``BCStep50000.Z32`` - Block carry step variance at 50000 timesteps in a swarm of size 32.
- ``BCStep50000`` - Block carry step variance at 50000 timesteps; swarm size not modified.

The frequency, amplitude, offset, and phase of the waveforms is set via the
``main.yaml`` configuration file for a project (not an easy way to specify
ranges in a single batch criteria definition string). The relevant section is
shown below.


.. _ln-bc-flexibility-yaml-config:

YAML Config
^^^^^^^^^^^
.. code-block:: YAML

   perf:
     ...
     flexibility:
       # The range of Hz to use for generated waveforms. Applies to Sine, Sawtooth, Square
       # waves. There is no limit for the length of the list.
       hz:
         - frequency1
         - frequency2
         - frequency3
         - ...
       # The range of block manipulation penalties to use if that is the type of applied temporal
       # variance (BM). Specified in timesteps. There is no limit for the length of the list.
       BM_amp:
         - penalty1
         - penalty2
         - penalty3
         - ...
      # The range of block carry penalties to use if that is the type of applied temporal variance
      # (BC). Specified as percent slowdown: [0.0, 1.0]. There is no limit for the length of the
      # list.
      BC_amp:
         - percent1
         - percent2
         - percent3
         - ...

Experiment Definitions
^^^^^^^^^^^^^^^^^^^^^^

- exp0 - Ideal conditions, which is a ``Constant`` waveform with amplitude
  ``BC_amp[0]``, or ``BM_amp[0]``, depending.

- exp1-expN

  - Cardinality of ``|hz|`` * ``|BM_amp|`` if the variance type is ``BM`` and
    the waveform type is Sine, Square, or Sawtooth.

  - Cardinality of ``|hz|`` * ``|BC_amp|`` if the variance type is ``BC`` and
    the waveform type is Sine, Square, or Sawtooth.

  - Cardinality of ``|BM_amp|`` if the variance type is ``BM`` and the waveform
    type is StepU, StepD.

  - Cardinality of ``|BC_amp|`` if the variance type is ``BC`` and the waveform
    type is StepU, StepD.

.. _ln-bc-oracle:

Oracle
------

.. _ln-bc-oracle-cmdline:

Cmdline Syntax
^^^^^^^^^^^^^^
``oracle.{oracle_name}[.Z{population}]``

- ``oracle_name`` - {entities, tasks}

  - ``entities`` - Inject perfect information about locations about entities in
    the arena, such as blocks and caches.
  - ``tasks`` - Inject perfect information about task execution and interface
    times.

- ``population`` - Static size of the swarm to use (optional).

Examples:

- ``entities.Z16`` - All permutations of oracular information about entities in
  the arena, run with swarms of size 16.

- ``tasks.Z8`` - All permutations of oracular information about tasks in the
  arena, run with swarms of size 8.

- ``entities`` - All permuntations of oracular information of entities in the
  arena (swarm size is not modified).

.. _ln-bc-ta-policy-set:

Task Allocation Policy
----------------------

Cmdline Syntax
^^^^^^^^^^^^^^
``ta_policy_set.All[.Z{population}]``

``population`` - The swarm size to use (optional)

Examples:

- ``All.Z16``: All possible task allocation policies with swarms of size 16.
- ``All``: All possible task allocation policies; swarm size not modified.


.. _ln-bc-saa-noise:

Sensor and Actuator Noise
-------------------------

.. WARNING::

   Some of the flexibility config via applied temporal variance is very FORDYCA
   specific; hopefully this will change in the future, or be pushed down to a
   project-specific extension of a base flexibility class.

Cmdline Syntax
^^^^^^^^^^^^^^
``saa_noise.{category}.C{cardinality}[.Z{population}]``

- ``category`` - [sensors,actuators,all]
  - ``sensors`` - Apply noise to robot sensors only.
  - ``actuators`` - Apply noise to robot actuators only.
  - ``all`` - Apply noise to robot sensors AND actuators.

- ``cardinality`` - The # of different noise levels to test with between the min
  and max specified in the config file for each sensor/actuator which defines
  the cardinality of the batched experiment.

- ``population`` - The static swarm size to use (optional).

Examples:

- ``sensors.C4.Z16``: 4 levels of noise applied to all sensors in a swarm of size 16.
- ``actuators.C3.Z32``: 3 levels of noise applied to all actuators in a swarm of size 32.
- ``all.C10``: 10 levels of noise applied to both sensors and actuators; swarm size not
  modified.

The values for the min, max noise levels for each sensor which are used along
with ``cardinality`` to define the set of noise ranges to test are set via the
main YAML configuration file (not an easy way to specify ranges in a single
batch criteria definition string). The relevant section is shown below. If the
min, max level for a sensor/actuator is not specified in the YAML file, no XML
changes will be generated for it.

.. _ln-bc-saa-noise-yaml-config:

YAML Config
^^^^^^^^^^^

For all sensors and actuators to which noise should be applied, the noise model
and dependent parameters must be specified (i.e. if a given sensor or sensor is
present in the config, all config items for it are mandatory).

For a ``uniform`` model, the ``range`` attribute is required, and defines the
-[level, level] distribution.  For example, setting `` range: [0.0,1.0]`` with
``cardinality=2`` will result in two experiments with uniformly distributed
noise ranges of ``[0.0, 0.5]``, and ``[0.0, 1.0]``.

For a ``gaussian`` model, the ``stddev_range`` and ``mean_range`` attributes are
required.  For example, setting ``stddev_range: [0.0,1.0]`` and ``mean_range:
[0.0, 0.0]`` with ``cardinality=2`` will result in two experiments with Guassian
distributed ranges ``Gaussian(0, 0.5)``, and ``Gaussian(0, 1.0)``.

.. code-block:: YAML

   perf:
     ...
     robustness:
       sensors:
         light:
           model: uniform
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

         actuators:
           steering:
             model: uniform
             range: [0.0, 0.1]

Experiment Definitions
^^^^^^^^^^^^^^^^^^^^^^

- exp0 - Ideal conditions, in which noise will be applied to the specified
  sensors and/or actuators at the lower bound of the specified ranges for each.

- exp1-expN - Increasing levels of noise, using the cardinality specified on the
  command line.

FORDYCA Plugin Batch Criteria
-----------------------------

None for the moment.

SILICON Plugin Batch Criteria
-----------------------------

None for the moment.

.. _ln-usage-examples:

===============
SIERRA Examples
===============

These examples all assume that you have successfully set up SIERRA with a
:term:`Project` of your choice.

Basic Example
=============

This examples assumes a project named `fordyca` which contains a controller
defined in the `controllers.yaml` as `d0.CRW`, with a runtime environment of
the local machine.

::

   sierra-cli \
   --sierra-root=$HOME/exp\
   --template-input-file=templates/ideal.argos \
   --n-sims=3\
   --project=fordyca\
   --hpc-env=hpc.local\
   --physics-n-engines=1\
   --time-setup=time_setup.T10000\
   --controller=d0.CRW\
   --scenario=SS.12x6x1\
   --batch-criteria population_size.Log64\
   --n-blocks=20\
   --models-disable

This will run a batch of 7 experiments using a correlated random walk robot
controller (CRW), across which the swarm size will be varied from 1..64, by
powers of 2. Within each experiment, 3 copies of each simulation will be run
(each with different random seeds), for a total of 21 ARGoS simulations. On a
reasonable machine it should take about 10 minutes or so to run. After it
finishes, you can go to ``$HOME/exp`` and find all the simulation outputs,
including camera ready graphs! For an explanation of SIERRA's runtime directory
tree, see :ref:`ln-usage-runtime-exp-tree`.

Rendering Example
=================

This example shows how to use ARGoS image capturing ability to create nice
videos of simulations.

::

   sierra-cli \
   --sierra-root=$HOME/exp\
   --template-input-file=templates/ideal.argos \
   --project=fordyca\
   --n-sims=3\
   --argos-rendering\
   --exp-graphs=none\
   --physics-n-engines=1\
   --batch-criteria population_size.Log8

The runs 3 simulations in parallel with 1 physics engine each, and runs ARGoS
under :program:`Xvfb` to get it to render headless images. During stage 4, these
images are stitched together using :program:`ffmpeg` to create videos (see
:ref:`ln-usage-runtime-exp-tree` for where the videos will appear). No graphs
are generated during stage 4 in this example.

You may also be interested in the ``--camera-config`` option, which allows you
to specify different static/dynamic camera arrangements (e.g., do a nice
circular pan around the arena during simulation).

.. NOTE:: Because LOTS of images can be captured by ARGoS to create videos,
          depending on simulation length, you usually want to have a very small
          ``--n-sims`` to avoid filling up the filesystem.

Stage 5 Example
===============


This example assumes that stages 1-4 have been run successfully with a project
named ``fordyca`` and that a univariate batch criteria has been used (such as
:ref:`ln-bc-population-size`).

::

   sierra-cli \
   --project=fordyca\
   --pipeline 5\
   --scenario-comparison\
   --dist-stats=conf95\
   --bc-univar\
   --controller=d0.CRW\
   --sierra-root=$HOME/exp"


This will compare all scenarios that all controllers with ``$HOME/exp`` which
have been run on the same set of scenarios according to the configuration
defined in ``stage5.yaml``. It will plot the 95% confidence intervals on all
generated graphs for the univariate batch criteria.

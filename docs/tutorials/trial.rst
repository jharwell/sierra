.. _ln-trial:

Trying Out SIERRA
=================

If you just want to try SIERRA out with a pre-existing project without first
defining your own, the steps to do so are:

#. Build the code for the :xref:`FORDYCA` project, following the steps
   `here<https://swarm-robotics-fordyca.readthedocs.io/en/latest/setup/build.html>`_.

   .. IMPORTANT:: Make sure you to build an optimized version of the code by
                  passing ``--opt`` to the bootstrap script. For `most` use
                  cases, that is the only additional option you will need.

#. Setup the :xref:`FORDYCA` runtime environment, following the steps `here
   <https://swarm-robotics-fordyca.readthedocs.io/en/latest/setup/local-runtime.html>`_,
   and make sure (1) ``argos3`` is found by your shell, (2) you can launch the
   FORDYCA demo ARGoS simulation.

#. Clone the SIERRA repo, and checkout the ``devel`` branch::

     mkdir $HOME/research
     git clone https://github.com/swarm-robotics/fordyca.git $HOME/research/sierra
     cd $HOME/research/sierra
     git checkout devel

#. From the SIERRA repo root, install python dependencies with ``pip3``::

     pip3 install --upgrade pip
     pip3 install -r requirements/common.txt

#. Install OS packages:

   - GNU parallel (``sudo apt-get install parallel`` on ubuntu)

#. From the SIERRA repo root, clone the SIERRA project plugin for the FORDYCA
   project and checkout the ``devel`` branch::

     mkdir projects
     git clone https://github.com/swarm-robotics/sierra-plugin-fordyca.git projects/fordyca
     cd projects/fordyca
     git checkout devel

#. From the SIERRA repo root, run SIERRA::

     python3 sierra.py \
        --sierra-root=$HOME/exp\
        --template-input-file=templates/ideal.argos \
        --n-sims=3\
        --project=fordyca\
        --hpc-env=local\
        --physics-n-engines=1\
        --time-setup=time_setup.T10000\
        --controller=d0.CRW\
        --scenario=SS.12x6\
        --batch-criteria population_size.Log64\
        --n-blocks=20\
        --exp-overwrite\
        --models-disable

   This will run a batch of 7 experiments using a correlated random walk robot
   controller (CRW), across which the swarm size will be varied from 1..64, by
   powers of 2. Within each experiment, 3 copies of each simulation will be run
   (each will different random seeds), for a total of 21 ARGoS simulations. On a
   reasonable machine it should take about 10 minutes or so to run. After it
   finishes, you can go to ``$HOME/exp`` and find all the simulation outputs,
   including camera ready graphs! For an explanation of SIERRA's runtime
   directory tree, see :ref:`ln-runtime-exp-tree`.

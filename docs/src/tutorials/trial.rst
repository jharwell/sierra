.. _ln-tutorials-trial:

=================
Trying Out SIERRA
=================

If you just want to try SIERRA out with a pre-existing project without first
defining your own, the steps to do so are:

#. Build the code for the :xref:`FORDYCA` project, following the `build steps
   here <https://swarm-robotics-fordyca.readthedocs.io/en/latest/setup/build.html>`_.

   .. IMPORTANT:: Make sure you to build an optimized version of the code by
                  passing ``--opt`` to the bootstrap script. For `most` use
                  cases, that is the only additional option you will need.

#. Setup the :xref:`FORDYCA` runtime environment, following the `setup steps here
   <https://swarm-robotics-fordyca.readthedocs.io/setup/local-runtime.html>`_,
   and make sure that:

   - ``argos3`` is found by your shell

   - You can launch the FORDYCA demo ARGoS simulation.

   `If you can't do these then you won't be able to do anything useful with
   SIERRA!`.

#. Clone the SIERRA repo, and checkout the ``devel`` branch::

     mkdir $HOME/research
     git clone https://github.com/swarm-robotics/fordyca.git $HOME/research/sierra
     cd $HOME/research/sierra
     git checkout devel

#. From the SIERRA repo root, install SIERRA locally::

     cd docs && make man && cd ..
     python3 -m build
     pip3 install .

#. Install OS packages (ubuntu package names shown):

   - ``parallel``
   - ``cm-super``
   - ``texlive-fonts-recommended``
   - ``texlive-latex-extra``

#. Clone the TITERRA project plugin and checkout the ``devel`` branch::

     cd $HOME/research
     git clone https://github.com/swarm-robotics/titerra.git
     git checkout devel

#. Set :envvar:`SIERRA_PROJECT_PATH`::

     export SIERRA_PROJECT_PATH=$HOME/research/titerra

#. Set :envvar:`ARGOS_PLUGIN_PATH`::

     export ARGOS_PLUGIN_PATH=$HOME/research/fordyca/build/lib

#. From the TITERRA repo root, run SIERRA (taken from
   :ref:`ln-usage-examples`)::

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
        --exp-overwrite\
        --models-disable

   This will run a batch of 7 experiments using a correlated random walk robot
   controller (CRW), across which the swarm size will be varied from 1..64, by
   powers of 2. Within each experiment, 3 copies of each simulation will be run
   (each with different random seeds), for a total of 21 ARGoS simulations. On a
   reasonable machine it should take about 10 minutes or so to run. After it
   finishes, you can go to ``$HOME/exp`` and find all the simulation outputs,
   including camera ready graphs! For an explanation of SIERRA's runtime
   directory tree, see :ref:`ln-usage-runtime-exp-tree`.

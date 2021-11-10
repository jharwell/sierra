.. _ln-trial:

=================
Trying Out SIERRA
=================

If you just want to try SIERRA out with a pre-existing :term:`Project` without
first defining your own, the steps to do so below. I assume that all
repositories are cloned into ``$HOME/research``; adjust the paths accordingly if
you clone things somewhere else.

#. Install OS packages. The .deb package for ubuntu are shown; if you are on a
   different Linux distribution or on OSX you will have to install the
   equivalent packages.

   - ``parallel``
   - ``cm-super``
   - ``texlive-fonts-recommended``
   - ``texlive-latex-extra``
   - ``dvipng``
   
   .. IMPORTANT:: SIERRA will not work if these packages (or their equivalent on
                  non-ubuntu systems) are installed!

#. Install :term:`ARGoS` via your chosen method. Check that ``argos3`` is found
   by your shell.

   .. IMPORTANT:: If ``argos3`` is not found by your shell then
                  you won't be able to do anything useful with SIERRA!

#. Download and build the super-simple SIERRA sample ARGoS project, which is
   based on the foraging example from the ARGoS website::

     git clone https://github.com/swarm-robotics/sierra-sample-project.git
     cd sierra-sample-project
     mkdir build && cmake -DARGOS_INSTALL_DIR=<path> ..
     make

  ``ARGOS_INSTALL_DIR`` should point to the directory you have installed the
  version of ARGoS you want to use for the trial (installed, not
  compiled!). This is used instead of the ``FindARGoS()`` cmake functionality to
  support having multiple versions of ARGoS installed in multiple directories.


#. From the SIERRA repo root, install SIERRA locally::

     git clone https://github.com/swarm-robotics/sierra.git
     cd sierra
     git checkout devel
     cd docs && make man && cd ..
     python3 -m build
     pip3 install .


#. Set :envvar:`SIERRA_PROJECT_PATH`::

     export SIERRA_PROJECT_PATH=$HOME/research/sierra-sample-project/project

#. Set :envvar:`ARGOS_PLUGIN_PATH`::

     export ARGOS_PLUGIN_PATH=$HOME/research/sierra-sample-project/build

#. Run SIERRA (invocation inspired by :ref:`ln-usage-examples`). You can do this
   from any directory::

     sierra-cli \
        --sierra-root=$HOME/research/exp\
        --template-input-file=exp/template.argos \
        --n-sims=4\
        --project=sample_project\
        --physics-n-engines=1\
        --controller=foraging.footbot_foraging\
        --scenario=LowBlockCount.10x10x1\
        --batch-criteria population_size.Log8\
        --with-robot-leds\
        --with-robot-rab\
        --exp-overwrite\

   This will run a batch of 4 experiments using the ``sample_project.so`` C++
   library. The swarm size will be varied from 1..8, by powers of 2. Within each
   experiment, 4 copies of each simulation will be run (each with different
   random seeds), for a total of 16 ARGoS simulations.  On a reasonable machine
   it should take about 1 minute or so to run. After it finishes, you can go to
   ``$HOME/research/exp`` and find all the simulation outputs, including camera
   ready graphs! For an explanation of SIERRA's runtime directory tree, see
   :ref:`ln-usage-runtime-exp-tree`. You can also run the same experiment again,
   and it will overwrite the previous one because you passe ``--exp-overwrite``.

   .. NOTE:: The ``--with-robot-rab`` and ``--with-robot-leds`` arguments are
             required because robot controllers in the sample project use the
             RAB and LED sensor/actuators, and SIERRA strips those tags out of
             the robots ``<sensors>`` and ``<actuators>`` and ``<media>`` parent
             tags by default.

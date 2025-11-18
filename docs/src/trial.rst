.. _trial:

=================
Trying Out SIERRA
=================

If you just want to try SIERRA out with a pre-existing :term:`Project` without
first defining your own, the steps to do so below. I assume that all
repositories are cloned into ``$HOME/research``; adjust the paths accordingly if
you clone things somewhere else.

#. Install OS packages (if you don't see your OS below you will have to find and
   install the equivalent packages). Note: this installs ALL OS packages needed
   by ALL plugins which come with SIERRA for the purposes of fast setup.

   .. tabs::

           .. group-tab:: Ubuntu

              Install the following required packages with ``apt install``:

              - ``parallel``
              - ``cm-super``
              - ``texlive-fonts-recommended``
              - ``texlive-latex-extra``
              - ``dvipng``
              - ``psmisc``
              - ``pssh``
              - ``ffmpeg``
              - ``xvfb``
              - ``iputils-ping``

           .. group-tab:: OSX

              Install the following required packages with ``brew install``:

              - ``parallel``
              - ``--cask mactex``
              - ``pssh``
              - ``--cask xquartz``
              - ``ffmpeg``


     If you are on a different Linux distribution you will have to find and
     install the equivalent packages.

     .. IMPORTANT:: SIERRA will not work correctly in all cases if the required
                    packages (or their equivalent) are not installed! It may
                    start, it might even not crash immediately depending on what
                    you are using it to do. If you are missing an optional
                    package for a feature you try to use, you will get an
                    error.

#. Install SIERRA::

     pip3 install sierra-research

#. Setup your chosen :term:`Engine`:

   .. tabs::

      .. group-tab:: ARGoS

         Install :term:`ARGoS` via your chosen method (from source or via
         .deb). Check that ``argos3`` is found by your shell.

         .. IMPORTANT:: If ``argos3`` is not found by your shell then
                        you won't be able to do anything useful with SIERRA!

      .. group-tab:: ROS1+Gazebo

         #. Install ROS distribution by following one of (or an equivalent guide
            for OSX or an alternative linux distribution):

            - `<http://wiki.ros.org/noetic/Installation/Ubuntu>`_

            - `<http://wiki.ros.org/noetic/Installation/Ubuntu>`_

            SIERRA only supports kinetic,noetic.

         #. Install additional ROS packages for the turtlebot:

            - ``ros-<distro>-turtlebot3-description``
            - ``ros-<distro>-turtlebot3-msgs``
            - ``ros-<distro>-turtlebot3-gazebo``
            - ``ros-<distro>-turtlebot3-bringup``

            Where ``<distro>`` is replaced by your ROS distro.

         #.  Install ROS bridge :xref:`SIERRA_ROSBRIDGE`::

               source /opt/ros/<distro>/setup.bash

               pip3 install pysip \
                            numpy \
                            matplotlib \
                            pyyaml \
                            psutil \
                            defusedxml \
                            pyparsing \
                            pydev \
                            pyopengl \
                            opencv-python \
                            catkin_tools \
                            rospkg \
                            empy

               git clone https://github.com/jharwell/sierra_rosbridge.git
               cd sierra_rosbridge
               git checkout devel
               catkin init
               catkin config --extend /opt/ros/${{ inputs.rosdistro }}
               catkin config --install -DCMAKE_INSTALL_PREFIX=$HOME/.local
               catkin build

             Where ``<distro>`` is replaced by your ROS distro.  Finally, set
             catkin to install at a common location (e.g.,
             ``$HOME/.local/ros/noetic``) and build the package::

               catkin config --install -DCMAKE_INSTALL_PREFIX=$HOME/.local/ros/noetic
               catkin build


#. Download and build the super-simple SIERRA sample project for your chosen
   :term:`Engine`:

   .. tabs::

      .. group-tab:: ARGoS

         Based on the `foraging example
         <https://www.argos-sim.info/examples.php>`_ from the ARGoS website::

           git clone https://github.com/jharwell/sierra-sample-project.git
           cd sierra-sample-project/argos
           mkdir -p build && cd build
           cmake -DARGOS_INSTALL_DIR=<path> ..
           make

         ``ARGOS_INSTALL_DIR`` should point to the directory you have installed
         the version of ARGoS you want to use for the trial (installed, not
         compiled!). This is used instead of the ``FindARGoS()`` cmake
         functionality to support having multiple versions of ARGoS installed in
         multiple directories.

      .. group-tab:: ROS1+Gazebo

         Based on one of the turtlebot3 `intro tutorials
         <https://github.com/ROBOTIS-GIT/turtlebot3_simulations>`_::

           git clone https://github.com/jharwell/sierra-sample-project.git
           cd sierra-sample-project/ros1gazebo
           catkin init
           catkin config --extend=$HOME/.local/ros/noetic
           catkin build

         Where ``$HOME/.local/ros/noetic`` is where I installed the SIERRA
         ROSBridge into.


      .. group-tab:: JSONSim

         Nothing to do!

      .. group-tab:: YAMLSim

         Nothing to do!

#. Setup runtime environment:

   .. tabs::

      .. group-tab:: ARGoS

         #. Set :envvar:`SIERRA_PLUGIN_PATH`::

              export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-project

         #. Set :envvar:`ARGOS_PLUGIN_PATH`::

              export ARGOS_PLUGIN_PATH=$HOME/research/sierra-sample-project/argos/build:<ARGOS_INSTALL_DIR>/lib/argos3

            Where ``<ARGOS_INSTALL_DIR>`` is the prefix that you installed ARGoS
            to.

      .. group-tab:: ROS1+Gazebo

         #. Set :envvar:`SIERRA_PLUGIN_PATH`::

              export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-projec/

         #. Source ROS environment to set :envvar:`ROS_PACKAGE_PATH` (if you
            haven't already)::

              . /path/to/setup.bash

      .. group-tab:: JSONSim

         Nothing to do!

      .. group-tab:: YAMLSim

         Nothing to do!

#. Run SIERRA (invocation inspired by :ref:`usage/examples`).

   .. tabs::

      .. group-tab:: ARGoS

         ::

            sierra-cli \
            --sierra-root=$HOME/research/exp \
            --expdef-template=$HOME/research/sierra-sample-project/exp/argos/template.argos \
            --n-runs=4 \
            --engine=engine.argos \
            --project=projects.sample_argos \
            --physics-n-engines=1 \
            --controller=foraging.footbot_foraging \
            --scenario=LowBlockCount.10x10x1 \
            --batch-criteria population_size.Log8 \
            --with-robot-leds \
            --with-robot-rab \
            --exp-overwrite

         This will run a batch of 4 experiments using the
         ``projects.sample_argos.so`` C++ library. The swarm size will be varied
         from 1..8, by powers of 2. Within each experiment, 4 copies of each
         simulation will be run (each with different random seeds), for a total
         of 16 ARGoS simulations.  On a reasonable machine it should take about
         1 minute or so to run. After it finishes, you can go to
         ``$HOME/research/exp`` and find all the simulation outputs, including
         camera ready graphs! For an explanation of SIERRA's runtime directory
         tree, see :ref:`usage/run-time-tree`. You can also run the same
         experiment again, and it will overwrite the previous one because you
         passed ``--exp-overwrite``.

         .. NOTE:: The ``--with-robot-rab`` and ``--with-robot-leds`` arguments
                   are required because robot controllers in the sample project
                   use the RAB and LED sensor/actuators, and SIERRA strips those
                   tags out of the robots ``<sensors>`` and ``<actuators>`` and
                   ``<media>`` parent tags by default to increase speed and
                   reduce the memory footprint of ARGoS simulations.

      .. group-tab:: ROS1+Gazebo

         ::

            sierra-cli \
            --sierra-root=$HOME/research/exp \
            --expdef-template=$HOME/research/sierra-sample-project/exp/ros1gazebo/turtlebot3_house.launch \
            --n-runs=4 \
            --engine=engine.ros1gazebo \
            --project=projects.sample_ros1gazebo \
            --controller=turtlebot3.wander \
            --scenario=HouseWorld.10x10x1 \
            --batch-criteria population_size.Log8 \
            --robot turtlebot3 \
            --exp-overwrite \
            --pipeline 1 2

         This will run a batch of 4 experiments. The swarm size will be varied
         from 1..8, by powers of 2. Within each experiment, 4 copies of each
         simulation will be run (each with different random seeds), for a total
         of 16 Gazebo simulations.  Only the first two pipeline stages are run,
         because this controller does not produce any output. You can also run
         the same experiment again, and it will overwrite the previous one
         because you passed ``--exp-overwrite``.

      .. group-tab:: JSONSim

         ::

            sierra-cli \
            --sierra-root=$HOME/research/exp \
            --expdef-template=$HOME/research/sierra-sample-project/exp/jsonsim/template.json \
            --n-runs=4 \
            --engine=plugins.jsonsim \
            --project=projects.sample_jsonsim \
            --controller=default.default \
            --scenario=scenario1 \
            --batch-criteria max_speed.1.9.C3 \
            --exp-overwrite

         This will run a batch of 3 experiments. The max speed of agents will be
         varied from 1..9. Within each experiment, 4 copies of each simulation
         will be run (each with different random seeds), for a total of 16
         imaginary simulations. you can run the same experiment again, and it
         will overwrite the previous one because you passed ``--exp-overwrite``.

      .. group-tab:: YAMLSim

         ::

            sierra-cli \
            --sierra-root=$HOME/research/exp \
            --expdef-template=$HOME/research/sierra-sample-project/exp/yamlsim/template.yaml \
            --n-runs=4 \
            --engine=plugins.yamlsim \
            --project=projects.sample_yamlsim \
            --controller=default.default \
            --scenario=scenario1 \
            --batch-criteria max_speed.1.9.C3 \
            --exp-overwrite

         This will run a batch of 3 experiments. The max speed of agents will be
         varied from 1..9. Within each experiment, 4 copies of each simulation
         will be run (each with different random seeds), for a total of 16
         imaginary simulations. you can run the same experiment again, and it
         will overwrite the previous one because you passed ``--exp-overwrite``.

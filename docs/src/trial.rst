.. _ln-sierra-trial:

=================
Trying Out SIERRA
=================

If you just want to try SIERRA out with a pre-existing :term:`Project` without
first defining your own, the steps to do so below. I assume that all
repositories are cloned into ``$HOME/research``; adjust the paths accordingly if
you clone things somewhere else.

#. Install OS packages (if you don't see your OS below you will have to find and
   install the equivalent packages).

   .. tabs::

           .. group-tab:: Ubuntu

              Install the following required packages with ``apt install``:

              - ``parallel``
              - ``cm-super``
              - ``texlive-fonts-recommended``
              - ``texlive-latex-extra``
              - ``dvipng``
              - ``psmisc``

              Install the following optional packages with ``apt install``:

              - ``pssh``
              - ``ffmpeg``
              - ``xvfb``

           .. group-tab:: OSX

              Install the following required packages with ``brew install``:

              - ``parallel``
              - ``--cask mactex``
              - ``pssh``

              Install the following optional packages with ``brew install``:

              - ``--cask xquartz``
              - ``pssh``
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

#. Setup your chosen :term:`Platform`:

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

         #.  Install the `SIERRA ROSBridge <https://github.com/jharwell/sierra_rosbridge>`_::

               pip3 install catkin_tools
               git clone https://github.com/jharwell/sierra_rosbridge.git
               cd sierra_rosbridge
               catkin init
               catkin config --extend /opt/ros/<distro>

            Where ``<distro>`` is replaced by your ROS distro.  Finally, set
            catkin to install at a common location (e.g.,
            ``$HOME/.local/ros/noetic``) and build the package::

              catkin config --install -DCMAKE_INSTALL_PREFIX=$HOME/.local/ros/noetic
              catkin build


#. Download and build the super-simple SIERRA sample project for your chosen
   :term:`Platform`:

   .. tabs::

      .. group-tab:: ARGoS

         Based on the `foraging example
         <https://www.argos-sim.info/examples.php>`_ from the ARGoS website::

           git clone https://github.com/jharwell/sierra-sample-project.git
           cd sierra-sample-project/argos
           git checkout devel
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
           git checkout devel
           catkin init
           catkin config --extend=$HOME/.local/ros/noetic
           catkin build

         Where ``$HOME/.local/ros/noetic`` is where I installed the SIERRA
         ROSBridge into.


#. Setup runtime environment:

   .. tabs::

      .. group-tab:: ARGoS

         #. Set :envvar:`SIERRA_PLUGIN_PATH`::

              export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-project/projects

         #. Set :envvar:`ARGOS_PLUGIN_PATH`::

              export ARGOS_PLUGIN_PATH=$HOME/research/sierra-sample-project/argos/build:<ARGOS_INSTALL_DIR>/lib/argos3

            Where ``<ARGOS_INSTALL_DIR>`` is the prefix that you installed ARGoS
            to.

      .. group-tab:: ROS1+Gazebo

         #. Set :envvar:`SIERRA_PLUGIN_PATH`::

              export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-project/projects/ros1gazebo_project

         #. Source ROS environment to set :envvar:`ROS_PACKAGE_PATH` (if you
            haven't already)::

              . /path/to/setup.bash


#. Run SIERRA (invocation inspired by :ref:`ln-sierra-usage-examples`). You can do this
   from any directory! (yay SIERRA!)

   .. tabs::

      .. group-tab:: ARGoS

         ::

            sierra-cli \
            --sierra-root=$HOME/research/exp \
            --template-input-file=exp/argos/template.argos \
            --n-runs=4 \
            --platform=platform.argos \
            --project=argos_project \
            --physics-n-engines=1 \
            --controller=foraging.footbot_foraging \
            --scenario=LowBlockCount.10x10x1 \
            --batch-criteria population_size.Log8 \
            --with-robot-leds \
            --with-robot-rab \
            --exp-overwrite

         This will run a batch of 4 experiments using the ``argos_project.so``
         C++ library. The swarm size will be varied from 1..8, by powers
         of 2. Within each experiment, 4 copies of each simulation will be run
         (each with different random seeds), for a total of 16 ARGoS
         simulations.  On a reasonable machine it should take about 1 minute or
         so to run. After it finishes, you can go to ``$HOME/research/exp`` and
         find all the simulation outputs, including camera ready graphs! For an
         explanation of SIERRA's runtime directory tree, see
         :ref:`ln-sierra-usage-runtime-exp-tree`. You can also run the same experiment
         again, and it will overwrite the previous one because you passed
         ``--exp-overwrite``.

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
            --template-input-file=exp/ros1gazebo/turtlebot3_house.launch \
            --n-runs=4 \
            --platform=platform.ros1gazebo \
            --project=ros1gazebo_project \
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

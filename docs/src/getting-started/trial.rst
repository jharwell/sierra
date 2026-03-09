.. _getting-started/trial:

=================
Trying Out SIERRA
=================

This page walks you through a complete SIERRA experiment using a pre-built
sample project. No plugin setup is required — just install, clone, and run.

All repositories are assumed to be cloned into ``$HOME/research``; adjust
paths if you work somewhere else.

.. note::

   Complete :doc:`installation` before starting here. The steps below assume
   ``sierra-cli`` is already on your ``PATH``.

Step 1: Install Engine-Specific Dependencies
=============================================

The sample project supports four engines. Pick the one you want to try and
follow the instructions for it.

.. tab-set::

   .. tab-item:: ARGoS

      Install :term:`ARGoS` via your chosen method (from source or via
      the ``.deb`` package). Verify the install:

      .. code-block:: bash

         argos3 --version

      .. IMPORTANT::

         If ``argos3`` is not found by your shell, SIERRA cannot launch any
         experiments. Make sure it is on your ``PATH`` before continuing.

   .. tab-item:: ROS1+Gazebo

      #. Install a supported ROS distribution. SIERRA supports **kinetic** and
         **noetic** only:

         - `ROS Noetic (Ubuntu) <http://wiki.ros.org/noetic/Installation/Ubuntu>`_
         - `ROS Kinetic (Ubuntu) <http://wiki.ros.org/kinetic/Installation/Ubuntu>`_

      #. Install Turtlebot3 packages (replace ``<distro>`` with your ROS
         distribution name):

         .. code-block:: bash

            sudo apt install \
              ros-<distro>-turtlebot3-description \
              ros-<distro>-turtlebot3-msgs \
              ros-<distro>-turtlebot3-gazebo \
              ros-<distro>-turtlebot3-bringup

      #. Install and build the SIERRA ROSBridge:

         .. code-block:: bash

            source /opt/ros/<distro>/setup.bash

            pip3 install pysip numpy matplotlib pyyaml psutil defusedxml \
                         pyparsing pydev pyopengl opencv-python \
                         catkin_tools rospkg empy

            git clone https://github.com/jharwell/sierra_rosbridge.git
            cd sierra_rosbridge
            git checkout devel
            catkin init
            catkin config --extend /opt/ros/<distro>
            catkin config --install -DCMAKE_INSTALL_PREFIX=$HOME/.local/ros/<distro>
            catkin build

   .. tab-item:: JSONSim / YAMLSim

      No engine-specific setup needed. These engines are included with SIERRA
      and run directly.

Step 2: Install Full Plugin Dependencies
========================================

The trial installs a broader set of OS packages than the core SIERRA install
requires, to enable all bundled plugins (graph rendering, video, LaTeX labels,
etc.).

.. tab-set::

   .. tab-item:: Ubuntu / Debian

      .. code-block:: bash

         sudo apt install \
           parallel psmisc pssh ffmpeg xvfb iputils-ping \
           cm-super texlive-fonts-recommended texlive-latex-extra dvipng

   .. tab-item:: macOS

      .. code-block:: bash

         brew install parallel pssh ffmpeg
         brew install --cask mactex xquartz

Step 3: Clone and Build the Sample Project
==========================================

.. tab-set::

   .. tab-item:: ARGoS

      Based on the `ARGoS foraging example <https://www.argos-sim.info/examples.php>`_:

      .. code-block:: bash

         git clone https://github.com/jharwell/sierra-sample-project.git
         cd sierra-sample-project/argos
         mkdir -p build && cd build
         cmake -DARGOS_INSTALL_DIR=<argos-install-prefix> ..
         make

      ``ARGOS_INSTALL_DIR`` should be the prefix you installed ARGoS *to* (not
      where you compiled it). This allows multiple ARGoS versions to coexist on
      one system.

   .. tab-item:: ROS1+Gazebo

      Based on the `turtlebot3 simulation tutorials
      <https://github.com/ROBOTIS-GIT/turtlebot3_simulations>`_:

      .. code-block:: bash

         git clone https://github.com/jharwell/sierra-sample-project.git
         cd sierra-sample-project/ros1gazebo
         catkin init
         catkin config --extend=$HOME/.local/ros/noetic
         catkin build

   .. tab-item:: JSONSim / YAMLSim

      No build step needed.

Step 4: Set Up the Runtime Environment
======================================

.. tab-set::

   .. tab-item:: ARGoS

      .. code-block:: bash

         export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-project
         export ARGOS_PLUGIN_PATH=$HOME/research/sierra-sample-project/argos/build:<argos-install-prefix>/lib/argos3

      Replace ``<argos-install-prefix>`` with the same prefix used in Step 3.

   .. tab-item:: ROS1+Gazebo

      .. code-block:: bash

         export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-project
         source /path/to/ros/setup.bash   # sets ROS_PACKAGE_PATH

   .. tab-item:: JSONSim / YAMLSim

      export SIERRA_PLUGIN_PATH=$HOME/research/sierra-sample-project

Step 5: Run SIERRA
==================

Pick your engine and paste the corresponding command. All examples clone the
sample project to ``$HOME/research``; adjust if needed.

.. tab-set::

   .. tab-item:: ARGoS

      .. code-block:: bash

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

      This runs 4 experiments varying swarm size from 1–8 (powers of 2).
      Each experiment runs 4 independent simulations with different random
      seeds, for 16 ARGoS simulations total. On a reasonable machine this
      takes about 1 minute.

      When complete, ``$HOME/research/exp`` contains all simulation outputs,
      processed statistics, and camera-ready graphs. See
      :doc:`../user-guide/running-experiments` for a guide to the output
      structure.

      .. NOTE::

         :ref:`--with-robot-rab<src/plugins/engine/argos/index:sierra-cli---with-robot-rab>`
         :ref:and
         :ref:`--with-robot-leds<src/plugins/engine/argos/index:sierra-cli---with-robot-leds>`
         :ref:are required here because the sample project's controllers use
         :ref:those sensor/actuator types. SIERRA strips unused sensor and
         :ref:actuator XML tags by default to reduce ARGoS's memory footprint;
         :ref:these flags restore them.

   .. tab-item:: ROS1+Gazebo

      .. code-block:: bash

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

      This runs 4 experiments varying swarm size from 1–8, with 4 runs each
      for 16 Gazebo simulations total. Only pipeline stages 1 and 2 are run
      because this controller does not produce output files — there is nothing
      for stages 3–4 to process.

      When complete, ``$HOME/research/exp`` contains the generated launch files
      and execution logs.

   .. tab-item:: JSONSim

      .. code-block:: bash

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

      This runs 3 experiments varying agent max speed from 1–9. Each experiment
      runs 4 independent simulations for 12 total. When complete,
      ``$HOME/research/exp`` contains all outputs and graphs.

   .. tab-item:: YAMLSim

      .. code-block:: bash

         sierra-cli \
           --sierra-root=$HOME/research/exp \
           --expdef-template=$HOME/research/sierra-sample-project/exp/yamlsim/template.yaml \
           --n-runs=4 \
           --engine=plugins.yamlsim \
           --project=projects.sample_yamlsim \
           --controller=default.default \
           --scenario=scenario1 \
           --batch-criteria noise_floor.1.9.C3 \
           --exp-overwrite

      Identical to JSONSim above, but using a YAML template. Runs 3 experiments
      (12 simulations total) varying noise floor from 1–9 (meaning project
      dependent).

Next Steps
==========

You have run a complete SIERRA pipeline from experiment generation through
graph output. From here:

- **Connect your own code** — follow :ref:`getting-started/setup` to create a
  project plugin and run SIERRA against your own simulator or algorithm.
- **Understand what was generated** — read :ref:`concepts/run-time-tree` for a
  full walkthrough of the output directory structure.
- **Learn the concepts** — :ref:`concepts/pipeline` explains each pipeline
  stage and why it is structured the way it is.
- **See more invocation examples** — :ref:`user-guide/examples` has annotated
  examples for common scenarios.

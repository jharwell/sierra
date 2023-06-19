===========================================================================
SIERRA (reSearch pIpEline for Reproducibility, Reusability, and Automation)
===========================================================================

.. |pepy-downloads| image:: https://pepy.tech/badge/sierra-research
                    :target: https://pepy.tech/project/sierra-research

.. |pypi-version| image:: https://img.shields.io/pypi/v/sierra-research.svg
                  :target: https://pypi.python.org/pypi/sierra-research/

.. |supported-pythons| image:: https://img.shields.io/pypi/pyversions/sierra-research.svg
                       :target: https://pypi.python.org/pypi/sierra-research/

.. |linux-supported| image:: https://img.shields.io/badge/os-Linux-crimson
.. |osx-supported| image:: https://img.shields.io/badge/os-OSX-crimson

.. |ci-integration-master| image:: https://github.com/jharwell/sierra/actions/workflows/integration-all.yml/badge.svg?branch=master
.. |ci-analysis-master| image:: https://github.com/jharwell/sierra/actions/workflows/static-analysis.yml/badge.svg?branch=master
.. |ci-coverage-master| image:: https://coveralls.io/repos/github/jharwell/sierra/badge.svg?branch=master

.. |ci-integration-devel| image:: https://github.com/jharwell/sierra/actions/workflows/integration-all.yml/badge.svg?branch=devel
.. |ci-analysis-devel| image:: https://github.com/jharwell/sierra/actions/workflows/static-analysis.yml/badge.svg?branch=devel
.. |ci-coverage-devel| image:: https://coveralls.io/repos/github/jharwell/sierra/badge.svg?branch=devel

.. |license| image:: https://img.shields.io/badge/License-MIT-blue.svg

.. |doi| image:: https://zenodo.org/badge/125774567.svg
         :target: https://zenodo.org/badge/latestdoi/125774567

.. |docs| image:: https://readthedocs.org/projects/sierra/badge/?version=master
          :target: https://sierra.readthedocs.io/en/master/

.. |maintenance| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
                  :target: https://gitHub.com/jharwell/sierra/graphs/commit-activity


:Usage:
   |pepy-downloads| |pypi-version| |supported-pythons| |linux-supported|
   |osx-supported|

:Release:

   |ci-analysis-master| |ci-integration-master| |ci-coverage-master|

:Development:

   |ci-analysis-devel| |ci-integration-devel| |ci-coverage-devel|

:Misc:

   |license| |doi| |docs| |maintenance|


TL;DR
=====

What is SIERRA? See `What is SIERRA?`_

Why should you use SIERRA? See `Why SIERRA?`_

To install SIERRA (requires python 3.8+):

::

   pip3 install sierra-research

To get started using SIERRA, see `getting started
<https://sierra.readthedocs.io/en/master/src/getting_started.html>`_.

Want to cite SIERRA? See `Citing`_.

Have an issue using SIERRA? See `Troubleshooting`_.

What is SIERRA?
===============

.. figure:: https://raw.githubusercontent.com/jharwell/sierra/master/docs/figures/architecture.png

   SIERRA architecture, organized by pipeline stage. Stages are listed left to
   right, and an approximate joint architectural/functional stack is top to
   bottom for each stage. “...” indicates areas where SIERRA is designed via
   plugins to be easily extensible. “Host machine” indicates the machine SIERRA
   was invoked on.

SIERRA is a command line tool and plugin framework for:

- Automating scientific research, providing faculties for seamless experiment
  generation, execution, and results processing.

- Accelerating research cycles by allowing researchers to focus on the “science”
  aspects: developing new things and designing experiments to test them.

- Improving the reproducibility of scientific research, particularly in AI.


Why SIERRA?
===========

- SIERRA changes the paradigm of the engineering tasks researchers must perform
  from manual and procedural to declarative and automated. That is, from::

    "I need to perform these steps to run the experiment, process the data and
    generate the graphs I want."

  to::

    "OK SIERRA: Here is the environment and simulator/robot platform I want to
    use, the deliverables I want to generate, and the data I want to appear on
    them for my research query--GO!"

  Essentially, SIERRA handles the “engineering” parts of research on the
  backend, such as: generating experiments, configuring execution environments
  or platforms, running the generated experiments, and processing experimental
  results to generate statistics, and/or visualizations. It also handles random
  seeds, algorithm stochasticity, and other low-level details.

- It eliminates manual reconfiguration of experiments across simulator/robot
  platforms by decoupling the concepts of execution environment and platform;
  any supported pair can be selected in a mix-and-match fashion (see `SIERRA
  Support Matrix`_). Thus, it removes the need for throw-away scripts for data
  processing and deliverable generation.

- SIERRA can be used with code written in any language; only bindings must be
  written in python.

- SIERRA has a rich model framework allowing you to run arbitrary models,
  generate data, and plot it on the same figure as empirical results,
  automatically.

- Its deeply modular architecture makes it easy to customize for the needs
  of a specific research project.

Not sure if SIERRA makes sense for your research? Consider the following use
cases:

- `Use Case #1: Alice The Robotics Researcher`_

- `Use Case #2: Alice The Contagion Modeler`_

If aspects of either use case sound familiar, then there is a strong chance
SIERRA could help you! SIERRA is well documented--see the `SIERRA docs
<https://sierra.readthedocs.io/en/master/>`_ to get started.

Use Case #1: Alice The Robotics Researcher
------------------------------------------

Alice is a researcher at a large university that has developed a new distributed
task allocation algorithm ``$\alpha$`` for use in a foraging task where
robots must coordinate to find objects of interest in an unknown environment and
bring them to a central location. Alice wants to implement her algorithm so she
can investigate:

- How well it scales with the number of robots, specifically if it remains
  efficient with up to 1000 robots in several different scenarios.

- How robust it is with respect to sensor and actuator noise.

- How it compares to other similar state of the art algorithms on a foraging
  task: ``$\beta,\gamma$``.

Alice is faced with the following heterogeneity matrix which she has to deal
with to answer her research queries, *in addition to the technical challenges of
the AI elements themselves*:

.. list-table::
   :header-rows: 1
   :widths: 25,25,25

   * - Algorithm

     - Contains stochasticity?

     - Outputs data in?

   * - ``$\alpha$``

     - Yes

     - CSV, rosbag

   * - ``$\beta$``

     - Yes

     - CSV, rosbag

   * - ``$\gamma$``

     - No

     - rosbag

Alice is familiar with ROS, and wants to use it with large scale simulated and
small scale real-robot experiments with TurtleBots. However, for real robots she
is unsure what data she will ultimately need, and wants to capture all ROS
messages, to avoid having to redo experiments later.  She has access to a large
SLURM-managed cluster, and prefers to develop code on her laptop.

Use Case #2: Alice The Contagion Modeler
----------------------------------------

Alice has teamed with Bob, a biologist, to model the spread of contagion among
agents in a population, and how that affects their individual and collective
abilities to do tasks. She believes her ``$\alpha$`` algorithm can be reused
in this context. However, Bob is not convinced and has selected several
multi-agent models from recent papers: ``$\delta,\epsilon$``, and wants
Alice to compare ``$\alpha$`` to them. ``$\delta$`` was originally
developed in NetLogo, for modeling disease transmission in
animals. ``$\epsilon$`` was originally developed for ARGoS to model the
effects of radiation on robots.

Alice is faced with the following heterogeneity matrix which she must deal with
with to answer her research query, *in addition to the technical challenges of
the AI elements themselves*:

.. list-table::
   :header-rows: 1
   :widths: 25,25,25

   * - Algorithm

     - Can Run On?

     - Input Requirements?

   * - ``$\alpha$``

     - ROS/Gazebo

     - XML

   * - ``$\delta$``

     - NetLogo

     - NetLogo

   * - ``$\epsilon$``

     -  ARGoS

     -  XML

Bob is interested in how the rate of contagion spread varies with agent velocity
and population size. Bob needs to prepare succinct, comprehensive visual
representations of the results of this research queries for a a presentation,
including visual comparisons of the multi-agent model as it runs for each
algorithm. He will give Alice a range of parameter values to test for each
algorithm based on his ecological knowledge, and rely on Alice to perform the
experiments. For this project, Alice does not have access to HPC resources, but
does have a handful of servers in her lab which she can use.

SIERRA Support Matrix
=====================

SIERRA supports multiple `platforms
<https://sierra.readthedocs.io/en/master/src/platform/index.html>`_ which
researchers can write code to target. In SIERRA terminology, a platform is a
"thing" (usually a simulator or robot) that you want to write to code to run
on. Note that platform != OS, in SIERRA terminology. If a SIERRA platform runs
on a given OS, then SIERRA supports doing so; if it does not, then SIERRA does
not. For example, SIERRA does not support running ARGoS on windows, because
ARGoS does not support windows.

SIERRA supports multiple execution environments for execution of experiments,
such as `High Performance Computing (HPC) environments
<https://sierra.readthedocs.io/en/master/src/exec_env/hpc.html>`_ and `real
robots <https://sierra.readthedocs.io/en/master/src/exec_env/robots.html>`_.
Which execution environment experiments targeting a given platform is (somewhat)
independent of the platform itself (see below).

SIERRA also supports multiple output formats for experimental outputs, as shown
below. SIERRA currently only supports XML experimental inputs.

SIERRA supports (mostly) mix-and-match between platforms, execution
environments, experiment input/output formats as shown in its support matrix
below. This is one of the most powerful features of SIERRA!  If your desired
platform/execution environment is not listed, see the `plugin tutorials
<https://sierrap.readthedocs.io/en/master/src/tutorials.html>`_ for how to add
it via a plugin.

.. list-table::
   :header-rows: 1
   :widths: 25,25,25,25

   * - Execution Environment

     - Platform

     - Experimental Input Format

     - Experimental Output Format

   * - `SLURM <https://slurm.schedmd.com/documentation.html>`_: An HPC cluster
       managed by the SLURM scheduler.

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - `Torque/MOAB
       <https://adaptivecomputing.com/cherry-services/torque-resource-manager>`_:
       An HPC cluster managed by the Torque/MOAB scheduler.

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - ADHOC: A miscellaneous collection of networked HPC compute nodes or
       random servers; not managed by a scheduler.


     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - Local: The SIERRA host machine,e.g., a researcher's laptop.

     - ARGoS, ROS1+Gazebo

     - XML

     - CSV, PNG

   * - ROS1+Turtlebot3: `Turtlebot3
       <https://emanual.robotis.com/docs/en/platform/turtlebot3/overview>`_
       robots with ROS1.

     - ROS1+Gazebo, ROS1+robot

     - XML

     - CSV, PNG

For more details about the platforms out experimental output formats, see below.

.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Platform

     - Description

   * - `ARGoS <https://www.argos-sim.info/index.php>`_

     - Simulator for fast simulation of large swarms. Requires ARGoS >=
       3.0.0-beta59.

   * - `ROS1 <https://ros.org>`_ + `Gazebo <https://www.gazebosim.org>`_

     - Using ROS1 with the Gazebo simulator. Requires Gazebo >= 11.9.0, ROS1
       Noetic or later.

   * - `ROS1+Robot <https://ros.org>`_

     - Using ROS1 with a real robot platform of your choice. ROS1 Noetic or
       later is required.


.. list-table::
   :header-rows: 1
   :widths: 50,50

   * - Experimental Output Format

     - Scope

   * - CSV file

     - Raw experimental outputs, transforming into heatmap images.

   * - PNG file

     - Stitching images together into videos.


Requirements To Use SIERRA
==========================

The basic requirements are:

- Recent OSX (tested with 12+) or Linux (tested with ubuntu 20.04+).

- python >= 3.8.

.. NOTE:: Windows is not supported currently. Not because it can't be supported,
          but because there are not currently any platform plugins that which
          work on windows. That is, SIERRA's OS support is dictated by the OS
          support of its current platform plugins, none of which support
          windows.

          If windows support would be helpful for your intended usage of
          SIERRA, please get in touch with me--SIERRA is written in pure
          python and can definitely be made to work on windows.

For more details, including the requirements for researcher code, see the
`SIERRA requirements
<https://sierra.readthedocs.io/en/master/src/requirements.html>`_.

Citing
======
If you use SIERRA and have found it helpful, please cite the following paper::

  @inproceedings{Harwell2022a-SIERRA,
  author = {Harwell, John and Lowmanstone, London and Gini, Maria},
  title = {SIERRA: A Modular Framework for Research Automation},
  year = {2022},
  isbn = {9781450392136},
  publisher = {International Foundation for Autonomous Agents and Multiagent Systems},
  booktitle = {Proceedings of the 21st International Conference on Autonomous Agents and Multiagent Systems},
  pages = {1905–1907}
  }

You can also cite the specific version of SIERRA used with the DOI at the top of
this page, to help facilitate reproducibility.

Troubleshooting
===============

If you have problems using SIERRA, please open an issue or post in the Github
forum and I'll be happy to help you work through it.

Contributing
============

I welcome all types of contributions, no matter how large or how small, and if
you have an idea, I'm happy to talk about it at any point :-). See `here
<https://sierra.readthedocs.io/en/master/src/contributing.html>`_
for the general procedure.

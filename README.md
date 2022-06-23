# SIERRA (reSearch pIpEline for Reproducability, Reusability, and Automation)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/swarm-robotics-sierra/badge/?version=latest)](https://swarm-robotics-sierra.readthedocs.io/en/latest/?badge=latest)

SIERRA is named thusly because it will save you a LITERAL, (not figurative)
mountain of work. It is basically a plugin-based framework for automating
research driven by the scientific method. SIERRA is well documented--see the
docs [here](https://swarm-robotics-sierra.readthedocs.io/en/latest/) to get
started using it!

# Automated Research Pipeline

![SIERRA Architecture](./docs/figures/architecture.png "
Architecture of SIERRA,organized by pipeline stage. Pipeline stages are listed
left to right, and an approximate joint architectural/functional stack is top to
bottom for each stage. “... ” indicates areas where SIERRA is designed via
python plugins to be easily extensible. “Host machine” indicates the machine
SIERRA was invoked on.")

## 1. Generating Experiment Inputs

Experiments using the scientific method have an independent variable whose
impact on results are measured through a series of trials. SIERRA allows you to
express this as a research query on the command line, and then parses your query
to make changes to a template input file to generate launch commands and
experimental inputs to operationalize it. Switching from targeting platform A
(e.g., ARGoS) to platform B (e.g., ROS1+Gazebo) is as easy as changing a a
single command line argument (assuming your code is setup to handle both ARGoS
and ROS environments!). Similarly for switching from running on the local
machine to running on a HPC cluster. SIERRA handles all the "backend" aspects of
running experiments and allows you to focus on the fun parts--the research
itself!

## 2. Running Experiments

SIERRA currently supports two types of execution environments: simulators and
real robots, which are handled seamlessly with GNU parallel. For simulators,
SIERRA will run multiple experimental runs (simulations) from each experiment in
parallel (exact concurrency dependent on the limits of the computing hardware
and the nature of the experiment). For real robots, SIERRA will execution 1
experimental run at a time, per configuration (runs can have different
configuration/# of robots).

SIERRA supports multiple HPC environments for execution of experiments in
simulation
([docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/exec_env/hpc.html))
and on real robots
([docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/exec_env/robots.html)):

| Execution Environment     | Supported Platforms |
| ------------------------- | ------------------- |
| [SLURM](https://slurm.schedmd.com/documentation.html) | ARGoS, ROS1+Gazebo |
| [Torque/MOAB](https://adaptivecomputing.com/cherry-services/torque-resource-manager) | ARGoS, ROS1+Gazebo |
| ADHOC (suitable for a miscellaneous collection of networked compute nodes for a research group) | ARGoS, ROS1+Gazebo |
| Local machine (for testing) | ARGoS, ROS+Gazebo |
| [ROS1+Turtlebot3](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview) | ROS1+Gazebo, ROS1+robot |

To add additional execution environments, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/tutorials/plugin/exec_env_plugin.html).

## 3. Processing Experiment Results

SIERRA supports a number of data formats which simulations/real robot
experiments can output their data (e.g., the number of robots engaged in a given
task over time) for processing. For more details see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/). SIERRA can
generate various statistics from the results such as confidence intervals on
observed behavior.

## 4. Generating Deliverables

SIERRA can generate many deliverables from the processed experimental results
automatically (independent of the platform/execution environment!), thus greatly
simplifying reproduction of previous results if you need to tweak a given graph
(for example). SIERRA currently supports generating the following deliverables:

   - Camera-ready linegraphs, heatmaps, 3D surfaces, and scatterplots directly
     from averaged/statistically processed experimental data using matplotlib.
   - Videos built from frames captured during simulation or real robot
     operation.
   - Videos built from captured experimental output .csv files.

For some examples, see the "Generating Deliverables" section
[here](https://www-users.cse.umn.edu/~harwe006/showcase/aamas-2022-demo).

## 5. Controller/Scenario Comparison

SIERRA can take pieces from graphs generated in stage 4 and put them on a single
graph to generate camera ready comparison graphs. It can generate comparison
graphs for:

- Different robot controllers which have all been run in the same scenario.
- A single robot controller which has been run in multiple scenarios.

# Platform Support

SIERRA currently supports the following platforms, allowing you to use the same
interface for the below pipeline to automate your research workflow:

- [ARGoS](https://www.argos-sim.info/index.php) for fast simulation of large
  robot swarms via multiple physics engines.

- [Gazebo](https://www.gazebosim.org) for ROS1+Gazebo.

- [ROS](https://ros.org) for ROS on a real robot.

To define additional platforms, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/tutorials/plugin/platform_plugin.html).

# Requirements

- python >= 3.9.
- ARGoS >= 3.0.0-beta59 (if you are using ARGoS).
- ROS1 Melodic or later (if you are using ROS).
- Gazebo 11.9.0 or later (if you are using ROS1+Gazebo).


# Installing SIERRA

    pip3 install sierra-research

# Citing
If you use SIERRA and have found it helpful, please cite the following paper:

    @inproceedings{Harwell2022a-SIERRA,
    author = {Harwell, John and Lowmanstone, London and Gini, Maria},
    title = {SIERRA: A Modular Framework for Research Automation},
    year = {2022},
    isbn = {9781450392136},
    publisher = {International Foundation for Autonomous Agents and Multiagent Systems},
    booktitle = {Proceedings of the 21st International Conference on Autonomous Agents and Multiagent Systems},
    pages = {1905–1907}
    }

# Contributing

See [here](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/contributing.html) to get started.

# License
This project is licensed under GPL 3.0. See [LICENSE](LICENSE.md).

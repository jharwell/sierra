# SIERRA (reSearch pIpEline Reusable Robotics Automation)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/swarm-robotics-sierra/badge/?version=latest)](https://swarm-robotics-sierra.readthedocs.io/en/latest/?badge=latest)

SIERRA is named thusly because it will save you a LITERAL, (not figurative)
mountain of work. It is basically a plugin framework for automating a common
research pipeline in robotics, and contains the following 5 stage
pipeline. SIERRA is well documented--see the docs
[here](https://swarm-robotics-sierra.readthedocs.io/en/latest/) to get started
using it!

# Automated Research Pipeline

## 1. Generating experiment inputs

SIERRA allows you to investigate some variable(s) of interest across some
range(s) for arbitrary system sizes, robot controllers, and scenarios (exact
capabilities depend on the controller+support code you have written). To do
this, it uses a python specification of your variable(s) to generate launch
commands for simulatins/real robot code.

## 2. Running experiments

SIERRA supports two types of execution environments: simulators and real robots,
which are handled seamlessly with GNU parallel. For simulators, SIERRA will run
multiple experimental runs (simulations) from each experiment in parallel (exact
concurrency dependent on the limits of the computing hardware and the nature of
the experiment). For real robots, SIERRA will execution 1 experimental run at a
time, per configuration (runs can have different configuration/# of robots).

SIERRA supports multiple HPC environments for execution of experiments in
simulation
([docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/hpc/index.html)):

- [SLURM](https://slurm.schedmd.com/documentation.html).
- [Torque/MOAB](http://docs.adaptivecomputing.com/torque/5-0-1/help.htm#topics/torque/0-intro/torquewelcome.htm%3FTocPath%3DWelcome%7C_____0).
- ADHOC (suitable for a miscellaneous collection of networked compute nodes
  for a research group).
- Local machine (for testing).

To add additional HPC environments, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/tutorials/index.html)

SIERRA supports the following real robot targets:

- ROS/turtlebot3.

To add additional robot targets, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/tutorials/index.html).

## 3. Processing experiment results

SIERRA supports a number of data formats which simulations/real robot
experiments can output their data (e.g., the number of robots engaged in a given
task over time) for processing. For more details see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/). SIERRA can
generate various statistics from the results such as confidence intervals on
observed behavior.

## 4. Generating deliverables

SIERRA can generate many deliverables from the processed experimental results
automatically (independent of the platform/execution environment!), thus greatly
simplifying reproduction of previous results if you need to tweak a given graph
(for example). SIERRA currently supports generating the following deliverables:

   - Camera-ready linegraphs, heatmaps, 3D surfaces, and scatterplots directly
     from averaged/statistically processed experimental data using matplotlib.
   - Videos built from frames captured during simulation or real robot
     operation.
   - Videos built from captured experimental output .csv files.

## 5. Controller/scenario comparison

SIERRA can take pieces from graphs generated in stage 4 and put them on a single
graph to generate camera ready comparison graphs. It can generate comparison
graphs for:

- Different robot controllers which have all been run in the same scenario.
- A single robot controller which has been run in multiple scenarios.

# Platform Support

SIERRA currently supports the following platforms, allowing you to use the same
interface for the above pipeline
([docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/platform/index.html)):

- [ARGoS](https://www.argos-sim.info/index.php) for fast simulation of large
  robot swarms via multiple physics engines.
- [ROS](https://www.ros.org) for real robots.

To define additional platforms, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/tutorials/index.html).

# Requirements

- python >= 3.6.
- ARGoS >= 3.0.0-beta59 (if you are using ARGoS)

# Contributing

See [here](https://swarm-robotics-sierra.readthedocs.io/en/latest/src/contributing.html) to get started.

# License
This project is licensed under GPL 3.0. See [LICENSE](LICENSE.md).

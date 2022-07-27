# SIERRA (reSearch pIpEline for Reproducibility, Reusability, and Automation)


| Usage   | Release | Development |
|---------|---------|-------------|
| [![](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) | ![](https://github.com/swarm-robotics/sierra/actions/workflows/static-analysis.yml/badge.svg?branch=master) | ![](https://github.com/swarm-robotics/sierra/actions/workflows/static-analysis.yml/badge.svg?branch=devel) |
| [![Python 3.8](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-360/)  | ![](https://github.com/swarm-robotics/sierra/actions/workflows/argos-integration-tests.yml/badge.svg?branch=master) | ![](https://github.com/swarm-robotics/sierra/actions/workflows/argos-integration-tests.yml/badge.svg?branch=devel) |
| [![Linux](https://svgshare.com/i/Zhy.svg)](https://svgshare.com/i/Zhy.svg) [![macOS](https://svgshare.com/i/ZjP.svg)](https://svgshare.com/i/ZjP.svg) |![](https://github.com/swarm-robotics/sierra/actions/workflows/ros1gazebo-integration-tests.yml/badge.svg?branch=master) | ![](https://github.com/swarm-robotics/sierra/actions/workflows/ros1gazebo-integration-tests.yml/badge.svg?branch=devel) |
| [![Downloads](https://pepy.tech/badge/sierra-research)](https://pepy.tech/project/sierra-research)  | [![](https://readthedocs.org/projects/swarm-robotics-sierra/badge/?version=master)](https://swarm-robotics-sierra.readthedocs.io/en/master/?badge=master) | [![](https://readthedocs.org/projects/swarm-robotics-sierra/badge/?version=master)](https://swarm-robotics-sierra.readthedocs.io/en/master/?badge=devel)|
| [![DOI](https://zenodo.org/badge/125774567.svg)](https://zenodo.org/badge/latestdoi/125774567) | |


# Installing SIERRA

    pip3 install sierra-research

# Why SIERRA?

![SIERRA Architecture](https://raw.githubusercontent.com/swarm-robotics/sierra/master/docs/figures/architecture.png "
Architecture of SIERRA,organized by pipeline stage. Pipeline stages are listed
left to right, and an approximate joint architectural/functional stack is top to
bottom for each stage. “... ” indicates areas where SIERRA is designed via
python plugins to be easily extensible. “Host machine” indicates the machine
SIERRA was invoked on.")

SIERRA is a command line tool for automating the pipeline described above,
providing faculties for seamless experiment generation, execution, and results
processing. SIERRA accelerates research cycles by allowing researchers to focus
on the “science” aspects: developing AI elements and designing experiments to
test them. SIERRA changes the paradigm of the engineering tasks researchers must
perform from manual and procedural to declarative and automated. That is, from
“Do these steps to run the experiment, process the data and generate graphs” to
“Here is the environment and platform, the deliverables I want to generate and
the data I want to appear on them for my research query--GO!”. Essentially,
SIERRA handles the “backend” parts of research, such as: random seeds, algorithm
stochasticity, configuration for a given execution environment or platform,
generating statistics from experimental results, and generating visualizations
from processed results. By employing declarative researcher specification via
command line arguments and YAML configuration, it eliminates manual
reconfiguration of experiments across platforms by decoupling the concepts of
execution environment platform; any supported pair can be selected in a
mix-and-match fashion (see below). Furthermore, it removes the need for
throw-away scripts for data processing and deliverable generation by providing
rich, extensible faculties for those pipeline stages.

Consider the two use cases below: within each, SIERRA provides faculties for
managing heterogeneity and automating common tasks to reduce the burden on
researchers, either directly or through a rich plugin interface.  If aspects of
either use case sound familiar, then there is a strong chance SIERRA could help
you with your research! SIERRA is well documented--see the docs
[here](https://swarm-robotics-sierra.readthedocs.io/en/master/) for more info on
the automation it provides and to get started using it!

## Use Case #1: Alice The Robotics Researcher

Alice is a researcher at a large university that has developed a distributed new
task allocation algorithm $\alpha$ for use in a foraging task where robots must
coordinate to find objects of interest in an unknown environment and bring them
to a central location. Alice wants to implement her algorithm so she can
investigate:

- How well it scales with the number of robots, specifically if it remains
  efficient with up to 1000 robots in several different scenarios.

- How robust it is with respect to sensor and actuator noise.

- How it compares to other similar state of the art algorithms on a foraging
  task: $\beta,\gamma$.

Alice is faced with the following heterogeneity matrix which she has to deal
with to answer her research queries, _in addition to the technical challenges of
the AI elements themselves_:

| Algorithm | Contains stochasticity? | Outputs data in? |
|-----------|-------------------------|------------------|
| $\alpha$  | Yes                     | CSV, rosbag      |
| $\beta$   | Yes                     | CSV, rosbag      |
| $\gamma$  | No                      | rosbag           |

Alice is familiar with ROS, and wants to use it with large scale simulated and
small scale real-robot experiments with TurtleBots. However, for real robots she
is unsure what data she will ultimately need, and wants to capture all ROS
messages, to avoid having to redo experiments later.  She has access to a large
SLURM-managed cluster, and prefers to develop code on her laptop.

## Use Case#2: Alice The Contagion Modeler

Alice has teamed with Bob, a biologist, to model the spread of contagion among
agents in a population, and how that affects their individual and collective
abilities to do tasks. She believes her α algorithm can be reused in this
context. However, Bob is not convinced and has selected several multi-agent
models from recent papers: $\delta$,$\epsilon$, and wants Alice to compare
$\alpha$ to them. $\delta$ was originally developed in NetLogo, for modeling
disease transmission in animals. $\epsilon$ was originally developed for ARGoS
to model the effects of radiation on robots.

Alice is faced with the following heterogeneity matrix which she must deal with
with to answer her research query, _in addition to the technical challenges of
the AI elements themselves_:

| Algorithm  | Can Run On? | Input Requirements? |
|------------|-------------|---------------------|
| $\alpha$   | ROS/Gazebo  | XML                 |
| $\delta$   | NetLogo     | NetLogo             |
| $\epsilon$ | ARGoS       | XML                 |

Bob is interested in how the rate of contagion spread varies with agent velocity
and population size. Bob needs to prepare succinct, comprehensive visual
representations of the results of this research queries for a a presentation,
including visual comparisons of the multi-agent model as it runs for each
algorithm. He will give Alice a range of parameter values to test for each
algorithm based on his ecological knowledge, and rely on Alice to perform the
experiments. For this project, Alice does not have access to HPC resources, but
does have a handful of servers in her lab which she can use.

# SIERRA Support Matrix

SIERRA supports multiple platforms which researchers can write code to target
([docs](https://swarm-robotics-sierra.readthedocs.io/en/master/src/platform/index.html)). SIERRA
supports multiple execution environments for execution of experiments, such as
High Performance Computing (HPC) environments
([docs](https://swarm-robotics-sierra.readthedocs.io/en/master/src/exec_env/hpc.html))
and real robots
([docs](https://swarm-robotics-sierra.readthedocs.io/en/master/src/exec_env/robots.html)). If
your desired platform or execution environment is not listed, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/master/src/tutorials.html)
for how to add it via a plugin.

| Execution Environment                                                                | Description                                                                      |
|--------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [SLURM](https://slurm.schedmd.com/documentation.html)                                | A cluster managed by the SLURM scheduler                                         |
| [Torque/MOAB](https://adaptivecomputing.com/cherry-services/torque-resource-manager) | A cluster managed by the Torque/MOAB scheduler                                   |
| ADHOC                                                                                | Miscellaneous collection of networked compute nodes (not managed by a scheduler) |
| Local                                                                                | The SIERRA host machine (e.g., a researcher's laptop)                            |
| [Turtlebot3](https://emanual.robotis.com/docs/en/platform/turtlebot3/overview)       | Real turtlebot3 robots                                                           |

| Platform                                                    | Description                                                                             |
|-------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| [ARGoS](https://www.argos-sim.info/index.php)               | Simulator for fast simulation of large swarms. Requires ARGoS >= 3.0.0-beta59.          |
| [ROS1](https://ros.org)+[Gazebo](https://www.gazebosim.org) | Using ROS1 with the Gazebo simulator. Requires Gazebo >= 11.9.0, ROS1 Noetic or later.  |
| [ROS1](https://ros.org)+Robot                               | Using ROS1 with a real robot platform of your choice. ROS1 Noetic or later is required. |

SIERRA also supports multiple output formats for experimental outputs. If the
format for your experimental outputs is not listed, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/master/src/tutorials.html)
for how to add it via a plugin. SIERRA currently only supports XML experimental
inputs.

| Experimental Output Format | Scope                                                     |
|----------------------------|-----------------------------------------------------------|
| CSV file                   | Raw experimental outputs, tranforming into heatmap images |
| PNG file                   | Stitching images together into videos                     |

SIERRA supports (mostly) mix-and-match between platforms, execution
environments, experiment input/output formats as shown in its support matrix
below. This is one of the most powerful features of SIERRA!

| Execution Environment     | Platform                | Experimental Input Format | Experimental Output Format  |
| ------------------------- | ----------------------- | ------------------------- | --------------------------- |
| SLURM                     | ARGoS, ROS1+Gazebo      | XML                       | CSV, PNG                    |
| Torque/MOAB               | ARGoS, ROS1+Gazebo      | XML                       | CSV, PNG                    |
| ADHOC                     | ARGoS, ROS1+Gazebo      | XML                       | CSV, PNG                    |
| Local                     | ARGoS, ROS1+Gazebo      | XML                       | CSV, PNG                    |
| ROS1+Turtlebot3           | ROS1+Gazebo, ROS1+robot | XML                       | CSV, PNG                    |

# Requirements To Use SIERRA

The basic requirements are:

- Recent OSX or Linux (Windows is not supported).

- python >= 3.8.

For more details, such requirements for researcher code, see the
[docs](https://swarm-robotics-sierra.readthedocs.io/en/master/src/requirements.html).

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

You can also cite the specific version of SIERRA used with the DOI at the top of
this page, to help facilitate reproducibility.

# Contributing

See
[here](https://swarm-robotics-sierra.readthedocs.io/en/master/src/contributing.html)
to get started.

# License
This project is licensed under GPL 3.0. See [LICENSE](LICENSE.md).

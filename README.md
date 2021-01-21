# SIERRA (Swarm IntElligence Reusable ARGoS Automation)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/swarm-robotics-sierra/badge/?version=latest)](https://swarm-robotics-sierra.readthedocs.io/en/latest/?badge=latest)

Python framework for automating a common research pipeline in swarm
robotics. ARGoS extension. It is named thusly because it will save you a
LITERAL, (not figurative) mountain of work.

Automated pipeline currently contains:

1. Generating simulation inputs for experiments simulations to investigate some
   variable(s) of interest across some range(s).

2. Running all simulations in parallel. Supports multiple HPC environments such as:

    - [slurm](https://slurm.schedmd.com/documentation.html)
    - Torque/MOAB (http://docs.adaptivecomputing.com/torque/5-0-1/help.htm#topics/torque/0-intro/torquewelcome.htm%3FTocPath%3DWelcome%7C_____0)
    - ADHOC (suitable for a miscellaneous collection of networked compute nodes
      for a research group)

    Also supports running on the local machine for testing.

3. Averaging simulation results to obtain confidence obtain on observed performance.

4. Generating camera-ready outputs such as (1) graphs of simulation results via
   YAML configuration, (2) videos of simulation execution, (3) videos rendered
   from simulation outputs.

This is the reusable CORE part of SIERRA; to use SIERRA with your project, you
will need to defined a project plugin, as described in the documentation
[here](https://swarm-robotics-sierra.readthedocs.io/en/latest/).

# Requirements
You need python 3.6 or later to run SIERRA.

# License
This project is licensed under GPL 3.0. See [LICENSE](LICENSE.md).

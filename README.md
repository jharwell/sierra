# SIERRA (Swarm IntElligence Reusable ARGoS Automation)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/swarm-robotics-sierra/badge/?version=latest)](https://swarm-robotics-sierra.readthedocs.io/en/latest/?badge=latest)

Python framework for automating a common research pipeline in swarm
robotics. ARGoS driver. It is named thusly because it will save you a
LITERAL, (not figurative) mountain of work.

Automated pipeline currently contains:

1. Generating simulation inputs for experiments simulations to investigate some
   variable(s) of interest across some range(s) for arbitrary swarm sizes, robot
   controllers, and scenarios (exact capabalitities depend on the
   controller+support code you have written).

2. Running all simulations in parallel. Supports multiple HPC environments such
   as:

   - [SLURM](https://slurm.schedmd.com/documentation.html).
   - [Torque/MOAB](http://docs.adaptivecomputing.com/torque/5-0-1/help.htm#topics/torque/0-intro/torquewelcome.htm%3FTocPath%3DWelcome%7C_____0).
   - ADHOC (suitable for a miscellaneous collection of networked compute nodes
     for a research group).
   - Local machine (for testing).

3. Averaging simulation results to obtain confidence intervals on observed
   behavior.

4. Generating camera-ready outputs such as:

   - Graphs of simulation results
   - Videos of simulation execution, captured using ARGoS rendering facilities
   - Videos built from captured simulation output .csv files.

5. Generating camera ready graphs comparing swarm behaviors within a single
   scenario and across multiple scenarios.


This is the reusable CORE part of SIERRA; to use SIERRA with your project, you
will need to defined a project plugin, as described in the documentation
[here](https://swarm-robotics-sierra.readthedocs.io/en/latest/).

# Requirements
You need python 3.6 or later to run SIERRA.

# License
This project is licensed under GPL 3.0. See [LICENSE](LICENSE.md).

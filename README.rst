===========================================================================
SIERRA (reSearch pIpEline for Reproducibility, Reusability, and Automation)
===========================================================================

.. |pepy-downloads| image:: https://pepy.tech/badge/sierra-research
                    :target: https://pepy.tech/project/sierra-research

.. |pypi-version| image:: https://img.shields.io/pypi/v/sierra-research.svg
                  :target: https://pypi.python.org/pypi/sierra-research/

.. |supported-pythons| image:: https://img.shields.io/pypi/pyversions/sierra-research.svg

.. |os-supported| image:: https://img.shields.io/badge/os-linux%20%7C%20macOS-blue

.. |ci-analysis-master| image:: https://github.com/jharwell/sierra/actions/workflows/analysis-top.yml/badge.svg?branch=master
.. |ci-coverage-master| image:: https://coveralls.io/repos/github/jharwell/sierra/badge.svg?branch=master

.. |ci-analysis-devel| image:: https://github.com/jharwell/sierra/actions/workflows/analysis-top.yml/badge.svg?branch=devel
.. |ci-coverage-devel| image:: https://coveralls.io/repos/github/jharwell/sierra/badge.svg?branch=devel

.. |license| image:: https://img.shields.io/github/license/jharwell/sierra
   :alt: GitHub License

.. |doi| image:: https://zenodo.org/badge/125774567.svg
         :target: https://zenodo.org/badge/latestdoi/125774567

.. |docs| image:: https://readthedocs.org/projects/sierra/badge/?version=master
          :target: https://sierra.readthedocs.io/en/master/

.. |maintenance| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
                 :target: https://github.com/jharwell/sierra/graphs/commit-activity


+---------------+--------------------------------------------------------------------+
| Usage         | |pepy-downloads| |pypi-version| |supported-pythons| |os-supported| |
+---------------+--------------------------------------------------------------------+
| Release       | |ci-analysis-master| |ci-coverage-master|                          |
+---------------+--------------------------------------------------------------------+
| Development   | |ci-analysis-devel| |ci-coverage-devel|                            |
+---------------+--------------------------------------------------------------------+
| Miscellaneous |    |license| |doi| |docs| |maintenance|                            |
+---------------+--------------------------------------------------------------------+


Quick Links
===========

- `What is SIERRA?`_ — Overview and architecture
- `Features at a Glance`_ — Supported platforms and capabilities
- `Why SIERRA?`_ — Motivation and comparison with alternatives
- `Quick Start`_ — Install and run your first experiment
- `Citing`_ — How to cite SIERRA in your research
- `Troubleshooting`_ — Common issues and how to get help
- `Contributing`_ — How to contribute to SIERRA


What is SIERRA?
===============

.. figure:: https://raw.githubusercontent.com/jharwell/sierra/master/docs/figures/architecture.png

   SIERRA architecture, organized by pipeline stage, left to right. High-level
   inputs/outputs and active plugins are shown for each stage. "..." indicates
   areas of further extensibility and customization via new plugins. "Host
   machine" indicates the machine SIERRA was invoked on. The active plugins in
   each stage and what they cumulatively enable are highlighted in red. See
   `pipeline documentation
   <https://sierra.readthedocs.io/en/master/src/pipeline.html>`_ for a
   detailed walkthrough of each stage.

SIERRA is a command line tool and plugin framework for:

- **Automating R&D**, providing facilities for seamless experiment
  generation, execution, and results processing.

- **Accelerating R&D cycles** by allowing researchers and developers to focus
  on the "science"—developing new ideas and designing experiments to test
  them—rather than the engineering (writing scripts, configuring environments,
  etc.).

- **Improving reproducibility** of scientific research, particularly in AI and
  autonomous systems.

In practice, this means you can run a 50-condition parameter sweep across
multiple simulators, generate comparative plots overlaid with model predictions,
and archive fully reproducible results—all with a single SIERRA command.


Features at a Glance
====================

+-------------------------------+--------------------------------------------------+
| Feature                       | Details                                          |
+===============================+==================================================+
| Supported simulators          | ARGoS, ROS1+Gazebo, ROS1+Robot,custom via plugins|                 |
+-------------------------------+--------------------------------------------------+
| Execution environments        | Local machine, HPC clusters (SLURM, PBS), custom |
+-------------------------------+--------------------------------------------------+
| Parameter sweeps              | Numeric, categorical, or mixed combinations      |
+-------------------------------+--------------------------------------------------+
| Output formats                | CSV, GraphML, graphs/plots, video, custom via plugins     |
+-------------------------------+--------------------------------------------------+
| Model framework               | Overlay analytical models on empirical results   |
+-------------------------------+--------------------------------------------------+
| Reproducibility               | Fully archived, citable experiment configurations|
+-------------------------------+--------------------------------------------------+
| Python version                | 3.9+                                             |
+-------------------------------+--------------------------------------------------+
| OS support                    | Linux (Ubuntu 20.04+), macOS 13+                 |
+-------------------------------+--------------------------------------------------+


Quick Start
===========

**Install** (requires Python 3.9+):

.. code-block:: shell

   pip3 install sierra-research

**Run your first experiment:**

.. code-block:: shell

   sierra-cli \
     --template-input-file=my-experiment.xml \
     --n-runs=4 \
     --time-setup=time_setup.T10000 \
     --scenario=RN.10x10 \
     --batch-criteria population_size.Log8

This single command generates all experiment inputs, runs them (locally or on a
cluster), and processes results into graphs—no scripting required. See `getting
started <https://sierra.readthedocs.io/en/master/src/getting_started.html>`_ for
a full walkthrough.


Why SIERRA?
===========

SIERRA changes the paradigm of the engineering tasks researchers must perform
from manual and procedural to **declarative and automated**. That is, from:

.. code-block:: text

   "I need to perform these steps to run the experiment, process the data and
   generate the graphs I want."

to:

.. code-block:: text

   "Here is the environment and simulator/platform(s) I want to use, the
   deliverables I want to generate, and the data I want to appear on them for
   my research query—GO!"

Essentially, SIERRA handles the "engineering" parts of research as a backend
compiler of sorts: turning research queries into executable objects, running the
compiled experiments, and processing results into visualizations or other
deliverables.

**Key advantages:**

- **Deep parameter sweep support** — numeric, categorical, or any combination
  thereof, with no boilerplate.

- **Broad platform coverage via plugins** — supports a wide range of execution
  engines and experiment I/O formats. Mix and match simulators (ARGoS, ROS2),
  execution environments (local, SLURM, PBS), and output formats with little to
  no configuration changes.

- **Maximum reusability** — designed so that *no* copy-pasting is ever needed,
  improving code quality with no additional effort.

- **Rich model framework** — run arbitrary analytical models, generate synthetic
  data, and overlay it on empirical results automatically on the same figure.

- **Research-domain focus** — built specifically for the scientific research
  workflow, with native concepts for experiments, runs, batch criteria, and
  replication.

**Why SIERRA over Prefect, Dagster, or Airflow?**

General-purpose workflow tools like `Prefect <https://www.prefect.io>`_,
`Dagster <https://www.dagster.io>`_, and `Airflow
<https://airflow.apache.org>`_ require you to build your own research pipelines
from scratch. SIERRA provides a battle-tested pipeline with first-class support
for the patterns that matter most in R&D: parameter sweeps, simulator
integration, reproducible archiving, and model-vs-empirical plotting.

The trade-off: SIERRA is more opinionated and less feature-complete than those
frameworks for general data engineering workloads. For most research use cases,
that gap doesn't matter—and the domain-specific abstractions save significant
time and effort.

Not sure if SIERRA makes sense for your work? Check out some of the `use cases
<https://sierra.readthedocs.io/en/master/src/use-cases.html>`_ for which SIERRA
was designed. If aspects of any sound familiar, there is a strong chance SIERRA
could help. See the `SIERRA docs <https://sierra.readthedocs.io/en/master/>`_
to get started.


Citing
======

If you use SIERRA and have found it helpful, please cite the following paper:

.. code-block:: bibtex

  @inproceedings{Harwell2022a-SIERRA,
  author = {Harwell, John and Lowmanstone, London and Gini, Maria},
  title = {SIERRA: A Modular Framework for Research Automation},
  year = {2022},
  isbn = {9781450392136},
  publisher = {International Foundation for Autonomous Agents and Multiagent Systems},
  booktitle = {Proceedings of the 21st International Conference on Autonomous Agents and Multiagent Systems},
  pages = {1905–1907}
  }

You can also cite the specific version of SIERRA used with the DOI badge at the
top of this page, to help facilitate reproducibility.


Troubleshooting
===============

If you encounter problems using SIERRA, please `open an issue
<https://github.com/jharwell/sierra/issues>`_ or post in the `GitHub
Discussions <https://github.com/jharwell/sierra/discussions>`_ forum. Please
include your SIERRA version, OS, and a minimal reproducible example where
possible.


Contributing
============

Contributions of all sizes are welcome—bug fixes, documentation improvements,
new plugins, or larger features. If you have an idea to discuss before diving
in, feel free to open a discussion thread at any point. See the `contributing
guide <https://sierra.readthedocs.io/en/master/src/contributing.html>`_ for the
general procedure.

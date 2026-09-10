.. |pypi-version| image:: https://img.shields.io/pypi/v/sierra-research.svg
                  :target: https://pypi.python.org/pypi/sierra-research/

.. |ci-analysis-master| image:: https://github.com/jharwell/sierra/actions/workflows/analysis-top.yml/badge.svg?branch=master
                        :target: https://github.com/jharwell/sierra/actions/workflows/analysis-top.yml

.. |docs| image:: https://readthedocs.org/projects/sierra/badge/?version=master
          :target: https://sierra.readthedocs.io/en/master/

.. |doi| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.6834758.svg
         :target: https://doi.org/10.5281/zenodo.6834758

.. |pepy-downloads| image:: https://pepy.tech/badge/sierra-research
                    :target: https://pepy.tech/project/sierra-research

.. |supported-pythons| image:: https://img.shields.io/pypi/pyversions/sierra-research.svg
                       :target: https://pypi.python.org/pypi/sierra-research/

.. |os-supported| image:: https://img.shields.io/badge/os-linux%20%7C%20macOS-blue

.. |ci-coverage-master| image:: https://coveralls.io/repos/github/jharwell/sierra/badge.svg?branch=master
                        :target: https://coveralls.io/github/jharwell/sierra?branch=master

.. |ci-analysis-devel| image:: https://github.com/jharwell/sierra/actions/workflows/analysis-top.yml/badge.svg?branch=devel
                       :target: https://github.com/jharwell/sierra/actions/workflows/analysis-top.yml

.. |ci-coverage-devel| image:: https://coveralls.io/repos/github/jharwell/sierra/badge.svg?branch=devel
                       :target: https://coveralls.io/github/jharwell/sierra?branch=devel

.. |license| image:: https://img.shields.io/github/license/jharwell/sierra
   :alt: GitHub License
   :target: https://github.com/jharwell/sierra/blob/master/LICENSE

.. |maintenance| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg
                 :target: https://github.com/jharwell/sierra/graphs/commit-activity

.. image:: docs/_static/logo-banner.png
   :width: 400px

+---------------+--------------------------------------------------------------------+
| Usage         | |pypi-version| |pepy-downloads| |supported-pythons| |os-supported| |
+---------------+--------------------------------------------------------------------+
| Release       | |ci-analysis-master| |ci-coverage-master|                          |
+---------------+--------------------------------------------------------------------+
| Development   | |ci-analysis-devel| |ci-coverage-devel|                            |
+---------------+--------------------------------------------------------------------+
| Miscellaneous | |license| |doi| |docs| |maintenance|                               |
+---------------+--------------------------------------------------------------------+


**SIERRA is a command-line tool that turns a one-line description of an
experiment into fully executed, reproducible results — inputs, runs, and
finished plots.** It automates the parts of R&D experiments that are usually
manual engineering: generating configurations, running them across
simulators/processing pipelines, processing outputs, and producing analysis
artifacts.

Instead of writing (and re-writing) glue scripts for every project:

.. code-block:: text

   "I need one script to run the experiment, another to process the data,
   and a third to generate the graphs I want."

you describe the *what*, and SIERRA does the rest:

.. code-block:: text

   "Here is the simulator/processing pipeline I want to run, the final
   deliverables I want to generate, and the data I want on them — GO."

Think of it as a **backend compiler for research**: a description of what you
want in, a fully executed experiment with processed results out.

.. code-block:: shell

   pip3 install sierra-research

`Read the docs <https://sierra.readthedocs.io/en/master/>`_ ·
`Quick Start`_ · `Why SIERRA?`_ · `Limitations`_ · `Citing`_

----

Quick Start
===========

**Install:**

.. code-block:: shell

   pip3 install sierra-research

**Run your first sweep.** This runs a small parameter sweep locally using the
built-in `sample project`_:

.. code-block:: shell

   sierra \
     --sierra-root=$HOME/exp \
     --project=sierra_sample_project \
     --platform=platform.argos \
     --exec-env=hpc.local \
     --template-input-file=exp/argos/template.argos \
     --scenario=LowBlockCount.10x10x1 \
     --batch-criteria population_size.Log8 \
     --n-runs=2 \
     --pipeline 1 2 3 4

This generates all experiment inputs, runs them locally, and processes the
results into graphs under ``$HOME/exp``. See the `getting started guide`_ for a
full walkthrough, including the expected output.


What is SIERRA?
===============

SIERRA (**reSearch pIpEline for Reproducibility, Reusability, and
Automation**) is a command-line tool and plugin framework that automates the
full experimental workflow — generating experiment inputs, executing
experiments across heterogeneous computing environments, processing results,
and producing analysis artifacts such as plots, videos, and comparative
summaries.

It organizes every experiment into a fixed, five-stage pipeline:

1. **Input generation** --- Create experiment configurations from templates
2. **Execution** --- Run experiments locally, on clusters, etc.
3. **Postprocessing** --- Parse raw outputs into structured datasets
4. **Product generation** --- Generate plots, summaries, and derived artifacts
5. **Product comparison** --- Combine/overlay generated plots and other
   artifacts

.. figure:: https://raw.githubusercontent.com/jharwell/sierra/master/docs/figures/architecture.png

   The SIERRA pipeline, stage 1 through stage 4 (left to right). Each stage is
   extensible via plugins.

SIERRA is built around three design goals:

- **Reproducibility** — every result is fully described by its path on disk,
  which encodes the project, controller, scenario, and batch criteria used to
  produce it. Re-running the same invocation always produces the same layout.

- **Automation** — experiment generation, execution, post-processing, and
  product generation are handled by the pipeline; no scripting required.

- **Reusability** — the plugin architecture means a project written for one
  simulator or execution environment requires minimal changes to run on another.


Features at a Glance
====================

All categories below are extensible via plugins.

+-------------------------------+------------------------------------------------------+
| Feature                       | Details                                              |
+===============================+======================================================+
| Supported simulators          | ARGoS, ROS1+Gazebo, ROS1+Robot                       |
+-------------------------------+------------------------------------------------------+
| Execution environments        | Local machine, HPC clusters (SLURM, PBS), AWS Batch, |
|                               | Prefect server                                       |
+-------------------------------+------------------------------------------------------+
| Parameter sweeps              | Numeric, categorical, or mixed combinations          |
+-------------------------------+------------------------------------------------------+
| Output formats                | CSV, Arrow, GraphML, graphs (PNG, HTML), video (mp4) |
+-------------------------------+------------------------------------------------------+
| Model framework               | Overlay analytical models on empirical results       |
+-------------------------------+------------------------------------------------------+
| Reproducibility               | Fully archived, citable experiment configurations    |
+-------------------------------+------------------------------------------------------+
| Python version                | 3.9+                                                 |
+-------------------------------+------------------------------------------------------+


Why SIERRA?
===========

SIERRA changes the paradigm of running experiments from manual and procedural
to **declarative and automated**. You describe the environment, the
deliverables, and the data you want — SIERRA turns that description into a
fully executed experiment with processed results.

**Key advantages:**

- **Deep parameter sweep support** — numeric, categorical, or any combination
  thereof, with no boilerplate. A sweep that would require ~200 lines of
  brittle, non-reusable bash takes one SIERRA invocation.

- **Broad platform coverage** — mix and match simulators (ARGoS, ROS1+Gazebo),
  execution environments (local, SLURM, PBS), and output formats with little to
  no code changes between them.

- **Maximum reusability** — designed so that no copy-pasting is ever needed
  across projects or platforms.

- **Rich model framework** — run analytical models, generate synthetic data,
  and overlay it on empirical results automatically on the same figure.

- **Research-domain focus** — built for the scientific workflow, with native
  concepts for experiments, runs, batch criteria, and replication.

**Why SIERRA over Prefect, Dagster, or Airflow?**

General-purpose workflow tools like `Prefect <https://www.prefect.io>`_,
`Dagster <https://www.dagster.io>`_, and `Airflow <https://airflow.apache.org>`_
require you to build your own research pipeline from scratch. SIERRA provides a
battle-tested pipeline with first-class support for the patterns that matter
most in R&D: parameter sweeps, simulator integration, reproducible archiving,
and model-vs-empirical comparison.

The trade-off: SIERRA is more opinionated and less feature-complete than those
frameworks for general data engineering workloads. For most research use cases,
that gap doesn't matter.

Limitations
===========

SIERRA is purpose-built for the scientific experiment workflow. It is not the
right tool if:

- You need a **general-purpose DAG runner** for arbitrary data engineering
  tasks — use Prefect, Dagster, or Airflow instead.
- Your experiments are highly irregular and cannot be expressed as systematic
  variations on a template.
- You need **ROS2** --- ROS1 is supported; ROS2 support is planned.

If you are unsure whether SIERRA fits your use case, check the `use cases`_ page
or open a `discussion thread <https://github.com/jharwell/sierra/discussions>`_.

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

To cite a specific version of SIERRA (recommended for reproducibility), use the
DOI: |doi|


Troubleshooting
===============

If you encounter problems using SIERRA, please `open an issue
<https://github.com/jharwell/sierra/issues>`_ or post in the `GitHub
Discussions <https://github.com/jharwell/sierra/discussions>`_ forum. Please
include your SIERRA version, OS, and a minimal reproducible example where
possible.


Contributing
============

Contributions of all sizes are welcome — bug fixes, documentation improvements,
new plugins, or larger features.

A good first contribution is adding a storage plugin or a simple processor
plugin — both are typically under 100 lines and have clear contracts defined in
the `plugin developer guide`_.

If you have an idea to discuss before diving in, open a discussion thread at any
point. See the `contributing guide`_ for the full procedure.


.. _`getting started guide`: https://sierra.readthedocs.io/en/master/src/getting-started/trial.html
.. _`pipeline documentation`: https://sierra.readthedocs.io/en/master/src/concepts/pipeline.html
.. _`environment variables`: https://sierra.readthedocs.io/en/master/src/reference/environment.html
.. _`use cases`: https://sierra.readthedocs.io/en/master/src/getting-started/why-sierra.html
.. _`plugin developer guide`: https://sierra.readthedocs.io/en/master/src/tutorials/plugins/devguide.html
.. _`contributing guide`: https://sierra.readthedocs.io/en/master/src/reference/contributing.html
.. _`sample project`: https://github.com/jharwell/sierra-sample-project.git

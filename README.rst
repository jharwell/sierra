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

.. |license| image:: https://img.shields.io/badge/License-MIT-blue.svg

.. |doi| image:: https://zenodo.org/badge/125774567.svg
         :target: https://zenodo.org/badge/latestdoi/125774567

.. |docs| image:: https://readthedocs.org/projects/sierra/badge/?version=master
          :target: https://sierra.readthedocs.io/en/master/

.. |maintenance| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg


+---------------+--------------------------------------------------------------------+
| Usage         | |pepy-downloads| |pypi-version| |supported-pythons| |os-supported| |
+---------------+--------------------------------------------------------------------+
| Release       | |ci-analysis-master| |ci-coverage-master|                          |
+---------------+--------------------------------------------------------------------+
| Development   | |ci-analysis-devel| |ci-coverage-devel|                            |
+---------------+--------------------------------------------------------------------+
| Miscellaneous |    |license| |doi| |docs| |maintenance|                            |
+---------------+--------------------------------------------------------------------+


TL;DR
=====

What is SIERRA? See `What is SIERRA?`_

Why should you use SIERRA? See `Why SIERRA?`_

To install SIERRA (requires python 3.9+):

::

   pip3 install sierra-research


SIERRA requires a recent OSX (tested with 13+) or Linux (tested with ubuntu
20.04+) and python >= 3.9. For more details, including the requirements for
project code, see the `SIERRA requirements
<https://sierra.readthedocs.io/en/master/src/requirements.html>`_.

To get started using SIERRA, see `getting started
<https://sierra.readthedocs.io/en/master/src/getting_started.html>`_.

Want to cite SIERRA? See `Citing`_.

Have an issue using SIERRA? See `Troubleshooting`_.

What is SIERRA?
===============

.. figure:: https://raw.githubusercontent.com/jharwell/sierra/master/docs/figures/architecture.png

   SIERRA architecture, organized by pipeline stage, left to right. High-level
   inputs/outputs and active plugins and shown for each stage. “...”  indicates
   areas of further extensibility and customization via new plugins. “Host
   machine” indicates the machine SIERRA was invoked on. The active plugins in
   each stage and what they cumulatively enable are highlighted in red.

SIERRA is a command line tool and plugin framework for:

- Automating R&D, providing faculties for seamless experiment
  generation, execution, and results processing.

- Accelerating R&D cycles by allowing researchers/developers to focus on the
  “science” aspects: developing new things and designing experiments to test
  them, rather than the engineering aspects (writing scripts, configuring
  environments, etc.).

- Improving the reproducibility of scientific research, particularly in AI.

Why SIERRA?
===========

- It changes the paradigm of the engineering tasks researchers must perform
  from manual and procedural to declarative and automated. That is, from::

    "I need to perform these steps to run the experiment, process the data and
    generate the graphs I want."

  to::

    "Here is the environment and simulator/platforms(s) I want to use, the
    deliverables I want to generate, and the data I want to appear on them for
    my research query--GO!"

  Essentially, SIERRA handles the “engineering” parts of research on the
  backend, acting as a compiler of sorts, turning research queries into
  executable objects, running the "compiled" experiments, and processing results
  into visualizations or other deliverables.

- It has deep support for arbitrary parameter sweeps: numeric, categorical, or
  any combination thereof.

- It supports a wide range of execution engines/environments, and experiment
  input/output formats via plugins. SIERRA supports mix-and-match between all
  plugin types, subject to restrictions within the plugins themselves. This is
  and makes it very easy to run experiments on different hardware, targeting
  different simulators, generating different outputs, etc., all with little to
  no configuration changes by the user.

- SIERRA maximizes reusability of code and configuration; it is designed so that
  *no* copy-pasting is ever needed, improving code quality with no additional
  effort from users.

- SIERRA has a rich model framework allowing you to run arbitrary models,
  generate data, and plot it on the same figure as empirical
  results--automatically.

- Why use SIERRA over something like `prefect <https://www.prefect.io>`_,
  `dagster <https://www.dagster.io>`_, or `airflow
  <https://airflow.apache.org>`_ ? Briefly, because SIERRA provides a common
  pipeline which is tested and can accommodate most use cases; SIERRA is not as
  feature complete as these other frameworks, though. For most use cases (but
  not all), that delta doesn't matter. In addition, with the other frameworks,
  you have to create your own pipelines from scratch.

Not sure if SIERRA makes sense for you? Check out some of the `use cases
<https://sierra.readthedocs.io/en/master/src/use-cases.html>`_ for which SIERRA
was designed.  If aspects of any sound familiar, then there is a strong chance
SIERRA could help you! See the `SIERRA docs
<https://sierra.readthedocs.io/en/master/>`_ to get started.

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
you have an idea, I'm happy to talk about it at any point :-). See the
`contributing guide
<https://sierra.readthedocs.io/en/master/src/contributing.html>`_ for the
general procedure.

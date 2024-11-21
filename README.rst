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

- Automating R&D, providing faculties for seamless experiment
  generation, execution, and results processing.

- Accelerating R&D cycles by allowing researchers/developers to focus on the
  “science” aspects: developing new things and designing experiments to test
  them.

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
  of a specific project.

Not sure if SIERRA makes sense for your research? Check out some of the
`use cases<https://sierra.readthedocs.io/en/master/src/use-cases.html>`_ for
which SIERRA was designed.

If aspects of any sound familiar, then there is a strong chance SIERRA could
help you! SIERRA is well documented--see the `SIERRA docs
<https://sierra.readthedocs.io/en/master/>`_ to get started.


SIERRA Support Matrix
=====================

SIERRA supports multiple `platforms
<https://sierra.readthedocs.io/en/master/src/platform/index.html>`_ which you
can write code to target. In SIERRA terminology, a platform is a "thing"
(usually a simulator or real hardware) that you want to write to code to run
on. Note that platform != OS, in SIERRA terminology. If a SIERRA platform runs
on a given OS, then SIERRA supports doing so; if it does not, then SIERRA does
not. For example, SIERRA does not support running ARGoS on windows, because
ARGoS does not support windows.

SIERRA supports multiple execution environments for execution of experiments,
such as `High Performance Computing (HPC) environments
<https://sierra.readthedocs.io/en/master/src/exec_env/hpc.html>`_ and `real
robots <https://sierra.readthedocs.io/en/master/src/exec_env/robots.html>`_.

SIERRA also supports multiple formats for experimental inputs and outputs.

The set of built-in plugins which come with SIERRA are below. If your desired
platform/execution environment/etc is not listed, see the `plugin tutorials
<https://sierra.readthedocs.io/en/master/src/tutorials.html>`_ for how to add
it via a new plugin. SIERRA supports full mix-and-match between plugins from the
table above--this is one of the most powerful features of SIERRA!

While SIERRA itself supports arbitrary sets of plugins, there are necessarily
restrictions on which plugins can be used together. For example, if you are
using a platform mapping to a custom in-house simulator which takes JSON as
input, you can't use the XML plugin for experimental inputs. For more details on
which sets of plugins are valid which built-in platforms, see the
`support matrix <https://sierra.readthedocs.io/en/master/src/matrix.html>`_.

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

For more details, including the requirements for project code, see the `SIERRA
requirements <https://sierra.readthedocs.io/en/master/src/requirements.html>`_.

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

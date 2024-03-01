.. _ln-sierra-packages:

=============================
SIERRA Installation Reference
=============================

.. _ln-sierra-packages-pypi:

SIERRA PyPi Package
===================


The SIERRA PyPi package provides the following executables:

- ``sierra-cli`` - The command line interface to SIERRA.

The SIERRA PyPi package provides the following man pages, which can be viewed
via ``man <name>``. Man pages are meant as a `reference`, and though I've tried
to make them as full featured as possible, there are some aspects of SIERRA
which are only documented on the online docs (e.g., the tutorials). Available
manpages are:

- ``sierra-cli`` - The SIERRA command line interface.

- ``sierra-usage`` - How to use SIERRA (everything BUT the command line
  interface).

- ``sierra-platforms`` - The target platforms that SIERRA currently
  supports (e.g., ARGoS).

- ``sierra-examples`` - Examples of SIERRA usage via
  command line invocations demonstrating various features.

- ``sierra-glossary`` - Glossary of SIERRA terminology to make things
  easier to understand.

- ``sierra-exec-envs`` - The execution environments that SIERRA currently
  supports (e.g., SLURM).

Installing SIERRA
-----------------

::

   pip3 install sierra-research

.. _ln-sierra-packages-rosbridge:

SIERRA ROSBridge
================

SIERRA provides a :term:`ROS1` package containing functionality it uses to
manage simulations and provide run-time support to :term:`projects<Project>`
using a :term:`Platform` built on ROS. To use SIERRA with a ROS platform, you
need to setup the SIERRA ROSbridge package here (details in README):
`<https://github.com/jharwell/sierra_rosbridge>`_.

This package provides the following nodes:

- ``sierra_timekeeper`` - Tracks time on an :term:`Experimental Run`, and
  terminates once the amount of time specified in ``--exp-setup`` has
  elapsed. Necessary because ROS does not provide a way to say "Run for this
  long and then terminate". An XML tag including this node is inserted by SIERRA
  into each ``.launch`` file.

.. _ln-packages:

===============
SIERRA Packages
===============

.. _ln-packages-pypi:

SIERRA PyPi Package
===================

SIERRA can be built locally into a PyPi package which you can install to provide
fully access to its functionality outside of the SIERRA repo (generally
necessary for development with SIERRA :term:`projects<Project>`), and without
modifying your :envvar:`PYTHONPATH`. Eventually, it will be deployed to PyPi,
and local installations will be unnecessary except for development of SIERRA
itself.

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

Installing SIERRA PyPi locally
------------------------------

To install SIERRA locally do the following from the SIERRA repo:

#. Build SIERRA documentation (needed for package manpages)::

     pip3 install -r docs/requirements.txt
     cd docs && make man && cd ..

#. Install SIERRA::

     pip3 install .

.. _ln-packages-rosbridge:

SIERRA ROSBridge
----------------

SIERRA provides a :term:`ROS` package containing functionality it uses to manage
simulations and provide run-time support to :term:`projects<Project>` using a
:term:`Platform` built on ROS. To use SIERRA with a ROS platform, you need to
setup the SIERRA ROSbridge package here (details in README):
`<https://github.com/swarm-robotics/sierra_rosbridge.git>`_.

This package provides the following nodes:

- ``sierra_timekeeper`` - Tracks time on an :term:`Experimental Run`, and
  terminates once the amount of time specified in ``--exp-setup`` has
  elapsed. Necessary because ROS does not provide a way to say "Run for this
  long and then terminate". An XML tag including this node is inserted by SIERRA
  into each ``.launch`` file.

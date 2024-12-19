.. _usage/cli:

======================
Command Line Interface
======================

Unless an option says otherwise, it is applicable to all batch criteria. That
is, option batch criteria applicability is only documented for options which
apply to a subset of the available :term:`Batch Criteria`.

If an option is given more than once, the last such occurrence is used.

To help shorten cmdlines, SIERRA supports the usual rcfile mechanism via
``--rcfile`` / :envvar:`SIERRA_RCFILE`.

SIERRA Core
===========

.. include:: cli-core.rst

:term:`ARGoS` Platform
======================

.. include:: cli-argos.rst

:term:`ROS1+Gazebo` Platform
============================

.. include:: cli-ros1gazebo.rst

:term:`ROS1+Robot` Platform
===========================

.. include:: cli-ros1robot.rst

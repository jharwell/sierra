.. _usage/cli:

======================
Command Line Interface
======================

Unless an option says otherwise, it is applicable to all batch criteria. That
is, option batch criteria applicability is only documented for options which
apply to a subset of the available :term:`Batch Criteria`.

If an option is given more than once, the last such occurrence is used.

.. TIP:: To help shorten cmdlines, SIERRA supports the usual rcfile mechanism
         via ``--rcfile`` / :envvar:`SIERRA_RCFILE`.

SIERRA Core
===========

.. include:: cli-core.rst

:term:`ARGoS` Engine
======================

.. include:: cli-engine-argos.rst

:term:`ROS1+Gazebo` Engine
============================

.. include:: cli-engine-ros1gazebo.rst

:term:`ROS1+Robot` Engine
===========================

.. include:: cli-engine-ros1robot.rst

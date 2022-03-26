.. _ln-platform-plugins-rosgazebo:

===================
ROS+Gazebo Platform
===================

This platform can be selected via ``--platform=platform.rosgazebo``.

This is the platform on which SIERRA will run experiments using the
:term:`Gazebo` simulator and :term:`ROS` (either ROS1 OR ROS2). It cannot be
used to run experiments on real robots. To use this platform, you must setup the
:ref:`SIERRA ROSBridge <ln-packages-rosbridge>`.


.. toctree::

   batch_criteria.rst

Random Seeding For Reproducibility
==================================

ROS+Gazebo do not provide a random number generator manager, but SIERRA provides
random seeds to each :term:`Experimental Run` which :term:`Project` code should
use to manage random number generation, if needed, to maximize
reproducability. See :ref:`ln-tutorials-project-template-input-file` and
:ref:`ln-req-exp` for details on the format of the provided seed. By default
SIERRA does not overwrite its generated random seeds for each experiment once
generated; you can override with ``--no-preserve-seeds``.

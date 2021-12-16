.. _ln-platform-plugins:

===================
Supported Platforms
===================

SIERRA supports a number of :term:`platforms <Platform>`, all of which can be
used transparently for running experiments (well transparent from SIERRA's point
of view; you probably will still have to make code modifications to switch
between platforms).

- :ref:`ARGoS <ln-platform-plugins-argos>`
- :ref:`ROS-Gazebo <ln-platform-plugins-ros-gazebo>`

.. _ln-platform-plugins-argos:

ARGoS Platform
==============

This platform can be selected via ``--platform=platform.argos``.

This is the default platform on which SIERRA will run experiments, and using the
:term:`ARGoS` simulator. It cannot be used to run experiments on real robots.


.. toctree::
   :maxdepth: 2
   :caption: ARGoS-specific Configuration for SIERRA

   argos/batch_criteria.rst

Random Seeding For Reproducibility
----------------------------------

ARGoS provides its own random seed mechanism under ``<experiment>`` which SIERRA
uses to seed each experiment. :term:`Project` code should use this mechanism or
a similar random seed generator manager seeded by the same value so that
experiments can be reproduced exactly. By default SIERRA does not overwrite its
generated random seeds for each experiment once generated; this can be override
with ``--no-preserve-seeds``. See
:ref:`ln-tutorials-project-template-input-file` and :ref:`ln-req-exp` for
details on the format of the provided seed.

.. _ln-platform-plugins-ros-gazebo:

ROS+Gazebo Platform
===================

This platform can be selected via ``--platform=platform.rosgazebo``.

This is the platform on which SIERRA will run experiments using the
:term:`Gazebo` simulator and :term:`ROS` (either ROS1 OR ROS2). It cannot be
used to run experiments on real robots. To use this platform, you must setup the
:ref:`SIERRA RosBridge <ln-packages-rosbridge>`.


.. toctree::
   :maxdepth: 2
   :caption: ROS+Gazebo-specific Configuration for SIERRA

   rosgazebo/batch_criteria.rst


Random Seeding For Reproducibility
----------------------------------

ROS+Gazebo do not provide a random number generator manager, but SIERRA provides
random seeds to each :term:`Experimental Run` which :term:`Project` code should
use to manage random number generation, if needed, to maximize
reproducability. See :ref:`ln-tutorials-project-template-input-file` and
:ref:`ln-req-exp` for details on the format of the provided seed. By default
SIERRA does not overwrite its generated random seeds for each experiment once
generated; this can be override with ``--no-preserve-seeds``.

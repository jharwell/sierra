.. _ln-platform-plugins-rosrobot:

==================
ROS+Robot Platform
==================

This platform can be selected via ``--platform=platform.rosrobot``.

This is the platform on which SIERRA will run experiments using :term:`ROS`
(either ROS1 OR ROS2) on a real robot of your choice. To use this platform, you
must setup the :ref:`SIERRA ROSBridge <ln-packages-rosbridge>`.

Random Seeding For Reproducibility
==================================

ROS do not provide a random number generator manager, but SIERRA provides random
seeds to each :term:`Experimental Run` which :term:`Project` code should use to
manage random number generation, if needed, to maximize reproducability. See
:ref:`ln-tutorials-project-template-input-file` and :ref:`ln-req-exp` for
details on the format of the provided seed. By default SIERRA does not overwrite
its generated random seeds for each experiment once generated; you can override
with ``--no-preserve-seeds``.

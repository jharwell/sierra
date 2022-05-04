==================
SIERRA Subprograms
==================

These are the shell programs which SIERRA `may` use internally when running,
depending on what you are doing.

- :program:`parallel` - GNU parallel. Used during stage 2 when running
  experiments (:term:`ARGoS`, :term:`ROS+Gazebo`, :term:`ROS+Robot` platforms).

- :program:`ffmpeg` - Used during stage 3 if imagizing is run. See
  :ref:`ln-usage-vc-platform`.

- :program:`Xvfb` - Used during stage 1 when generating simulation inputs, and
  during stage 2 when running experiments for the :term:`ARGoS`
  :term:`Platform`. See also :ref:`ln-usage-vc-platform`.

- :program:`parallel-ssh` - Used during stage 1 when generating experiments
  experiments (:term:`ROS+Robot` platform).

- :program:`parallel-rsync` - Used during stage 1 when generating experiments
  experiments (:term:`ROS+Robot` platform).

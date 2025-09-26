==================
SIERRA Subprograms
==================

These are the shell programs which SIERRA `may` use internally when running,
depending on what you are doing.

- :program:`parallel` - GNU parallel. Used during stage 2 when running
  experiments (:term:`ARGoS`, :term:`ROS1+Gazebo`, :term:`ROS1+Robot` engines).

- :program:`ffmpeg` - Used during stage 3 if imagizing is run. See
  :ref:`plugins/prod/render`.

- :program:`Xvfb` - Used during stage 1 when generating simulation inputs, and
  during stage 2 when running experiments for the :term:`ARGoS`
  :term:`Engine`. See also :ref:`plugins/prod/render`.

- :program:`parallel-ssh` - Used during stage 1 when generating experiments
  experiments (:term:`ROS1+Robot` engine).

- :program:`parallel-rsync` - Used during stage 1 when generating experiments
  experiments (:term:`ROS1+Robot` engine).

- :program:`killall` - Used during stage 2 when running :term:
  :term:`ARGoS`, :term:`ROS1+Gazebo` experiments to cleanup after each
  experimental run.

.. _usage/env-vars:

=====================
Environment Variables
=====================

Core
====


.. envvar:: SIERRA_PLUGIN_PATH

   Used for locating :term:`plugins <Plugin>`. Each directory is searched
   recursively for plugins matching one of the schemas SIERRA supports.  You
   should not put directories which you put on here also on :envvar:`PYTHONPATH`
   because (a) SIERRA modifies ``PYTHONPATH`` internally in specific ways to
   support dynamic searching/loading of plugins, and the interaction between
   ``PYTHONPATH`` and ``sys.path`` can have subtle consequences across python
   versions and systems, and (b) SIERRA uses this path for other things
   internally (e.g., computing the paths to YAML config files).

   This variable is used in stages 1-5. See :ref:`plugins/external` for more
   information.

.. envvar:: SIERRA_RCFILE

   Used to specify the path to a file to put cmdline args in to reduce the size
   of cmdlines. Can also be passed directly via ``--rcfile``. Priority:

   - ``--rcfile``

   - ``SIERRA_RCFILE``

   - ``~/.sierrarc``

   .. NOTE:: You can't pass shortform cmdline arguments in the rcfile, or
             arguments which are marked as required in their cmdline definition.

   .. versionadded:: 1.3.18

.. envvar:: PYTHONPATH

   Used for locating projects per the usual python mechanisms.

.. envvar:: SIERRA_ARCH

   Can be used to determine the names of executables launch in HPC environment,
   so that in environments with multiple queues/sub-clusters with different
   architectures simulators can be compiled natively for each for maximum
   performance. Can be any string. If defined, then instead of searching for the
   ``foobar`` executable for some engine on ``PATH``, SIERRA will look for
   ``foobar-$SIERRA_ARCH``.

   .. IMPORTANT:: Not all engines use this variable--see the docs for your
                  engine of interest.

.. envvar:: SIERRA_NODEFILE

   Points to a file suitable for passing to :program:`parallel` via
   ``--sshloginfile``. See :program:`parallel` docs for general
   content/formatting requirements.

   Used by SIERRA to configure experiments during stage 1,2; if it is not
   defined and ``--nodefile`` is not passed SIERRA will throw an error.


Plugins
=======

.. envvar:: ARGOS_PLUGIN_PATH

   Must be set to contain the library directory where you installed/built ARGoS,
   as well as the library directory for your project ``.so``. Checked to be
   non-empty before running stage 2 for all ``--execenv`` plugins. SIERRA does
   `not` modify this variable, so it needs to be setup properly prior to
   invoking SIERRA (i.e., the directory containing the :term:`Project` ``.so``
   file needs to be on it). SIERRA can't know, in general, where the location of
   the C++ code corresponding to the loaded :term:`Project` is.

.. envvar:: LD_LIBRARY_PATH

   Must be set to contain library directories for dynamically loaded libraries
   installed to nonstandard and/or non system locations.

.. envvar:: PARALLEL

   When running on some execution environments, such as ``hpc.slurm,hpc.pbs``,
   any and all environment variables needed by your :term:`Project` should be
   exported via the ``PARALLEL`` environment variable before invoking SIERRA,
   because GNU parallel does not export the environment of the node it is
   launched from to slave nodes (or even on the local machine). Something like::

     export PARALLEL="--workdir . \
     --env PATH \
     --env LD_LIBRARY_PATH \
     --env LOADEDMODULES \
     --env _LMFILES_ \
     --env MODULE_VERSION \
     --env MODULEPATH \
     --env MODULEVERSION_STACK
     --env MODULESHOME \
     --env OMP_DYNAMICS \
     --env OMP_MAX_ACTIVE_LEVELS \
     --env OMP_NESTED \
     --env OMP_NUM_THREADS \
     --env OMP_SCHEDULE \
     --env OMP_STACKSIZE \
     --env OMP_THREAD_LIMIT \
     --env OMP_WAIT_POLICY \
     --env SIERRA_ARCH \
     --env SIERRA_PLUGIN_PATH"

   Don't forget to include :envvar:`ARGOS_PLUGIN_PATH`,
   :envvar:`ROS_PACKAGE_PATH`, etc., depending on your chosen :term:`Engine`.

.. envvar:: PARALLEL_SHELL

   SIERRA sets up the :term:`Experiment` execution environments by running one
   or more shell commands in a subprocess (treated as a ``shell``, which means
   that :program:`parallel` can't determine ``SHELL``, and therefore defaults to
   ``/bin/sh``, which is not what users expect. SIERRA explicitly sets
   ``PARALLEL_SHELL`` to the result of ``shutil.which('bash')`` in keeping with
   the Principle Of Least Surprise.

.. envvar:: ROS_PACKAGE_PATH

   The list of directories which defines where ROS will search for
   packages. SIERRA does `not` modify this variable, so it needs to be setup
   properly prior to invoking SIERRA (i.e., sourcing the proper ``setup.bash``
   script).

.. envvar:: ROS_IP

   The IP address of a ROS node. Usually this is computed automatically for you;
   if things aren't working correctly you may have to explicitly assign this
   based on whatever the system ROS is running on says is IP address is.


.. envvar:: ROS_HOSTNAME

   The resolvable hostname for a ROS node. Unless you have DNS configured within
   the network that things are running on, best not to rely on this (at least
   for real robots).

.. envvar:: ROS_DISTRO

   The active ROS distribution (versioned set of ROS packages).

.. envvar:: ROS_VERSION

            The version of ROS. Currently SIERRA only supports ROS1.

.. envvar:: PBS_NUM_PPN

            # CPUs/node on a compute node allocated to a job on a HPC cluster
            managed by the PBS scheduler.

.. envvar:: PBS_NODEFILE

            Newline delimited list of compute nodes allocated to the current job
            on an HPC cluster managed by the PBS scheduler.

.. envvar:: PBS_JOBID

            Globally unique ID for a job on a HPC cluster managed by the PBS
            scheduler. Useful for creating unique output files/logging paths.

.. envvar:: SLURM_CPUS_PER_TASK

            # CPUs/node on a compute node allocated to a job on a HPC cluster
            managed by the SLURM scheduler.

.. envvar:: SLURM_TASKS_PER_NODE

            # tasks requested/allocated per compute node on a job on a HPC
            cluster managed by the SLURM scheduler.

.. envvar:: SLURM_JOB_NODELIST

            Newline delimited list of compute nodes allocated to the current job
            on an HPC cluster managed by the SLURM scheduler.

.. envvar:: SLURM_JOB_ID

            Globally unique ID for a job on a HPC cluster managed by the SLURM
            scheduler. Useful for creating unique output files/logging paths.

.. envvar:: PREFECT_API_URL

            The URL of the :term:`Prefect` server to use. Used by prefect-based
            execution environment plugins.

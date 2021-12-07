.. _ln-usage-env-vars:

*********************
Environment Variables
*********************

.. envvar:: SIERRA_PLUGIN_PATH

   Used for locating :term:`plugins <Plugin>`. The directory `containing` a
   plugin directory outside the SIERRA source tree must be on
   ``SIERRA_PLUGIN_PATH``. Paths are added to ``PYTHONPATH`` as needed to load
   plugins correctly. For example, if you have a different version of the
   ``--storage-medium`` plugin you'd like to use, and you have but the directory
   containing the plugin in ``/home/user/plugins``, then you need to add
   ``/home/user/plugins`` to your ``SIERRA_PLUGIN_PATH`` to so that SIERRA will
   find it. This variable is used in stages 1-5.

   Used for locating :term:`projects <Project>`; all projects specifiable with
   ``--project`` are directories found within the directories on this path. For
   example, if you have a project ``/home/$USER/git/projects/myproject``, then
   ``/home/$USER/git`` must be on ``SIERRA_PLUGIN_PATH`` in order for you to be
   able to specify ``--project=myproject``. This variable is used in stages 1-5.

   You *cannot* just put the parent directory of your project on
   :envvar:`PYTHONPATH` because SIERRA uses this path for other things
   internally (e.g., computing the paths to YAML config files).

.. envvar:: PYTHONPATH

   Used for locating projects per the usual python mechanisms.

.. envvar:: ARGOS_PLUGIN_PATH

   Must be set to contain the library directory where you installed/built ARGoS,
   as well as the library directory for your project ``.so``. Checked to be
   non-empty before running stage 2 for all ``--exec-env`` plugins. SIERRA does
   `not` modify this variable, so it needs to be setup properly prior to
   invoking SIERRA (i.e., the directory containing the :term:`Project` ``.so``
   file needs to be on it). SIERRA can't know, in general, where the location of
   the C++ code corresponding to the loaded :term:`Project` is.

.. envvar:: SIERRA_ARCH

   Used to determine the names of ARGoS executables via ``argos3-$SIERRA_ARCH``,
   so that in HPC environments with multiple queues/sub-clusters with different
   architectures ARGoS can be compiled natively for each for maximum
   performance.  Can be any string. Used when generating ARGoS cmds in stage 1,
   and only if SIERRA is run on a cluster.

.. envvar:: SIERRA_ADHOC_NODEFILE

   Points to a file suitable for passing to :program:`parallel` via
   ``--sshloginfile``. See :program:`parallel` docs for content/formatting
   requirements.

   Used by SIERRA to configure experiments during stage 1,2; if it is not
   defined and ``--exec-env=hpc.adhoc`` is set SIERRA will throw an error.

.. envvar:: PARALLEL

   Any and all environment variables needed by your :term:`Project` must be
   exported via the ``PARALLEL`` environment variable before invoking SIERRA,
   because GNU parallel does not export the environment of the node it is
   launched from to slave nodes (or even on the local machine). Something like::

     export PARALLEL="--workdir . --env PATH --env LD_LIBRARY_PATH --env
     LOADEDMODULES --env _LMFILES_ --env MODULE_VERSION --env MODULEPATH --env
     MODULEVERSION_STACK --env MODULESHOME --env OMP_DYNAMICS --env
     OMP_MAX_ACTIVE_LEVELS --env OMP_NESTED --env OMP_NUM_THREADS --env
     OMP_SCHEDULE --env OMP_STACKSIZE --env OMP_THREAD_LIMIT --env OMP_WAIT_POLICY
     --env SIERRA_ARCH --env SIERRA_PLUGIN_PATH"

   Should be a good starting point. Only used if SIERRA is run on a cluster with
   ``exec_env=hpc.slurm|hpc.pbs``. Don't forget to include
   :envvar:`ARGOS_PLUGIN_PATH`, :envvar:`ROS_PACKAGE_PATH`, etc., depending on
   your chosen :term:`Platform`.

.. envvar:: ROS_PACKAGE_PATH

   The list of directories which defines where ROS will search for
   packages. SIERRA does `not` modify this variable, so it needs to be setup
   properly prior to invoking SIERRA (i.e., sourcing the proper ``setup.bash``
   script).

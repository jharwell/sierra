.. _ln-hpc-cluster-setup:

HPC Cluster Setup
=================

This setup applies to the following SIERRA HPC cluster environments:

- PBS: :ref:`ln-hpc-plugin-pbs`
- SLURM: :ref:`ln-hpc-plugin-slurm`

The steps to properly configure the C++ libraries for ARGoS and your project for
use with SIERRA in one of the above environments are:

#. Build ARGoS natively on each different type of compute node SIERRA might be
   run on, for maximum efficiency with large swarms. For example, if your HPC
   cluster is 1/2 Intel chips and 1/2 AMD chips, you will want to compile ARGoS
   twice, natively on each chipset, and link the architecture-dependent ARGoS
   into your ``PATH`` via ``argos3-<arch>``, where ``<arch>`` is anything you
   like; ``SIERRA_ARCH`` will need to be set to ``<arch>`` before invocating
   SIERRA so that the correct ARGoS commands can be generated, depending on what
   the chipset is for the nodes you request for your HPC job.

#. Your project ``.so`` should be built natively on each different type of
   compute node SIERRA might be run on, just like ARGOS, for maximum efficiency
   with large swarms. Since the name of the ``.so`` is deduced from
   ``--project`` for SIERRA, you can use ``ARGOS_PLUGIN_PATH`` to specify where
   the library should be loaded from (e.g., using ``SIERRA_ARCH`` as the
   switch).

Once ARGoS/your C++ code has been built, you can setup SIERRA:

#. Install python dependencies with ``pip3``::

     pip3 install --user --upgrade pip
     pip3 install --user -r requirements/common.txt

#. Verify GNU parallel is installed; if it is not installed, ask your cluster
   admin to install it for you.

#. Clone plugin for whatever project you are going to use into
   ``projects``. SIERRA will (probably) refuse to do anything useful if there are
   no project installed. The repository should be cloned into a directory with
   the EXACT name you want it to be callable with on the cmdline via
   ``--project``.

In addition to the resource requests for the submitted jobs (see
:ref:`ln-hpc-plugins` for how SIERRA uses the results of the resource request to
configure experiments when invoked), the following additional requirements for
job scripts apply:

#. ``SIERRA_ARCH`` must be defined. It can be any string, as long as it can be
   used to select the correct version of ARGoS to invoke via
   ``argos3-$SIERRA_ARCH`` when generating ARGoS cmds in stage 1.

#. ``ARGOS_PLUGIN_PATH`` must be set to contain the library directory where
   you installed/built ARGoS, as well as the library directory for your project
   ``.so``.

#. Any and all environment variables needed by your project must be exported via
   the ``PARALLEL`` environment variable before invoking SIERRA, because GNU
   parallel does not export the environment of the node it is launched from to
   slave nodes. Something like::

     export PARALLEL="--workdir . --env PATH --env LD_LIBRARY_PATH --env
     LOADEDMODULES --env _LMFILES_ --env MODULE_VERSION --env MODULEPATH --env
     MODULEVERSION_STACK --env MODULESHOME --env OMP_DYNAMICS --env
     OMP_MAX_ACTIVE_LEVELS --env OMP_NESTED --env OMP_NUM_THREADS --env
     OMP_SCHEDULE --env OMP_STACKSIZE --env OMP_THREAD_LIMIT --env OMP_WAIT_POLICY
     --env ARGOS_PLUGIN_PATH --env SIERRA_ARCH"

   should be a good starting point.

#. Before invoking SIERRA, you must ``cd`` to the directory where it is cloned;
   this is a limitation which will be removed in the future once SIERRA is a
   pypi package.

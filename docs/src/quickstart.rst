=================
SIERRA Quickstart
=================

After developing the C++ code for your project, you need to link it with
SIERRA. To do that, you need to:

#. Setup the SIERRA :term:`Project` for your C++ code by following
   :ref:`ln-tutorials-project-project`.

#. Figure out which HPC environment SIERRA supports matches your available
   hardware: :ref:`ln-hpc-plugins`, and following the appropriate setup guide.

#. Decide what variable you are interested in investigating by consulting
   :ref:`ln-batch-criteria` (i.e., what variable(s) you want to change across
   some range and see how swarm behavior changes, or doesn't change).

#. Look at the :ref:`ln-usage-cli` to understand how to invoke SIERRA in
   general.

#. Look at the :ref:`ln-usage-examples` to get ideas on how to craft your own
   SIERRA invocation.

#. Determine how to invoke SIERRA. At a minimum you need to tell it the
   following:

   - What project to load: ``--project``. This must be live under a directory
     named ``projects`` which must be on :envvar:`SIERRA_PROJECT_PATH`. This is
     used to:

     - Compute the name of the library SIERRA will tell ARGoS to search for on
       :envvar:`ARGOS_PLUGIN_PATH` when looking for controller and loop function
       definitions. For example if you pass ``--project=foobar``, then SIERRA
       will tell ARGoS to search for ``libfoobar.so`` on
       :envvar:`ARGOS_PLUGIN_PATH`.

     - Figure out the directory to load graph and simulation processing
       configuration from.

   - What template input file to use: ``--template-input-file``.

   - How many copies of each simulation to run per experiment: ``--n-sims``.

   - Where it is running/how to run experiments: ``--hpc-env``.

   - How long simulations should be: ``--time-setup``.

   - What controller to run: ``--controller``.

   - How large the arena should be, what block distribution type to use (for
     example), etc. ``--scenario``. :term:`Project` dependent.

   - What you are investigating; that is, what variable are you interested in
     varying: ``--batch-criteria`` (you read :ref:`ln-batch-criteria`, right?).

   If you try to invoke SIERRA with an (obviously) incorrect combination of
   command line options, it will refuse to do anything. For less obviously
   incorrect combinations, it will (hopefully) stop when an assert fails before
   doing anything substantial.

   Full documentation of all command line options it accepts is in
   :ref:`ln-usage-cli`, and there are many useful options that SIERRA accepts,
   so skimming the CLI docs is **very** worthwhile.

#. Learn SIERRA's runtime :ref:`ln-runtime-exp-tree`. When running, SIERRA will
   create a (rather) large directory structure for you, so reading the docs is
   worthwhile to understand what the structure means, and to gain intuition into
   where to look for the inputs/outputs of different stages, etc., without having
   to search exhaustively through the filesystem.

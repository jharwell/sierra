=================
SIERRA Quickstart
=================

#. From the SIERRA repo root, install SIERRA locally by following
   :ref:`ln-package`.

#. Install OS packages (ubuntu package names shown):

   - ``parallel``
   - ``cm-super``
   - ``texlive-fonts-recommended``
   - ``texlive-latex-extra``

#. After developing the C++ code for your project (you've already done that
   right???), you may need to modify it so that it simulations can be launched
   and data from simulations captured in a way that SIERRA can process. See
   :ref:`ln-c++-lib-requirements` for requirements.

#. Setup the interface between your code and SIERRA by defining a SIERRA
   :term:`Project` in python by following
   :ref:`ln-tutorials-project-project`. If you don't want to spend the
   time doing this and just want to try out SIERRA with an existing
   :term:`Project`, see :ref:`ln-tutorials-trial` for the quick-quickstart.

#. Figure out which HPC environment SIERRA supports matches your available
   hardware: :ref:`ln-hpc-plugins`, and following the appropriate setup guide.

#. Decide what variable you are interested in investigating by consulting
   :ref:`ln-batch-criteria` (i.e., what variable(s) you want to change across
   some range and see how swarm behavior changes, or doesn't change).

#. Look at the :ref:`ln-usage-cli` to understand how to invoke SIERRA in
   general.

#. Look at the :ref:`ln-usage-examples` to get ideas on how to craft your own
   SIERRA invocation. If you get stuck, look at :ref:`ln-faq` for answers to
   common questions.

#. Determine how to invoke SIERRA. At a minimum you need to tell it the
   following:

   - What project to load: ``--project``. This must live under a directory named
     ``projects`` which must be on :envvar:`SIERRA_PROJECT_PATH`. This is used
     to:

     - Compute the name of the library SIERRA will tell ARGoS to search for on
       :envvar:`ARGOS_PLUGIN_PATH` when looking for controller and loop function
       definitions. For example if you pass ``--project=foobar``, then SIERRA
       will tell ARGoS to search for controller and loop function definitions in
       ``libfoobar.so``, which `must` be on :envvar:`ARGOS_PLUGIN_PATH` (SIERRA
       doesn't modify :envvar:`ARGOS_PLUGIN_PATH` for you).

     - Figure out the directory to load graph and simulation processing
       configuration from.

   - What template input file to use: ``--template-input-file``. See
     :ref:`ln-tutorials-project-template-input-file` for requirements.

   - How many copies of each simulation to run per experiment: ``--n-sims``.

   - Where it is running/how to run experiments: ``--hpc-env``. See
     :ref:`ln-hpc-plugins` for available plugins.

   - How long simulations should be: ``--time-setup``. See
     :ref:`ln-vars-ts-cmdline` for cmdline syntax/options.

   - What controller to run: ``--controller``. See
     :ref:`ln-tutorials-project-main-config` for details on how valid
     controllers are defined for a :term:`Project`. :term:`Project` dependent.

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

   .. NOTE:: Generally speaking, do not try to run SIERRA with a debug build of
             whatever project you are using (:xref:`FORDYCA`, :xref:`PRISM`,
             etc). It will work but be obnoxiously/irritatingly slow. SIERRA is
             intended for `production` code (well, as close to production as
             research code gets) which is compiled with optimizations enabled.

#. Setup the cmdline environment you are going to invoke SIERRA in.

   - Set :envvar:`SIERRA_PROJECT_PATH` appropriately.

   - Set :envvar:`ARGOS_PLUGIN_PATH` appropriately.

#. Learn SIERRA's runtime :ref:`ln-usage-runtime-exp-tree`. When running, SIERRA
   will create a (rather) large directory structure for you, so reading the docs
   is worthwhile to understand what the structure means, and to gain intuition
   into where to look for the inputs/outputs of different stages, etc., without
   having to search exhaustively through the filesystem.

#. Invoke SIERRA! Again, look at the :ref:`ln-usage-examples` for some ideas.

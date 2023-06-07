.. _ln-sierra-getting-started:

===========================
Getting Started With SIERRA
===========================

If you're looking for the "I just want to try out SIERRA without doing any work"
quickstart, see :ref:`ln-sierra-trial`. Otherwise, the steps to start using
SIERRA are below.

Basic Setup
===========

#. Browse through the SIERRA :doc:`/src/glossary` to get an overview of the
   terminology that SIERRA uses in the code and in the documentation--a little
   of this will go a long way towards quickly understanding how to get started
   and use SIERRA!

   Seriously--it will make the later steps make more sense.

#. Check requirements at :ref:`ln-sierra-req` to how to organize your
   experimental inputs/template input files so they can be used with SIERRA, and
   if you need to modify the way your code outputs data so that SIERRA can
   process it.

#. Install SIERRA

   - Install SIERRA packages by following :ref:`ln-sierra-packages`.

   - Install OS packages (if you don't see your OS below you will have to find
     and install the equivalent packages).

     .. tabs::

           .. group-tab:: Ubuntu

              Install the following required packages with ``apt install``:

              - ``parallel``
              - ``cm-super``
              - ``texlive-fonts-recommended``
              - ``texlive-latex-extra``
              - ``dvipng``
              - ``psmisc``

              Install the following optional packages with ``apt install``:

              - ``pssh``
              - ``ffmpeg``
              - ``xvfb``

           .. group-tab:: OSX

              Install the following required packages with ``brew install``:

              - ``parallel``
              - ``--cask mactex``
              - ``pssh``

              Install the following optional packages with ``brew install``:

              - ``--cask xquartz``
              - ``pssh``
              - ``ffmpeg``


     If you are on a different Linux distribution you will have to find and
     install the equivalent packages.

     .. IMPORTANT:: SIERRA will not work correctly in all cases if the required
                    packages (or their equivalent) are not installed! It may
                    start, it might even not crash immediately depending on what
                    you are using it to do. If you are missing an optional
                    package for a feature you try to use, you will get an
                    error.

Project Plugin Setup
====================

Now that you have some sense of what SIERRA is/how it works, you can define a
:term:`Project` plugin to interface between your code and SIERRA. The steps to
do so are:

#. Select which :term:`Platform` SIERRA should target (what platform it targets
   will partially define how you create your project plugin). See
   :ref:`ln-sierra-platform-plugins` for supported platforms. If your desired
   platform is not in the list, never fear! It's easy to create a new platform
   plugin, see :ref:`ln-sierra-tutorials-plugin-platform`.

#. Setup the interface between your code and SIERRA by defining a SIERRA by
   following :ref:`ln-sierra-tutorials-project-project`.

#. Select an execution environment for SIERRA that matches your available
   computational resources: :ref:`ln-sierra-exec-env-hpc` or
   :ref:`ln-sierra-exec-env-robot`, following the appropriate setup guide. If
   there is nothing suitable, never fear! It's easy to create a new execution
   environment plugin, see :ref:`ln-sierra-tutorials-plugin-exec-env`.

Usage Setup
===========

Now that you have created your project plugin, you are ready to start using
SIERRA! The steps to do so are:

#. Decide what variable you are interested in investigating by consulting the
   :term:`Batch Criteria` available for your project (i.e., what variable(s) you
   want to change across some range and see how system behavior changes, or
   doesn't change). Which criteria are available to use depends on your
   :term:`Platform`; if you don't see something suitable, you can
   :ref:`Define A New Batch Criteria <ln-sierra-tutorials-project-new-bc>`.

#. Look at the :ref:`ln-sierra-usage-cli` to understand how to invoke SIERRA in
   general.

#. Look at the :ref:`ln-sierra-usage-examples` to get ideas on how to craft your
   own SIERRA invocation. If you get stuck, look at :ref:`ln-sierra-faq` for
   answers to common questions.

#. Determine how to invoke SIERRA. At a minimum you need to tell it the
   following:

   - What platform you are targeting/want to run on: ``--platform``. See
     :ref:`ln-sierra-platform-plugins` for details.

   - What project to load: ``--project``. This is used to:

     - Configure runtime search paths (e.g., :envvar:`ARGOS_PLUGIN_PATH`,
       :envvar:`ROS_PACKAGE_PATH`).

     - Figure out the directory to load graph and :term:`Experiment` data
       processing configuration from.

   - What template input file to use: ``--template-input-file``. See
     :ref:`ln-sierra-tutorials-project-template-input-file` for requirements.

   - How many variations of the main settings for each experiment to run:
     ``--n-runs``.

   - Where it is running/how to run experiments: ``--exec-env``. See
     :ref:`ln-sierra-exec-env-hpc` for available plugins.

   - What controller to run: ``--controller``. See
     :ref:`ln-sierra-tutorials-project-main-config` for details on how valid
     controllers are defined for a :term:`Project`. Project dependent.

   - How large the arena should be, what block distribution type to use (for
     example), etc. ``--scenario``. Project dependent.

   - What you are investigating; that is, what variable are you interested in
     varying: ``--batch-criteria``.

   If you try to invoke SIERRA with an (obviously) incorrect combination of
   command line options, it will refuse to do anything. For less obviously
   incorrect combinations, it will (hopefully) stop when an assert fails before
   doing anything substantial.

   Full documentation of all command line options it accepts is in
   :ref:`ln-sierra-usage-cli`, and there are many useful options that SIERRA
   accepts, so skimming the CLI docs is **very** worthwhile.

   .. IMPORTANT:: Generally speaking, do not try to run SIERRA on HPC
                  environments with a debug build of whatever project you are
                  using. It will work but be obnoxiously/irritatingly
                  slow. SIERRA is intended for `production` code (well, as close
                  to production as research code gets) which is compiled with
                  optimizations enabled.

#. Setup the cmdline environment you are going to invoke SIERRA in.

   - Set :envvar:`SIERRA_PLUGIN_PATH` appropriately.

   Different platforms may require additional environments to be set.

#. Learn SIERRA's runtime :ref:`ln-sierra-usage-runtime-exp-tree`. When running,
   SIERRA will create a (rather) large directory structure for you, so reading
   the docs is worthwhile to understand what the structure means, and to gain
   intuition into where to look for the inputs/outputs of different stages,
   etc., without having to search exhaustively through the filesystem.

#. Invoke SIERRA! Again, look at the :ref:`ln-sierra-usage-examples` for some
   ideas.

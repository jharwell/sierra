.. _startup:

===========================
Getting Started With SIERRA
===========================

If you're looking for the "I just want to try out SIERRA without doing any work"
quickstart, see :ref:`trial`. Otherwise, the steps to start using
SIERRA are below.

Basic Setup
===========

#. Browse through the SIERRA :doc:`/src/glossary` to get an overview of the
   terminology that SIERRA uses in the code and in the documentation--a little
   of this will go a long way towards quickly understanding how to get started
   and use SIERRA!

   Seriously--it will make the later steps make more sense.

#. Check requirements at :ref:`req` to how to organize your
   experimental inputs/template input files so they can be used with SIERRA, and
   if you need to modify the way your code outputs data so that SIERRA can
   process it.

#. Install SIERRA

   - Install OS packages (if you don't see your OS below you will have to find
     and install the equivalent packages). Note that these are only the OS
     packages required by the SIERRA core; many :ref:`plugins` have their own
     package requirements, documented on their respective pages.

     .. tabs::

           .. group-tab:: Ubuntu

              Install the following required packages with ``apt install``:

              - ``parallel``
              - ``psmisc``

           .. group-tab:: Fedora

              Install the following required packages with ``dnf install``:

              - ``parallel``
              - ``psmisc``

           .. group-tab:: OSX

              Install the following required packages with ``brew install``:

              - ``parallel``

     If you are on a different Linux distribution you will have to find and
     install the equivalent packages.

     .. IMPORTANT:: SIERRA will not work correctly in all cases if the required
                    packages (or their equivalent) are not installed! It may
                    start, it might even not crash immediately depending on what
                    you are using it to do. If you are missing an optional
                    package for a feature you try to use, you will get an
                    error.

   - Install SIERRA via something like::

       pip3 install sierra-research


     See :ref:`packages` for some additional useful info.



Project Plugin Setup
====================

Now that you have some sense of what SIERRA is/how it works, you can define a
:term:`Project` plugin to interface between your code and SIERRA by following
:ref:`tutorials/project/project`.

Usage Setup
===========

Now that you have created your project plugin, you are ready to start using
SIERRA! The steps to do so are:

#. Decide what variable you are interested in investigating by consulting the
   :term:`Batch Criteria` available for your project (i.e., what variable(s) you
   want to change across some range and see how system behavior changes, or
   doesn't change).  If you don't see something suitable, you can
   :ref:`Define A New Batch Criteria <tutorials/project/new-bc>`.

#. Look at the :ref:`usage/cli` common cmdline options applicable to all
   plugins in a given stage.

#. Look at the :ref:`usage/examples` to get ideas on how to craft your
   own SIERRA invocation. If you get stuck, look at :ref:`faq` for
   answers to common questions.

#. Determine how to invoke SIERRA. At a minimum you need to tell it the
   following:

   - What engine you are targeting/want to run on: ``--engine``. See
     :ref:`plugins/engine` for details.

   - What project to load: ``--project``. This is used to:

     - Configure runtime search paths (e.g., :envvar:`ARGOS_PLUGIN_PATH`,
       :envvar:`ROS_PACKAGE_PATH`).

     - Figure out the directory to load graph and :term:`Experiment` data
       processing configuration from.

   - What template input file to use: ``--expdef-template``. See
     :ref:`plugins/expdef` for requirements.

   - How many variations of the main settings for each experiment to run:
     ``--n-runs``.

   - Where it is running/how to run experiments: ``--execenv``. See
     :ref:`plugins/execenv` for available plugins.

   - What controller/algorithm to run: ``--controller``. See
     :ref:`tutorials/project/config` for details on how ``--controller`` can be
     used to declaratively drive experiment generation for a
     :term:`Project`. Project dependent.

   - How large the arena should be (for example), etc., which can be drawn from
     ``--scenario``, or the batch criteria.

   - What you are investigating; that is, what variable are you interested in
     varying: ``--batch-criteria``.

   If you try to invoke SIERRA with an (obviously) incorrect combination of
   command line options, it will refuse to do anything. For less obviously
   incorrect combinations, it will (hopefully) stop when an assert fails before
   doing anything substantial.

#. Setup the cmdline environment you are going to invoke SIERRA in:

   - Set ``PYTHONPATH`` (if necessary) so python can find the SIERRA package.

   - Set :envvar:`SIERRA_PLUGIN_PATH` appropriately so SIERRA can find plugins
     you define.

   Different engines may require additional environments to be set.

#. Learn SIERRA's runtime :ref:`usage/run-time-tree`. When running,
   SIERRA will create a (rather) large directory structure for you, so reading
   the docs is worthwhile to understand what the structure means, and to gain
   intuition into where to look for the inputs/outputs of different stages,
   etc., without having to search exhaustively through the filesystem.

#. Invoke SIERRA! Again, look at the :ref:`usage/examples` for some
   ideas.

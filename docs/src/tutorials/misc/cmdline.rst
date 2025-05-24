.. _tutorials/misc/cmdline:

============================
Extending the SIERRA Cmdline
============================

This tutorial covers how to extend the SIERRA cmdline for

- A new :term:`Project`

- A new :term:`Platform`

The requirements/steps for each are largely the same, with differences shown
below.

.. tabs::

   .. group-tab::  Projects

      Must define the ``--scenario`` and ``--controller`` cmdline arguments to
      interact with the SIERRA core.

      .. NOTE:: The ``--scenario`` argument can be used to encode the arena
                dimensions used in an experiment; this is one of two ways to
                communicate to SIERRA that size of the experimental arena for
                each :term:`Experiment`. See :ref:`req/exp` for more details.

      Can define the ``validate()`` function in their derived cmdline classes.
      This function is optional, and should assert() as needed to check cmdline
      arg validity. For most cases, you shouldn't need to define this function;
      it is provided if you need to do some tricky validation beyond what is
      baked into argparse.

   .. group-tab:: Platforms

      Because of how SIERRA sets up the cmdline plugin, platform cmdlines cannot
      define the ``validate()`` function; it will never be called if defined.
      This is generally not an issue because each project is associated with
      exactly one platform, and so can do any checks needed for the platform
      there. If you need/want to validate arguments from platforms, you can do
      that via ``cmdline_postparse_configure()`` -- see
      :ref:`tutorials/plugin/platform` for details.

      Must define ``--exp-setup`` and make it available to SIERRA via the
      ``to_cmdopts()`` function.


With that out of the way, the steps to extend the SIERRA cmdline are as follows:

#. Create ``cmdline.py`` in your project/platform plugin directory.

#. Create a ``Cmdline`` class (MUST be named this way) which inherits from the
   SIERRA cmdline as follows:

   .. tabs::

      .. group-tab:: Projects

         .. literalinclude:: cmdline-project.py
            :language: python

      .. group-tab:: Platforms

         .. literalinclude:: cmdline-platform.py
            :language: python


   All of the ``init_XXstage()`` functions are optional; if they are not given
   then SIERRA will use the version in
   :class:`~sierra.core.cmdline.CoreCmdline`.

   .. IMPORTANT:: Whichever ``init_XXstage()`` functions you define must have a
                  call to ``super().init__XXstage()`` as the first statement,
                  otherwise the cmdline arguments defined by SIERRA will not be
                  setup properly.

   The ``to_cmdopts()`` function creates a dictionary from the parsed cmdline
   arguments which SIERRA uses to create an internal ``cmdopts`` dictionary used
   throughout. Keys can have any name, though in general it is best to make them
   the same as the name of the argument (principle of least surprise). The
   following required keys must be made available during stage 2:

   - ``exec_jobs_per_node`` - This is usually provided by the ``--exec-env``
     plugin via a nested update call like::

       from sierra.core import types
       from sierra.plugins.execenv import hpc
       ...

       def to_cmdopts(args) -> types.Cmdopts:

           opts = hpc.cmdline.cmdopts_update(args)
           ...
           return opts

     in the *platform* ``to_cmdopts()`` function. You can also hardcode this
     to whatever you like.


#. Hook your created cmdline into SIERRA.

   If you created a cmdline for a :term:`Project`, there is nothing to do!
   SIERRA will pick it up automatically.

   If you created a cmdline for a :term:`Platform`, then you will need to make
   sure your cmdline is used in the ``cmdline_parser()`` function in the
   ``plugin.py`` for your new platform (see :ref:`tutorials/plugin/platform` for
   details).

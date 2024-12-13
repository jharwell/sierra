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

      Must define ``--exp-setup`` and insert it into and the ``cmdopts`` dict
      via the the ``cmdopts_update()`` function.


With that out of the way, the steps to extend the SIERRA cmdline are as follows:

#. Create ``cmdline.py`` in your project/platform plugin directory.

#. Create a ``Cmdline`` class (name up to you) which inherits from the SIERRA
   cmdline as follows:

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

   The ``cmdopts_update()`` function inserts the parsed cmdline arguments into
   the main ``cmdopts`` dictionary used throughout SIERRA. Keys can have any
   name, though in general it is best to make them the same as the name of the
   argument (principle of least surprise).

#. Hook your created cmdline into SIERRA.

   If you created a cmdline for a :term:`Project`, there is nothing to do!
   SIERRA will pick it up automatically.

   If you created a cmdline for a :term:`Platform`, then you will need to make
   sure your cmdline is used in the ``cmdline_parser()`` function in the
   ``plugin.py`` for your new platform (see :ref:`tutorials/plugin/platform` for
   details).

.. _tutorials/plugin/compare:

====================================
Creating a Product Comparison Plugin
====================================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Plugin` ``microscope`` for comparing :term:`Products <Product>`.  Before
beginning:

- See :ref:`exp/stage5-dataflow` to get a brief overview of how data
  flows through the pipeline w.r.t. stage 5,

- See :ref:`plugins/devguide` for a general overview of creating a new plugin.

- Determine the type(s) of comparison your plugin will support: comparing
  *across* controllers, *across* scenarios, and *across* batch criteria. This is
  driven by the ``--across`` stage 5 option common to all stage 5 plugins.

To begin, create the following filesystem structure in
``$HOME/git/plugins/microscope``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go. You don't *have* to call it this; if you want to use a
   different name, see :ref:`plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new plugin doesn't need any
  additional cmdline arguments, you can skip it.

These files will be populated as you go through the rest of the tutorial.

#. Create additional cmdline arguments for the new engine by following
   :ref:`plugins/devguide/cmdline`.

#. Create the following filesystem structure in
   ``$HOME/git/plugins/microscope``:

   .. tabs::

      .. tab::  ``plugin.py``

         .. include:: plugin.rst

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--compare=plugins.microscope``.

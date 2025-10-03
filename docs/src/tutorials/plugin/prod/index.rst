.. _tutorials/plugin/prod:

====================================
Creating a Product Generation Plugin
====================================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Plugin` ``shinyrock`` for processing :term:`Processed Output Data` files
to create some kind of unique deliverable.  Before we begin, see
:ref:`exp/stage4-dataflow` to get a brief overview of how data flows through the
pipeline w.r.t. stage 4, and :ref:`plugins/devguide` for a general overview of
creating a new plugin.

To begin, create the following filesystem structure in
``$HOME/git/plugins/shinyrock``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go. You don't *have* to call it this; if you want to use a
   different name, see :ref:`plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new plugin doesn't need any
  additional cmdline arguments, you can skip it.

These files will be populated as you go through the rest of the tutorial.

#. Create additional cmdline arguments for the new engine by following
   :ref:`plugins/devguide/cmdline`.

#. Create the following filesystem structure in
   ``$HOME/git/plugins/shinyrock``:

   .. tabs::

      .. tab::  ``plugin.py``

         .. include:: plugin.rst

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--proc=plugins.shinyrock``.

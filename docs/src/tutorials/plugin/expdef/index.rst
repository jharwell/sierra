.. _tutorials/plugin/expdef:

===========================================
Creating a New Experiment Definition Plugin
===========================================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Plugin` ``fizzbuzz`` for reading in and creating experiment definitions
from an imaginary "fizzbuzz" file type.

Before we begin, see :ref:`plugins/expdef` to get a brief overview of the
different components of ``--expdef-template`` files, independent of format. See
also the :ref:`plugins/devguide` for a general overview of creating a new
plugin.

Each node (i.e., each element or attribute) must be uniquely identifiable by a
unique string *path* from the root of the file to the element. This task is
usually accomplished by query languages:

- XML -> XPath

- JSON -> JSONPath

- YAML -> YAMLPath

- etc.

This means that if the markup language/format that you want to use for your
template input/experiment definition files does not have a companion query
language, you will have to write one.

To begin, create the following filesystem structure in
``$HOME/git/plugins/fizzbuzz``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go. You don't *have* to call it this; if you want to use a
   different name, see :ref:`plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new plugin doesn't need any
  additional cmdline arguments, you can skip it.

These files will be populated as you go through the rest of the tutorial.

#. Create additional cmdline arguments for the new plugin by following
   :ref:`plugins/devguide/cmdline`.


#. Create the following filesystem structure in
   ``$HOME/git/plugins/fizzbuzz``:

   .. tabs::

      .. tab::  ``plugin.py``

         .. include:: plugin.rst

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--expdef=plugins.fizzbuzz``.

.. NOTE:: Plugin names have the same constraints as python package names (e.g.,
   no dots).

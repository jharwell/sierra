.. _tutorials/plugin/expdef:

===========================================
Creating a New Experiment Definition Plugin
===========================================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Plugin` ``fizzbuzz`` for reading in and creating experiment definitions
from an imaginary "fizzbuzz" file type.

Before we begin, see :ref:`plugins/expdef` to get a brief overview of the
different components of ``--expdef-template`` files, independent of format.

Node Identification
-------------------

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

Create the Code
===============

#. Create the following filesystem structure in
   ``$HOME/git/plugins/expdef/fizzbuzz``:

   .. tabs::

      .. tab::  ``plugin.py``

         .. include:: plugin.rst

Connect to SIERRA
=================

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--expdef=expdef.fizzbuzz``.

.. NOTE:: Experiment definition plugin names have the same constraints as python
   package names (e.g., no dots).

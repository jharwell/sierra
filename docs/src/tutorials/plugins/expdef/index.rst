.. _tutorials/plugins/expdef:

======================================
Experiment Definition Files (--expdef)
======================================

This page covers the contract that experiment definition template files must
satisfy, independent of format, and then walks through how to create a new
:term:`Plugin` for a custom file format. See
:ref:`user-guide/experiment-templates` for a user-facing introduction, and
:ref:`tutorials/plugins/devguide` for the general plugin development guide.

.. _tutorials/plugins/expdef/contract:

Template File Contract
======================

An experiment definition template is a single file passed to
:ref:`--expdef-template <src/reference/cli:sierra-cli---expdef-template>`. SIERRA
reads it once per batch and applies modifications from batch criteria and
``controllers.yaml`` to produce per-experiment, per-run input files. Two
requirements apply regardless of format:

#. **Single file.** The template must be a single file. Any configuration not
   reachable within it cannot be varied by SIERRA. If your simulator normally
   uses multiple config files, provide an ``expdef_flatten()`` hook in your
   engine plugin to collapse them at stage 1 startup---see
   :ref:`tutorials/plugins/engine`.

   If your simulator normally expects multiple configuration files (a common
   pattern in ROS launch setups), you have two options:

   #. Flatten the configuration into a single file before passing it to
      SIERRA. The :term:`Engine` plugin can provide an ``expdef_flatten()`` hook
      that SIERRA calls at the start of stage 1 to perform this transformation
      automatically. See :ref:`plugins/engine` for how to implement this hook.

   #. Factor out only the parameters SIERRA needs to vary into the template and
      load the remaining files from fixed paths within your project.  This is
      the pragmatic approach for large legacy configurations where flattening is
      not practical.

#. **Unique node paths.** Every element and attribute SIERRA needs to target
   must be uniquely identifiable by a path from the root of the file. For XML
   this is XPath; for JSON, JSONPath; for YAML, YAMLPath. If your file format
   has no companion query language you will need to write one.

.. _tutorials/plugins/expdef/tokens:

Special Tokens
==============

SIERRA recognises the following tokens during stage 1 and substitutes them
before writing per-run input files. They must appear in the locations described
— SIERRA only looks for them in specific places.

``__CONTROLLER__``
   A placeholder for the controller name in the template file. SIERRA replaces
   it with the controller name derived from ``--controller`` and
   ``controllers.yaml``. Supported in XML, JSON, and YAML templates.

   In XML templates, ``__CONTROLLER__`` appears as an element tag name:

   .. code-block:: xml

      <__CONTROLLER__ library="...">
        ...
      </__CONTROLLER__>

   In JSON and YAML templates, it appears as a key whose value SIERRA
   overwrites with the resolved controller name:

   .. code-block:: json

      { "__CONTROLLER__" : "..." }

   .. code-block:: yaml

      __CONTROLLER__: "..."

   For how to target ``__CONTROLLER__`` from ``controllers.yaml``, see
   :ref:`tutorials/project/config/controllers/tokens`.

``__UUID__``
   Available in ROS1 ``.launch`` templates when a ROS1 engine is selected.
   Expands to the robot's namespace prefix concatenated with its numeric ID
   (0-based); the enclosing tag is added once per robot rather than once
   overall. Used to set per-robot parameters that cannot be controlled through
   batch criteria. For usage in ``controllers.yaml``, see
   :ref:`tutorials/project/config/controllers/tokens`.

``sierra`` (namespace)
   Reserved. Must not appear as an XML tag name or attribute value in
   ROS1 ``.launch`` templates. SIERRA uses this namespace internally.

.. _tutorials/plugins/expdef/format-restrictions:

Format-Specific Restrictions
============================

**XML**
   Modifications use XPath expressions (Python
   :mod:`xml.etree.ElementTree` syntax) to locate elements and
   attributes. The full XPath subset supported is documented in the
   Python standard library.

**JSON and YAML**
   SIERRA distinguishes between keys that map to scalar values and keys
   that map to nested objects. Batch criteria and ``controllers.yaml``
   can only target scalar-valued keys. Attempting to modify a key that
   maps to a subtree raises an error, even though such a modification
   would be valid JSON or YAML. This restriction exists to keep
   modification semantics uniform across all supported formats.

**ROS1 launch files**
   A dialect of XML. Subject to the XML restrictions above, plus the
   ``sierra`` namespace reservation and ``__UUID__`` token described
   under :ref:`plugins/expdef/tokens`.

Creating a New Expdef Plugin
============================

For the purposes of this tutorial, I will assume you are creating a new
:term:`Plugin` ``fizzbuzz`` for reading in and creating experiment definitions
from an imaginary "fizzbuzz" file type. Before beginning, see
:ref:`tutorials/plugins/devguide` for a general overview of creating a new
plugin.

To begin, create the following filesystem structure in
``$HOME/git/plugins/fizzbuzz``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go. You don't *have* to call it this; if you want to use a
   different name, see :ref:`tutorials/plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new plugin doesn't need any
  additional cmdline arguments, you can skip it.

These files will be populated as you go through the rest of the tutorial.

#. Create additional cmdline arguments for the new plugin by following
   :ref:`tutorials/plugins/devguide/cmdline`.


#. Create the following filesystem structure in
   ``$HOME/git/plugins/fizzbuzz``:

   .. tab-set::

      .. tab-item::  ``plugin.py``

         .. include:: plugin.rst

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--expdef=plugins.fizzbuzz``.

.. _plugins/expdef:

================================
Experiment Definition (--expdef)
================================

SIERRA is capable of reading
:ref:`--expdef-template<src/reference/cli:sierra---expdef-template>` from a
number of formats via ``--expdef`` plugins.  Before diving into the details of
the plugins, it is important to clarify terminology around the different
components in files passed to
:ref:`--expdef-template<src/reference/cli:sierra---expdef-template>`:

- Attribute - The value part of a <key, value> pair within an
  :ref:`--expdef-template<src/reference/cli:sierra---expdef-template>` which
  maps to a native primitive such as a bool, int, or string. An *array* also
  counts as an attribute, but only when all of its members are primitives
  (e.g. ``[80, 443]``); an array whose members are themselves maps or lists is
  treated as an *element* (see below). Attributes *cannot* contain other
  attributes. Whether array-valued attributes are supported depends on the
  format: JSON and YAML plugins support them because the language spec supports
  them, while the XML plugin does not because XML attribute values are always
  scalars.

- Element - The value part of a <key, value> pair within an
  :ref:`--expdef-template<src/reference/cli:sierra---expdef-template>` which
  maps to a sub-tree of configuration. Thus, elements can contain other
  elements, as well as *attributes* (depending on markup format). A list whose
  members are maps/lists (for example a list of objects) is an element, not an
  attribute.

- Tag - The key part of a <key, value> pair within an
  :ref:`--expdef-template<src/reference/cli:sierra---expdef-template>` which
  maps either to an *element* or an *attribute*.

The differences between these components is best illustrated with some simple
examples:

.. include:: examples.rst


Builtin --expdef Plugins
========================

With that understanding in place, the supported formats that come with SIERRA
are summarized below, followed by per-format details.

.. list-table:: Built-in ``--expdef`` format comparison
   :header-rows: 1
   :widths: 30 23 23 24

   * - Capability
     - XML
     - JSON
     - YAML
   * - Selected via
     - ``--expdef=expdef.xml``
     - ``--expdef=expdef.json``
     - ``--expdef=expdef.yaml``
   * - Path/query language
     - XPath
     - JSONPath
     - YAMLPath
   * - Multiple path matches
     - only the **first** match is modified
     - **all** matches modified (all-or-nothing)
     - **all** matches modified
   * - Array-valued attributes
     - No (attribute values are always scalars)
     - Yes (flat array of scalars)
     - Yes (flat array of scalars)
   * - Flattening (``flatten()``)
     - Not supported
     - Supported
     - Supported

.. toctree::
   :maxdepth: 1

   xml.rst
   json.rst
   yaml.rst

Additional formats can be supported via :ref:`tutorials/plugins/expdef`.

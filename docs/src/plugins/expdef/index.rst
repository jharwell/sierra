.. _plugins/expdef:

================================
Experiment Definition (--expdef)
================================

SIERRA is capable of reading
:ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>` from a
number of formats via ``--expdef`` plugins.  Before diving into the details of
the plugins, it is important to clarify terminology around the different
components in files passed to
:ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>`:

- Attribute - The value part of a <key, value> pair within an
  :ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>` which
  maps to a native primitive such as a bool, int, or string. Attributes *cannot*
  contain other attributes.

- Element - The value part of a <key, value> pair within an
  :ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>` which
  maps to a sub-tree of configuration. Thus, elements can contain other
  elements, as well as *attributes* (depending on markup format).

- Tag - The key part of a <key, value> pair within an
  :ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>` which
  maps either to an *element* or an *attribute*.

The differences between these components is best illustrated with some simple
examples:

.. include:: examples.rst


With that understanding in place, the supported formats that come with SIERRA
are:

.. toctree::
   :maxdepth: 1

   xml.rst
   json.rst
   yaml.rst

Additional formats can be supported via :ref:`tutorials/plugins/expdef`.

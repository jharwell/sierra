.. _plugins/expdef:

==============
Expdef Plugins
==============

SIERRA is capable of reading ``--expdef-template`` from a number of
formats. Supported formats that come with SIERRA are:

- :ref:`plugins/expdef/xml`

- :ref:`plugins/expdef/json`

.. _plugins/expdef/xml:

XML
===

This expdef plugin can be selected via ``--expdef=expdef.xml``.

This is the default expdef type which SIERRA will use to read input files. This
plugin does not currently support flattening/nested configuration files.

.. _plugins/expdef/json:

JSON
====

This expdef plugin can be selected via ``--expdef=expdef.json``. This plugin
supports flattening/nested configuration files.

.. versionadded:: 1.3.19

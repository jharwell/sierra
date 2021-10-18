.. _ln-storage-plugins:

===============
Storage Plugins
===============

SIERRA is capable of reading :term:`Simulation` output data in a number of
formats. Supported formats that come with SIERRA are:

- :ref:`ln-storage-plugins-csv`

.. _ln-storage-plugins-csv:


CSV
===

This storage plugin can be selected via ``--storage-medium=storage.csv``.

This is the default storage type which SIERRA will use to read simulation
outputs.

.. IMPORTANT:: The ``.csv`` files read by this plugin must be semicolon (``;``)
               delimited, `NOT` comma delimited; this may changed in a future
               version of SIERRA.

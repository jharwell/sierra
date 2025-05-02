.. _plugins/storage:

===============
Storage Plugins
===============

SIERRA is capable of reading/writing :term:`Experimental Run` output data in a
number of formats. Supported formats that come with SIERRA are:

- :ref:`plugins/storage/csv`

- :ref:`plugins/storage/arrow`

.. _plugins/storage/csv:

CSV
===

Read/write experimental run data in stage 3 which is in CSV format.  This
storage plugin can be selected via ``--storage=storage.csv``.  This is the
default storage type which SIERRA will use to read :term:`Experimental Run`
outputs.

.. IMPORTANT:: The CSV files read by this plugin must be semicolon (``;``)
               delimited, *NOT* comma delimited; this may changed in a future
               version of SIERRA.

.. _plugins/storage/arrow:

Apache Arrow
============

Read/write experimental run data in stage 3 which is in `arrow format
<https://arrow.apache.org/>`_.  This storage plugin can be selected via
``--storage=storage.arrow``.

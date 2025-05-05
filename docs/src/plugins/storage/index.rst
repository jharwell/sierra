.. _plugins/storage:

===============
Storage Plugins
===============

Storage plugins tell SIERRA the storage format for :term:`Raw Output Data` from
:term:`Experimental Runs <Experimental Run>`, and also set the output format
that SIERRA writes intermediate files to in stages 3-5 (e.g., the files that are
used as direct inputs to build graphs). Basically, it sets the I/O format. See
:ref:`dataflow` for more details.

Supported formats that come with SIERRA are:

- :ref:`plugins/storage/csv`

- :ref:`plugins/storage/arrow`

.. _plugins/storage/csv:

CSV
===

Select the CSV format for all data I/O in stages 3-5.  This storage plugin can
be selected via ``--storage=storage.csv``.  This is the default storage type
which SIERRA will use if none is specified on the cmdline.

.. versionchanged:: 1.3.28

   The CSV files read by this plugin must be comma (``,``) separated. Previously
   it was  semicolon (``;``) separated.

.. _plugins/storage/arrow:

Apache Arrow
============

Select the `arrow format <https://arrow.apache.org/>`_ for all data I/O in
stages 3-5.  This storage plugin can be selected via
``--storage=storage.arrow``.

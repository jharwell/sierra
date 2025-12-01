.. _plugins/storage:

===============
Storage Plugins
===============

Storage plugins tell SIERRA how to handle file I/O in stages 3-5. Specifically:

- How to read :term:`Raw Output Data` from :term:`Experimental Runs
  <Experimental Run>`.

- How to write :term:`Processed Output Data`, :term:`Collated Output Data`,
  etc., files to disk.

Each plugin can support any number of input formats, identified by file
extensions, and any number of output types. This is summarized below for the
storage plugins which come with SIERRA; additional formats can be supported via
:ref:`tutorials/plugin/storage`.

.. list-table::
   :header-rows: 1

   * - Plugin

     - Supported input formats

     - Allowed file extensions

     - Output type

   * - :ref:`plugins/storage/csv`

     - CSV

     - ``.csv``

     - ``pd.DataFrame``

   * - :ref:`plugins/storage/arrow`

     - `Apache arrow <https://arrow.apache.org/>`_

     - ``.arrow``

     - ``pd.DataFrame``

   * - :ref:`plugins/storage/graphml`

     - `GraphML <http://graphml.graphdrawing.org/>`_

     - ``.graphml``

     - ``nx.Graph``

Other plugins in stages 3-5 may require a specific output format; see individual
docs for details.

.. TIP:: If you are :ref:`tutorials/plugin/storage`, follow the Unix philosophy
         of doing one thing well, and make multiple smaller plugins, rather than
         1 storage plugin which handles all of your custom types/formats.

.. _plugins/storage/csv:

CSV
===

Select the CSV format for all data I/O in stages 3-5.  This storage plugin can
be selected via ``--storage=storage.csv``.  This is the default storage type
which SIERRA will use if none is specified on the cmdline.

Since this plugin produces ``pd.DataFrame`` objects, it is suitable for
processing numeric data.

.. versionchanged:: 1.3.28

   The CSV files read by this plugin must be comma (``,``) separated. Previously
   it was  semicolon (``;``) separated.

.. _plugins/storage/arrow:

Apache Arrow
============

Select the `arrow format <https://arrow.apache.org/>`_ for all data I/O in
stages 3-5.  This storage plugin can be selected via
``--storage=storage.arrow``.

Since this plugin produces ``pd.DataFrame`` objects, it is suitable for
processing numeric data.

.. _plugins/storage/graphml:

GraphML
=======

Select the `GraphML format <http://graphml.graphdrawing.org/>`_ for all data I/O
in stages 3-5.  This storage plugin can be selected via
``--storage=storage.graphml``.

Since this plugin produces ``nx.Graph`` objects, it is *not* suitable for
processing numeric data. E.g., running the :ref:`plugins/proc/stat` plugin
with this plugin selected will cause an error.

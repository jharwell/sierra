.. _tutorials/plugin/storage:

=============================
Creating a New Storage Plugin
=============================

For the purposes of this tutorial, I will assume you are creating a new storage
:term:`Plugin` ``infinite``, and the code for that plugin lives in
``$HOME/git/plugins/storage/infinite``.

Before beginning, see the :ref:`plugins/devguide` for a general overview of
creating a new plugin.

To begin, create the following filesystem structure in
``$HOME/git/plugins/infinite``.

-  ``plugin.py`` - This file is required, and is where most of the bits for the
   plugin will go. You don't *have* to call it this; if you want to use a
   different name, see :ref:`plugins/devguide/schemas` for options.

- ``cmdline.py`` This file is optional. If your new plugin doesn't need any
  additional cmdline arguments, you can skip it.

These files will be populated as you go through the rest of the tutorial.

#. Create additional cmdline arguments for the new engine by following
   :ref:`plugins/devguide/cmdline`.

#. In ``plugin.py``, you must define the following functions:

   .. tabs::

      .. tab:: ``supports_input()``

         This function takes a file extension as an argument, and returns if the
         plugin supports it or not as an *input* format. This assumes a 1:1
         mapping between file extensions and the actual data format across all
         possible projects/use cases, which may not be realistic.

         .. code-block:: python

            def supports_input(fmt: str) -> bool:
                """
                Returns TRUE if the plugin supports files with the specified
                extension.
                """

      .. tab:: ``supports_output()``


         This function takes a type as input, and returns if the plugin supports
         it or not as an *output* format. Some examples of output formats SIERRA
         currently supports:

         - ``pd.DataFrame``
         - ``nx.Graph``

         .. code-block:: python

            def supports_output(fmt: type) -> bool:
                """
                Returns TRUE if the plugin supports the specified output
                format.
                """

#. In ``plugin.py``, you may define the following functions; which functions are
   actually required or not is dependent on the output formats that your plugin
   supports:

   - ``pd.DataFrame`` -> ``df_read()/df_write()`` are required.

   - ``nx.Graph`` -> ``graph_read()/graph_write()`` are required.


   .. tabs::

      .. tab:: ``df_read()``

         .. code-block:: python

            def df_read(path: pathlib.Path, **kwargs) -> pd.DataFrame:
                """
                Return a dataframe containing the contents of the input format
                at the specified path.  For other storage methods (e.g.
                database), you can use a function of the path way to uniquely
                identify the file in the database (for example).
                """

      .. tab:: ``df_write()``

         .. code-block:: python

            def df_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
                """
                Write a dataframe to the specified path.  For other storage
                methods (e.g. database), you can use a function of the path way
                to uniquely identify the file in the database (for example) when
                you add it.
                """

      .. tab:: ``graph_read()``

         .. code-block:: python

            def graph_read(path: pathlib.Path, **kwargs) -> nx.Graph:
                """
                Return a graph containing the contents of the input format
                at the specified path.
                """

      .. tab:: ``graph_write()``

         .. code-block:: python

            def df_write(graph: nx.Graph, path: pathlib.Path, **kwargs) -> None:
                """
                Write a graph to the specified path.
                """




#. Put ```$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--storage=storage.infinite``.

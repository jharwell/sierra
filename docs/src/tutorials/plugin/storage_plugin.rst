.. _ln-sierra-tutorials-plugin-storage:

=============================
Creating a New Storage Plugin
=============================

For the purposes of this tutorial, I will assume you are creating a new storage
:term: `Plugin` ``infinite``, and the code for that plugin lives in
``$HOME/git/plugins/storage/infinite``.

Create the Code
===============

#. Create the following filesystem structure in
   ``$HOME/git/plugins/storage/infinite``:

   .. tabs::

      .. code-tab::  python ``plugin.py``

         import pandas as pd


        def df_read(path: str, **kwargs) -> pd.DataFrame:
            """
            Return a dataframe containing the contains of the ``.csv`` at the
            specified path. For other storage methods (e.g. database), you can
            use a function of the path way to uniquely identify the file in the
            database (for example).

            """


        def df_write(df: pd.DataFrame, path: str, **kwargs) -> None:
            """
            Write a dataframe containing to the specified path. For other
            storage methods (e.g. database), you can use a function of the path
            way to uniquely identify the file in the database (for example) when
            you add it.

            """

Connect to SIERRA
=================

#. Put ``$HOME/git/plugins`` on your :envvar:`SIERRA_PLUGIN_PATH`. Then
   your plugin can be selected as ``--exec-env=storage.infinite``.

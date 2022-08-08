Within this file, you must define the following classes, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them.

.. code-block:: python

        import pandas as pd
        import pathlib

        def df_read(path: pathlib.Path, **kwargs) -> pd.DataFrame:
            """
            Return a dataframe containing the contents of the CSV at the
            specified path. For other storage methods (e.g. database), you can
            use a function of the path way to uniquely identify the file in the
            database (for example).

            """


        def df_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
            """
            Write a dataframe containing to the specified path. For other
            storage methods (e.g. database), you can use a function of the path
            way to uniquely identify the file in the database (for example) when
            you add it.

            """

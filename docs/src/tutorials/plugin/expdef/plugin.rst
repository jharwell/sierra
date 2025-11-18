Within this file, you must define the following classes, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them.

.. code-block:: python

        import pathlib
        import implements
        from sierra.core.experiment import definition

        @implements.implements(definition.BaseExpDef)
        class ExpDef():

Within this file, you must define the following functions, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them.

.. code-block:: python

        import pathlib
        import implements
        from sierra.core.experiment import definition

        def root_querypath() -> str:
            """Get unique string identifying the root element for the backend
            file type. This is needed when scaffolding batch experiments so
            SIERRA can do so in a format-agnostic way.
            """
            return "mystring"

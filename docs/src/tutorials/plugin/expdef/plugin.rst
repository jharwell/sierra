Within this file, you must define the following classes, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them.

.. code-block:: python

        import pathlib
        import implements
        from sierra.core.experiment import definition

        @implements.implements(definition.BaseExpDef)
        class ExpDef():

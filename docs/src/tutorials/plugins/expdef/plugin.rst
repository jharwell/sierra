.. SPDX-License-Identifier:  MIT

Within ``plugin.py`` you must define a class named **EXACTLY** ``ExpDef`` and a
module-level function named **EXACTLY** ``root_querypath()``, otherwise SIERRA
will not detect them. ``ExpDef`` derives from
:class:`~sierra.core.experiment.definition.BaseExpDef` and implements the
modification interface described in :ref:`the required interface
<tutorials/plugins/expdef/interface>` below.

.. code-block:: python

   import pathlib
   import typing as tp

   from sierra.core.experiment import definition


   def root_querypath() -> str:
       """Return a unique string identifying the root element for this file
       type. Needed when scaffolding batch experiments so SIERRA can do so in a
       format-agnostic way (e.g. ``"."`` for XML, ``"$"`` for JSON).
       """
       return "$"


   class ExpDef(definition.BaseExpDef):
       def __init__(
           self,
           input_fpath: pathlib.Path,
           write_config: tp.Optional[definition.WriterConfig] = None,
       ) -> None:
           ...

       # ... implement the required interface (see below) ...

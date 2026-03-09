Within this file, you must define the following functions, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them.

.. code-block:: python

   from sierra.core import types, batchroot
   import sierra.core.variables.batch_criteria as bc

   def proc_exps(
       main_config: types.YAMLDict,
       cmdopts: types.Cmdopts,
       cli_args: argparse.Namespace,
   ) -> None:
       """Compare products across batch experiments.

       Can be serially or in parallel; should respect
       ``--processing-parallelism``. See
       :class:`~sierra.plugins.compare.comparator.BaseComparator` for some
       reusable scaffolding.
       """

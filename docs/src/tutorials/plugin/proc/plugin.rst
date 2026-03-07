Within this file, you must define the following functions, which must be named
**EXACTLY** as specified, otherwise SIERRA will not detect them.

.. code-block:: python

   from sierra.core import types, batchroot
   import sierra.core.variables.batch_criteria as bc

   def proc_batch_exp(
       main_config: types.YAMLDict,
       cmdopts: types.Cmdopts,
       pathset: batchroot.PathSet,
       criteria: bc.XVarBatchCriteria,
   ) -> None:
       """Process the results for all experiments in the batch experiment.

       Can be serially or in parallel. Processing should respect
       ``--processing-parallelism`` and ``--exp-range``.
       """

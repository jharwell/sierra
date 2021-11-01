.. _ln-tutorials-project-hooks:

============
SIERRA Hooks
============

SIERRA allows a number of different elements of its pipeline to be customized
and extend by a :term:`Project`. To override part of a stage of the SIERRA
pipeline, you must create a ``pipeline/stageX`` directory structure in your
project directory, where ``stageX`` is the stage you want to override part of.

.. NOTE:: This is the most advanced feature of SIERRA, and strange things may
          happen or things might not work right if you don't call the
          ``super()`` version of whatever functions you are overriding in your
          hook.

.. WARNING:: Don't try to override parts of the pipeline which are not listed
             below. It will probably not work, and even if it does there is
             every chance that it will break stuff.

Stage 3 Hooks
=============

Simulation Collation
--------------------

In order to generate additional inter-experiment graphs, you have to also
collate additional ``.csv`` files by:

#. Create ``pipeline/stage3/sim_collator.py``.

#. Override the
   :class:`sierra.core.pipeline.stage3.sim_collator.SimulationCSVGatherer` class:

   .. code-block:: python

      import sierra.core.pipeline.stage3.sim_collator as sim_collator

      class SimulationCSVGatherer(sim_collator.SimulationCSVGatherer):
          def gather_csvs_from_sim(self, sim: str) -> tp.Dict[tp.Tuple[str, str], pd.DataFrame]:
              ...


Stage 4 Hooks
=============

Tiered YAML Config
------------------

Suppose you have some graphs which are common to multiple SIERRA projects, and
you don't want to have to duplicate the graph definitions in the ``.yaml``
files. You can put those definitions in a single location and then add them to
the ``.yaml`` graph definitions that are unique to the :term:`Project` as
follows:

#. Create ``pipeline/stage4/yaml_config_loader.py``.

#. Override the
   :class:`sierra.core.pipeline.stage4.yaml_config_loader.YAMLConfigLoader` class:

   .. code-block:: python

      import sierra.core.pipeline.stage4.yaml_config_loader as ycl

      class YAMLConfigLoader(ycl.YAMLConfigLoader):
          def __call__(self, cmdopts: types.Cmdopts) -> tp.Dict[str, tp.Dict[str, str]]:
              ...

Intra-Experiment Graph Generation
---------------------------------

You way want to extend the set of graphs which is generated for each experiment
in the batch, based on what batch criteria is selected, or for some other
reason. To do so:

#. Create ``pipeline/stage4/intra_exp_graph_generator.py``.

#. Override the
   :class:`sierra.core.pipeline.stage4.inter_exp_graph_generator.InterExpGraphGenerator`
   class:

   .. code-block:: python

      import sierra.core.pipeline.stage4 as stage4

      class IntraExpGraphGenerator(stage4.intra_exp_graph_generator.IntraExpGraphGenerator):
          def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
              ...

Inter-Experiment Graph Generation
---------------------------------

You way want to extend the set of graphs which is generated across each each experiment
in the batch (e.g., to create graphs of summary performance measures). To do so:

#. Create ``pipeline/stage4/Inter_exp_graph_generator.py``.

#. Override the
   :class:`sierra.core.pipeline.stage4.inter_exp_graph_generator.InterExpGraphGenerator`
   class:

   .. code-block:: python

      import sierra.core.pipeline.stage4 as stage4

      class InterExpGraphGenerator(stage4.inter_exp_graph_generator.InterExpGraphGenerator):
          def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
              ...

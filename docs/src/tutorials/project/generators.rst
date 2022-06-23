.. _ln-sierra-tutorials-project-generators:

=======================
Generator Configuration
=======================

.. _ln-sierra-tutorials-project-generators-scenario-config:

Per-Scenario Configuration
==========================

To enable SIERRA to generate experiment definitions based on the ``--scenario``
you specify, you need to:

#. Create ``generators/scenario_generator_parser.py`` in your ``--project``
   directory.

   Within this file, you must define the ``ScenarioGeneratorParser`` class with
   the following signature:

   .. code-block:: python

      import typing as tp

      class ScenarioGeneratorParser():
          def __init__(self):
              ...

          def to_scenario_name(self, args) -> tp.Optional[str]:
              """
              Parse the scenario generator from cmdline arguments into a
              string. Should return None if ``args`` is None (stage5).
              """
              ...

          def to_dict(self, scenario_name: str) -> str:
              """
              Given a string (presumably a result of an earlier cmdline parse),
              parse it into a dictionary of components: arena_x, arena_y,
              arena_z, scenario_tag

              which specify the X,Y,Z dimensions of the arena a unique tag/short
              scenario name unique among all scenarios for the project, which is
              used which creating the SIERRA runtime directory structure.
              """
              ...


#. Create ``generators/scenario_generators.py`` in your ``--project`` directory.

   Within this file, you must define at least one function (and presumably one
   or more classes representing the scenarios you want to test with), which is
   ``gen_generator_name()``, which takes the ``--scenario`` argument and returns
   the string of the class name within ``scenario_generators.py`` that SIERRA
   should use to generate scenario definitions for your experiments:

   .. code-block:: python

      def gen_generator_name(scenario_name: str) -> str:
          ...

   Each generator class within ``scenario_generators.py`` must define the
   ``generate()`` function like so:

   .. code-block:: python

      class MyScenarioGenerator():
          ...

      def generate(self):
          ...


.. _ln-sierra-tutorials-project-generators-sim-config:

Per-Experimental Run Configuration
==================================

In order to hook into SIERRA stage 1 experiment generation (doing so is
optional), you need to:

#. Create ``generators/exp_generators.py`` in your ``--project`` directory.

#. Define a ``ExpRunDefUniqueGenerator`` class in this file, overriding the
   ``generate()`` function with your customizations. Your class really should be
   derived from a platform generator (e.g.,
   :class:`~sierra.plugins.platform.argos.generators.platform_generators.PlatformExpRunDefUniqueGenerator`)
   and override the ``generate()`` function, though you don't have to.

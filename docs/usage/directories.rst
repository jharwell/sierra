Directory Structure
===================

It is helpful to know the purpose of how sierra is layed out, so it is easier to
see how things fit together, and where to look for implementation details when
sierra keeps crashing. So here is the directory structure:

* ``generators/`` - Controller and scenario generators used to modify template
                    .argos files to provide the setting/context for running
                    experiments with variables.

* ``graphs/`` - Generic code to generate graphs of different types.

* ``perf_measures/`` - Measures to compare performance of different controllers
                       across experiments.

* ``pipeline/`` - Core pipline code in 5 stages:

  #. Generate inputs
  #. Run experiments
  #. Process results of running experiments (averaging, etc.)
  #. Generate graphs within a single experiment and between
     experiments in a batch.
  #. Generate graphs comparing batched experiments (not part of
     default pipeline).

* ``scripts/`` - Contains some ``.pbs`` scripts that can be run on MSI. Scripts
                 become outdated quickly as the code base for this project and
                 its upstream projects changes, so scripts should not be relied
                 upon to work as is. Rather, they should be used to gain insight
                 into how to use sierra and how to craft your own script.

* ``templates/`` - Contains template .argos files. Really only necessary to be
                   able to change configuration that is not directly
                   controllable via generators, and the # of templates should be
                   kept small, as they need to be manually kept in sync with the
                   capabilities of fordyca.

* ``variables/`` - Generators for experimental variables to modify template
                   .argos files in order to run experiments with a given
                   controller.

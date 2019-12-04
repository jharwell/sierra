How to Add A New Plugin (I mean project)
=======================================

The argument to the cmdline option ``--plugin`` is added to the path
``plugins/<option>``, and the plugin directory tree must have the following
structure and content (a subset of the SIERRA core directory structure):

- ``config/`` - Plugin YAML configuration root. within this directory, the following
                files must be present when running a stage that utilizes them:

  - ``main.yaml`` - Main SIERRA configuration file. This file is required for all
    pipeline stages.

  - ``controllers.yaml`` - Configuration for controllers (input file/graph
    generation). This file is required for all pipeline stages.

  - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
    linegraphs. This file is optional. If it is present, graphs defined in it
    will be added to those specified in ``core/config/intra-graphs-line.yaml``,
    and will be generated if stage 4 is run.

  - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
    heatmaps. This file is optional. If it is present, graphs defined in it will
    be added to those specified in ``core/config/intra-graphs-hm.yaml``, and
    will be generated if stage 4 is run.

  - ``inter-graphs.yaml`` - Configuration for inter-experiment graphs. This file
    is optional. If it is present, graphs defined in it will be added to those
    specified in ``core/config/inter-graphs-line.yaml``, and will be generated
    if stage 4 is run.

  - ``stage5.yaml`` - Configuration for stage5 controller comparisons. This file
    is required if stage5 is run, and optional otherwise.

- ``generators/scenario_generators.py`` - Specifies extensions/specializations
  of the foraging scenarios in the SIERRA core, as well as any other scenarios
  the user would want to be able to pass via the ``--scenario`` cmdline
  argument.

- ``variables/`` - Additional variables (including batch criteria) defined by
  the plugin/project that can be directly or indirectly used by the
  ``--batch-criteria`` and ``--scenario`` cmdline arguments.

- ``cmdline.py`` - Specifies cmdline extensions specific to the plugin/project.

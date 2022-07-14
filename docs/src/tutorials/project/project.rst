.. _ln-sierra-tutorials-project-project:

=============================
Creating a New SIERRA Project
=============================

#. Decide what :term:`Platform` your :term:`Project` will target. Currently,
   there is no way to share projects across platforms; any common code will have
   to be put into common python files and imported as needed.

#. Create the directory which will hold your :term:`Project`. The directory your
   project must be on :envvar:`SIERRA_PLUGIN_PATH` or SIERRA won't be able to
   find your project. For example, if your project is ``proj-awesome``, and
   that directory is in ``projects`` as ``/path/to/projects/proj-awesome``, then
   ``/path/to/projects`` needs to be on :envvar:`SIERRA_PLUGIN_PATH`.

#. Create the following directory structure within your project directory (or
   copy and modify the one from an existing project).

   .. IMPORTANT:: Once you create the directory structure below you need to
                  INSTALL your project with pip so that not only can SIERRA find
                  it, but so can the python interpreter. If you don't want to do
                  that, then you need to put your project plugin directory on
                  :envvar:`PYTHONPATH`. Otherwise, you won't be able to use your
                  project plugin with SIERRA.

   - ``config/`` - Plugin YAML configuration root. This directory is required
     for all projects. Within this directory, the following files are used (not
     all files are required when running a stage that utilizes them):

     - ``main.yaml`` - Main SIERRA configuration file. This file is required for
       all pipeline stages. See :ref:`ln-sierra-tutorials-project-main-config`
       for documentation.

     - ``controllers.yaml`` - Configuration for controllers (input file/graph
       generation). This file is required for all pipeline stages. See
       :ref:`ln-sierra-tutorials-project-main-config` for documentation.

     - ``intra-graphs-line.yaml`` - Configuration for intra-experiment
       linegraphs. This file is optional. If it is present, graphs defined in it
       will be added to those specified in
       ``<sierra>/core/config/intra-graphs-line.yaml``, and will be generated if
       stage 4 is run. See :doc:`graphs_config` for documentation.

     - ``intra-graphs-hm.yaml`` - Configuration for intra-experiment
       heatmaps. This file is optional. If it is present, graphs defined in it
       will be added to those specified in
       ``<sierra>/core/config/intra-graphs-hm.yaml``, and will be generated if
       stage 4 is run. See :doc:`graphs_config` for documentation.

     - ``inter-graphs.yaml`` - Configuration for inter-experiment graphs. This
       file is optional. If it is present, graphs defined in it will be added to
       those specified in ``<sierra>/core/config/inter-graphs-line.yaml``, and
       will be generated if stage 4 is run. See :doc:`graphs_config` for
       documentation.

     - ``stage5.yaml`` - Configuration for stage5 controller comparisons. This
       file is required if stage 5 is run, and optional otherwise. See
       :doc:`stage5_config` for documentation.

     - ``models.yaml`` - Configuration for intra- and inter-experiment
       models. This file is optional. If it is present, models defined and
       enabled in it will be run before stage 4 intra- and/or inter-experiment
       graph generation, if stage 4 is run. See :doc:`models` for documentation.

   - ``generators/`` - Classes to enable SIERRA to generate changes to template
     XML files needed by your project. This directory is required for all SIERRA
     projects.

     - ``scenario_generator_parser.py`` - Contains the parser for parsing the
       contents of ``--scenario`` into a dictionary which can be used to
       configure experiments. This file is required. See
       :ref:`ln-sierra-tutorials-project-generators-scenario-config` for
       documentation.

     - ``scenario_generators.py`` - Specifies classes and functions to enable
       SIERRA to generate XML file modifications to the
       ``--template-input-file`` based on what is passed as ``--scenario`` on
       the cmdline. This file is required. See
       :ref:`ln-sierra-tutorials-project-generators-scenario-config` for documentation.

     - ``exp_generators.py`` - Contains extensions to the per-:term:`Experiment`
       and per-:term:`Experimental Run` configuration that SIERRA performs. See
       :ref:`ln-sierra-tutorials-project-generators-sim-config` for documentation. This
       file is optional.

   - ``variables/`` - Additional variables (including batch criteria) defined by
     the plugin/project that can be directly or indirectly used by the
     ``--batch-criteria`` and ``--scenario`` cmdline arguments. This directory
     is optional.

   - ``models/`` - Theoretical models that you want to run against empirical
     data from experimental runs (presumably to compare predictions with). This
     directory is optional. See :doc:`models` for documentation.

   - ``cmdline.py`` - Specifies cmdline extensions specific to the
     plugin/project. This file is required. See :doc:`cmdline` for
     documentation.

#. Configure your project so SIERRA understands how to generate
:term:`Experimental Run` inputs and process outputs correctly by following
:ref:`ln-sierra-tutorials-project-main-config`.

#. Define graphs to be generated from :term:`Experiment` outputs by following
   :doc:`graphs_config`. Strictly speaking this is optional, but automated graph
   generation during stage 4 is one of the most useful parts of SIERRA, so its
   kind of silly if you don't do this.

#. Setup your ``--template-input-file`` appropriately by following
   :doc:`template_input_file`.

Optional Steps
==============

#. Define additional batch criteria to investigate variables of interest
   specific to your project by following :ref:`ln-sierra-tutorials-project-new-bc`.

#. Define one or more :term:`Models <Model>` to run to compare with empirical
   data.

#. Add additional per-run configuration such as unique output directory
   names, random seeds, etc. in various python files referenced by
   ``scenario_generators.py`` and ``exp_generators.py`` beyond what is required
   for ``--scenario``.  SIERRA can't set stuff like this up in a project
   agnostic way.

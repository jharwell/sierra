.. _ln-tutorials-project-project:

=============================
Creating a New SIERRA Project
=============================

#. Create the directory which will hold your :term:`Project`, in a directory
   named ``projects``. ``projects`` must be on on :envvar:`SIERRA_PROJECT_PATH`
   (or alternatively, :envvar:`PYTHONPATH`) or SIERRA won't be able to find
   it. You should use :envvar:`SIERRA_PROJECT_PATH` though, because it is more
   self-documenting.

   For example, if your project is ``proj-awesome``, and that directory is in
   ``projects`` as ``/path/to/projects/proj-awesome``, and the path to
   ``/path/to/projects`` needs to be on :envvar:`SIERRA_PROJECT_PATH`.

   .. NOTE:: The name of the library C++ SIERRA will tell ARGoS to search for
      on :envvar:`ARGOS_PLUGIN_PATH` when looking for controller and loop
      function definitions is computed from the project name. For example if you
      pass ``--project=project-awesome``, then SIERRA will tell ARGoS to search in
      ``proj-awesome.so`` for both loop function and controller definitions via
      XML changes.

   .. NOTE:: SIERRA does `not` modify :envvar:`ARGOS_PLUGIN_PATH`, so you will
             need to make sure that the directories containing the necessary
             ``.so`` library are on it prior to invoking SIERRA.

#. Create the following directory structure within your project directory (or
   copy and modify the one from an existing project).

   - ``config/`` - Plugin YAML configuration root. within this directory, the following
     files are used (not all files are required when running a stage that utilizes
     them):

     - ``main.yaml`` - Main SIERRA configuration file. This file is required for all
       pipeline stages. See :doc:`main_config` for documentation.

     - ``controllers.yaml`` - Configuration for controllers (input file/graph
       generation). This file is required for all pipeline stages. See
       :doc:`main_config` for documentation.

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

   - ``generators/``

     - ``scenario_generators.py`` - Specifies classes and functions to enable
       SIERRA to generate XML file modifications to the
       ``--template-input-file`` based on what is passed as ``--scenario`` on
       the cmdline. This file is required. See
       :ref:`ln-tutorials-project-generators-scenario-config` for documentation.

     - ``exp_generators.py`` - Contains extensions to the per-simulation
       configuration that SIERRA performs. See
       :ref:`ln-tutorials-project-generators-sim-config` for documentation. This file is
       optional.

   - ``variables/`` - Additional variables (including batch criteria) defined by
     the plugin/project that can be directly or indirectly used by the
     ``--batch-criteria`` and ``--scenario`` cmdline arguments.

   - ``models/`` - Theoretical models that you want to run against empirical
     data from simulations (presumably to compare predictions with).

   - ``cmdline.py`` - Specifies cmdline extensions specific to the plugin/project.

#. Configure your project so SIERRA understands how to generate simulation
   inputs and process outputs correctly by following :doc:`main_config`.

#. Define graphs to be generated from simulation outputs by following
   :doc:`graphs_config`. Strictly speaking this is optional, but automated graph
   generation during stage 4 is one of the most useful parts of SIERRA, so its kind
   of silly if you don't do this.

#. Setup your ``--template-input-file`` appropriately by following
   :doc:`template_input_file`.

Optional Steps
==============

#. Define additional batch criteria to investigate variables of interest
   specific to your project by following :ref:`ln-tutorials-project-new-bc`.

#. Define one or more :term:`Models <Model>` to run to compare with empirical
   data.

#. Add additional per-simulation configuration such as unique output directory
   names, random seeds (if you don't use the ARGoS one), etc. in various python
   files referenced by ``scenario_generators.py`` and ``exp_generators.py``
   SIERRA can't set stuff like this up in a project agnostic way.

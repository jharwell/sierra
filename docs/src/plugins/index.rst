.. _plugins:

===============
Builtin Plugins
===============

SIERRA's behaviour is almost entirely determined by the plugins you select on
the command line. The core provides the pipeline skeleton — five ordered stages,
a shared filesystem convention, and a cmdline assembly mechanism — but every
meaningful action in each stage is delegated to a plugin.

To use any built-in plugin you only need to name it on the command line via the
appropriate flag. Details on configuration and capabilities are in each plugin's
own documentation, linked below.

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Type
     - Flag
     - Responsibility

   * - :ref:`Engine <plugins/engine>`
     - :ref:`--engine<src/reference/cli:sierra---engine>`
     - The simulator or robot platform experiments run on. Controls how
       ``--expdef-template`` files are modified in stage 1, how runs are
       launched in stage 2, and how engine-specific information (e.g., agent
       counts) is extracted during stages 3–5.

   * - :ref:`Execution environment <plugins/execenv>`
     - :ref:`--execenv<src/reference/cli:sierra---execenv>`
     - Where and how experiments execute. Translates SIERRA's abstract "run
       these N experiments in parallel" request into concrete shell commands
       for a laptop, a SLURM cluster, a PBS cluster, or a robot network.

   * - :ref:`Experiment definition <plugins/expdef>`
     - :ref:`--expdef<src/reference/cli:sierra---expdef>`
     - The file format of
       :ref:`--expdef-template<src/reference/cli:sierra---expdef-template>`. Controls how
       SIERRA reads and modifies template files to inject batch criteria changes
       in stage 1.  Supported formats include XML, JSON, and YAML.

   * - :ref:`Storage <plugins/storage>`
     - :ref:`--storage<src/reference/cli:sierra---storage>`
     - How experimental output data is read from and written to disk in
       stages 3–5. Determines the in-memory representation (e.g.,
       ``pd.DataFrame``, ``nx.Graph``) that processing and product plugins
       receive. Defaults to ``storage.csv``.

   * - :ref:`Processors <plugins/proc>`
     - :ref:`--proc<src/reference/cli:sierra---proc>`
     - What to do with raw output data in stage 3. Multiple processors can be
       active simultaneously; common examples are statistics generation and
       intra-experiment data collation. At least one processor must be active
       for stage 4 to have anything to work with.

   * - :ref:`Product generators <plugins/prod>`
     - :ref:`--prod<src/reference/cli:sierra---prod>`
     - What products to generate from processed data in stage 4. The built-in
       ``prod.graphs`` plugin generates camera-ready graphs; ``prod.render``
       stitches simulation frames into videos.

   * - :ref:`Comparison generators <plugins/compare>`
     - :ref:`--compare<src/reference/cli:sierra---compare>`
     - How to compare products across controllers or scenarios in stage 5.
       Only active when ``--pipeline 5`` is passed.

   * - :ref:`Project <tutorials/project/project>`
     - :ref:`--project<src/reference/cli:sierra---project>`
     - Your research code: batch criteria definitions, controller and scenario
       arguments, ``graphs.yaml`` graph configuration, and any processing
       hooks for your specific output data. See note below.

.. NOTE:: The project plugin is qualitatively different from the other types
   above. Every other plugin is infrastructure — interchangeable components
   provided by SIERRA or an engine vendor. The project plugin is your code. It
   cannot be shared across engines; if you want to run on both ARGoS and
   ROS1+Gazebo you need two project plugins, though they can share Python code
   via ordinary imports. See :ref:`tutorials/project/project` for details.

For a deeper explanation of how these plugin types fit together at runtime —
including why your available command line flags depend on which plugins you
select, and which layer to change when something does not behave as expected —
see :ref:`arch/plugin-system`.

Plugin Reference
================

.. toctree::
   :maxdepth: 1

   engine/index
   execenv/index
   storage/index
   expdef/index
   proc/index
   prod/index
   compare/index

.. _ln-tutorials-project-main-config:

==================
Main Configuration
==================

The three main required configuration files that you must define so that SIERRA
knows how to interact with your project are shown below:

.. tabs::

   .. tab:: ``config/main.yaml``

      .. tabs::

         .. group-tab:: ARGoS

            An example main configuration file for the ARGoS platform:

            .. code-block:: YAML

               # Per-project configuration for SIERRA core. This dictionary is
               # mandatory.
               sierra:
                 # Configuration for each experimental run. This dictionary is
                 # mandatory for all experiments.
                 run:
                   # The directory within each experimental run's working
                   # directory which will contain the metrics output as by the
                   # run. This key is mandatory for all experiments. Can be
                   # anything; this is the interface link between where the
                   # project code outputs things and where SIERRA looks for
                   # outputs.
                   run_metrics_leaf: 'metrics'

                   # The name of the shared library where project code can be
                   # found, sans file extension. Must include
                   # 'lib'. Optional. If not present, then SIERRA will use
                   # ``--project`` as the name of the library to tell ARGoS to
                   # use.
                   library_name: 'libawesome'

                 # Configuration for performance measures. This key is mandatory
                 # for all experiments. The value is the location of the .yaml
                 # configuration file for performance measures. It is a separate
                 # config file so that multiple scenarios within a single
                 # project which define performance measures in different ways
                 # can be easily accommodated without copy-pasting.
                 perf: 'perf-config.yaml'

         .. group-tab:: ROS+Gazebo

            An example main configuration file for the ROS+Gazebo platform:

            .. code-block:: YAML

               # Per-project configuration for SIERRA core. This dictionary is
               # mandatory.
               sierra:
                 # Configuration for each experimental run. This dictionary is
                 # mandatory for all experiments.
                 run:
                   # The directory within each experimental run's working
                   # directory which will contain the metrics output as by the
                   # run. This key is mandatory for all experiments. Can be
                   # anything; this is the interface link between where the
                   # project code outputs things and where SIERRA looks for
                   # outputs.
                   run_metrics_leaf: 'metrics'

                 # Configuration for performance measures. This key is mandatory
                 # for all experiments. The value is the location of the .yaml
                 # configuration file for performance measures. It is a separate
                 # config file so that multiple scenarios within a single
                 # project which define performance measures in different ways
                 # can be easily accommodated without copy-pasting.
                 perf: 'perf-config.yaml'

              # Configuration specific to the ROS platforms. This
              # dictionary is required if that platform is selected, and
              # optional otherwise.
              ros:
                # The list of robot configuration for the platform that you want
                # SIERRA to support (that actual list of robots supported by the
                # platform can be much larger).
                robots:
                  # The name of a supported robot which can be passed to
                  # ``--robot``. Can be any valid python string, and does not
                  # have to match whatever the robot is called in its ROS
                  # package.
                  governator:
                    # The ROS package that the robot can be found in. This
                    # package must be on your ROS_PACKAGE_PATH or SIERRA will
                    # fail at runtime. This key is required.
                    pkg: "my_ros_package"

                    # The name of your robot within its ROS package. Used by
                    # SIERRA to add the ROS node to load its description. This
                    # key is required.
                    model: "terminator"

                    # The name of a variation of the base robot model. This key
                    # is optional. If present, the actual name of the robot in
                    # the ROS package used to source the robot description is
                    # constructed via <model>_<model_variant>
                    model_variant: "T1000"

                    # The robot prefix which will be prepended to the robot's
                    # numeric ID to form its UUID. E.g., for robot 14, its UUID
                    # will be <prefix>14. This is used by SIERRA to create
                    # unique namespaces for each robot's nodes so that all their
                    # ROS topics are unique.
                    prefix: "T"

                  myrobot2:
                    ...




   .. tab:: ``config/perf-config.yaml``

      Configuration for summary performance measures. Does not have to be named
      ``perf-config.yaml``, but must match whatever is specified in
      ``main.yaml``.

      .. code-block:: YAML

         perf:

           # Is the performance measure for the project inverted, meaning that
           # lower values are better. This key is optional; defaults to False if
           # omitted.
           inverted: true

           # The ``.csv`` file under ``statistics/`` for each experiment which
           # contains the averaged performance information for the
           # experiment. This key is required.
           intra_perf_csv: 'block-transport.csv'

           # The ``.csv`` column within ``intra_perf_csv`` which is the
           # temporally charted performance measure for the experiment. This key
           # is required.
           intra_perf_col: 'cum_avg_transported'

      Additional fields can be added to this dictionary as needed to support
      custom performance measures,graph generation, or batch criteria as
      needed. See :ref:`ln-platform-argos-bc-saa-noise-yaml-config` for an
      example of adding fields to this dictionary as a lookup table of sorts for
      a broader range of cmdline configuration (i.e., using it to make the
      cmdline syntax for the `ln-platform-argos-bc-saa-noise` much nicer).

   .. tab:: ``config/controllers.yaml``

      Configuration for robot controllers.

      Root level dictionaries: varies; project dependent. Each root level
      dictionary is treated as the name of a :term:`Controller Category` when
      ``--controller`` is parsed. For example, if you pass
      ``--controller=mycategory.FizzBuzz`` to SIERRA, then you need to have a
      root level dictionary ``mycategory`` defined in ``controllers.yaml``.

      A complete YAML configuration for a :term:`Controller Category`
      ``mycategory`` and a controller ``FizzBuzz`` is shown below, separated by
      platform. This configuration specifies that all graphs in the categories
      of ``LN_MyCategory1``, ``LN_MyCategory2``, ``HM_MyCategory1``,
      ``HM_MyCategory2`` are applicable to ``FizzBuzz``, and should be generated
      if the necessary :term:`Experiment` output files exist. The
      ``LN_MyCategory1``, ``LN_MyCategory2`` graph categories are common to
      multiple controllers in this project, while the ``HM_MyCategory1``,
      ``HM_MyCategory2`` :term:`graph categories<Graph Category>` are specific
      to the ``FizzBuzz`` controller.

      .. tabs::

         .. code-tab:: YAML ARGoS

            my_base_graphs:
              - LN_MyCategory1
              - LN_MyCategory2

            mycategory:

              # Changes to existing XML attributes in the template ``.argos``
              # file for *all* controllers in the category, OR changes to
              # existing tags for *all* controllers in the template ``.xml``
              # file.  This is usually things like setting ARGoS loop functions
              # appropriately, if required. Each change is formatted as a list
              # with paths to parent tags specified in the XPath syntax.
              #
              # - [parent tag, attr, value] for changes to existing XML
              #   attributes.
              #
              # - [parent tag, child tag, value] for changes to existing tags
              #
              # - [parent tag, child tag, attr] for adding new tags. When adding
              #   tags the attr string is passed to eval() to turn it into a
              #   python dictionary.
              #
              # The ``xml`` section and subsections are optional. If
              # ``--platform-vc`` is passed, then this section should be used to
              # specify any changes to the XML needed to setup the selected
              # platform for frame capture/video rendering by specifying the QT
              # visualization functions to use.
              xml:
                tag_change:
                  - ['.//loop-functions/parent', 'child', 'stepchild']
                attr_change:
                  - ['.//loop-functions', 'label', 'my_category_loop_functions']
                  - ['.//qt-opengl/user_functions', 'label', 'my_category_qt_loop_functions']
                tag_add:
                  - ...
                  - ...

              # Under ``controllers`` is a list of controllers which can be
              # passed as part of ``--controller`` when invoking SIERRA, matched
              # by ``name``. Any controller-specific XML attribute changes can
              # be specified here, with the same syntax as the changes for the
              # controller category (``mycategory`` in this example). As above,
              # you can specify sets of changes to existing XML attributes,
              # changes to existing XML tags to set things up for a specific
              # controller, or adding new XML tags.
              controllers:
                - name: FizzBuzz
                  xml:
                    attr_change:

                      # The ``__CONTROLLER__`` tag in the
                      # ``--template-input-file`` is REQUIRED to allow SIERRA to
                      # unambiguously set the "library" attribute of the
                      # controller.
                      - ['.//controllers', '__CONTROLLER__', 'FizzBuzz']


                  # Sets of graphs common to multiple controller categories can
                  # be inherited with the ``graphs_inherit`` dictionary (they
                  # are added to the ``graphs`` dictionary). This dictionary is
                  # optional, but handy to reduce repetitive declarations and
                  # typing. see the YAML docs for details on how to include
                  # named lists inside other lists.
                  graphs_inherit:
                    - *my_base_graphs

                  # Specifies a list of graph categories from inter- or
                  # intra-experiment ``.yaml`` configuration which should be
                  # generated for this controller, if the necessary input .csv
                  # files exist.
                  graphs: &FizzBuzz_graphs
                    - HM_MyCategory1
                    - HM_MyCategory2

         .. code-tab:: YAML ROS+Gazebo

            my_base_graphs:
              - LN_MyCategory1
              - LN_MyCategory2

            mycategory:
              # Changes to existing XML attributes in the template ``.launch``
              # file for *all* controllers in the category, OR changes to
              # existing tags for *all* controllers in the template ``.launch``
              # file.  Each change is formatted as a list with paths to parent
              # tags specified in the XPath syntax.
              #
              # - [parent tag, attr, value] for changes to existing XML
              #   attributes.
              #
              # - [parent tag, child tag, value] for changes to existing tags
              #
              # - [parent tag, child tag, attr] for adding new tags. When adding
              #   tags the attr string is passed to eval() to turn it into a
              #   python dictionary.
              #
              # The ``xml`` section and subsections are optional. If
              # ``--platform-vc`` is passed, then this section should be used to
              # specify any changes to the XML needed to setup ROS+Gazebo for
              # visual capture.
              #
              # When adding new tags the ``__UUID__`` string can be included in
              # the parent tag or child tag fields, which has two
              # effects. First, it is expanded to the robot prefix (namespace in
              # ROS terminology) + the robot's ID to form a UUID for the
              # robot. Second, the tag is added not just once overall, but once
              # for each robot in each experimental run. This is useful to set
              # per-robot parameters specific to a given controller outside of
              # the parameters controller via batch criteria or SIERRA
              # variables (e.g., launching nodes to bringup sensors on the
              # robot that are not launched by default/by the controller entry
              # point).
              xml:
                tag_change:
                  - ...
                attr_change:
                  - ...
                tag_add:
                  - ...

              # Under ``controllers`` is a list of controllers which can be
              # passed as part of ``--controller`` when invoking SIERRA, matched
              # by ``name``. Any controller-specific XML attribute changes can
              # be specified here, with the same syntax as the changes for the
              # controller category (``mycategory`` in this example). As above,
              # you can specify sets of changes to existing XML attributes,
              # changes to existing XML tags to set things up for a specific
              # controller, or adding new XML tags.
              #
              # When adding new tags the ``__UUID__`` string can be included in
              # the parent tag or child tag fields, which has two
              # effects. First, it is expanded to the robot prefix (namespace in
              # ROS terminology) + the robot's ID to form a UUID for the
              # robot. Second, the tag is added not just once overall, but once
              # for each robot in each experimental run. This is useful to set
              # per-robot parameters specific to a given controller outside of
              # the parameters controller via batch criteria or SIERRA variables
              # (e.g., launching nodes to bringup sensors on the robot that are
              # not launched by default/by the controller entry point).
              controllers:
                - name: FizzBuzz
                  xml:
                    tag_add:
                      - [".//launch/group/[@ns='__UUID__']", 'param', "{'name': 'topic_name', 'value':'mytopic'}"]



                  # Sets of graphs common to multiple controller categories can
                  # be inherited with the ``graphs_inherit`` dictionary (they
                  # are added to the ``graphs`` dictionary). This dictionary is
                  # optional, but handy to reduce repetitive declarations and
                  # typing. see the YAML docs for details on how to include
                  # named lists inside other lists.
                  graphs_inherit:
                    - *my_base_graphs

                  # Specifies a list of graph categories from inter- or
                  # intra-experiment ``.yaml`` configuration which should be
                  # generated for this controller, if the necessary input .csv
                  # files exist.
                  graphs: &FizzBuzz_graphs
                    - HM_MyCategory1
                    - HM_MyCategory2

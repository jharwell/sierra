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

   .. group-tab:: ROS1+Gazebo

      An example main configuration file for the ROS1+Gazebo platform:

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


   .. group-tab:: ROS1+Robot

      An example main configuration file for the ROS1+Robot platform:

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
            turtlebot3:
              # The robot prefix which will be prepended to the robot's
              # numeric ID to form its UUID. E.g., for robot 14, its UUID
              # will be <prefix>14. This is used by SIERRA to create
              # unique namespaces for each robot's nodes so that all their
              # ROS topics are unique (if desired).
              prefix: "tb3_"

              # The name of the setup script to source on login to each
              # robot to setup the ROS environment. This key is optional.
              setup_script: "$HOME/setup.bash"

            myrobot2:
              ...




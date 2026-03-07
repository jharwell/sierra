.. _plugins/engine:

=================
Engine (--engine)
=================

SIERRA supports a number of :term:`engines <Engine>`, all of which can be
used transparently for running experiments; well, transparent from SIERRA's
point of view; you probably will still have to make code modifications to switch
between engines.

.. toctree::
   :maxdepth: 2

   argos/index
   ros1gazebo/index
   ros1robot/index


Additional engines can be supported via :ref:`tutorials/plugins/engine`.

ROS1-based Engines
==================

Requirements
------------

#. All robot systems are homogeneous (i.e., only contain 1 type of robot). While
   SIERRA does not currently support multiple types of robots in ROS, adding
   support for doing so would not be difficult.

#. Since SIERRA operates on a single template input file
   (:ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>`)
   when generating experimental definitions, all XML parameters you want to be
   able to modify with SIERRA must be present in a single ``.launch``
   file. Other parameters you don't want to modify with SIERRA can be present in
   other ``.launch`` or ``.world`` files, and using the usual ``<include>``
   mechanism. See also :ref:`concepts/philosophy`.

#. Within the template ``.launch`` file
   (:ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>`),
   the root XML tag must be ``<ros-configuration>`` . The
   ``<ros-configuration>`` tag is stripped out by SIERRA during generation, and
   exists solely for the purposes of conformance with the XML standard, which
   states that there can be only a single root element (i.e., you can't have a
   ``<params>`` element and a ``<launch>`` element both at the root level--see
   options below). See :ref:`plugins/expdef` for details of required structure
   of passed ``--expdef-template``, and what changes are applied to them by
   SIERRA to use with ROS.

   :term:`Projects <Project>` can choose either of the following options for
   specifying controller parameters. See :ref:`plugins/expdef` for further
   details of required structure of passed
   :ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>`, and
   what changes are applied to them by SIERRA to use with ROS, depending on the
   option chosen.

      - Use the ROS Parameter Server

        All parameters are specified as you would expect under ``<launch>``.

        .. WARNING:: Using the ROS parameter server is generally discouraged for
                     projects which have LOTS of parameters, because
                     manipulating the XML becomes non-trivial, and can require
                     extensive XPath knowledge (e.g.,
                     ``//launch/group/[@ns='{ns}']``). For smaller projects it's
                     generally fine.

      - Use the ``<params>`` tag under ``<ros-configuration>`` to specify an XML
        tree of controller parameters.

        This is recommended for large projects, as it allows cleaner XPath
        specifications (e.g., ``.//params/task_alloc/mymethod/threshold``). For
        projects using an XML-based simulator (e.g., :term:`ARGoS`) for
        simulations and a ROS engine for real robots, using a separate
        parameter XML subtree maximizes code reuse. During stage 1 the modified
        ``<params>`` sub-tree is removed from the written ``.launch`` file if it
        exists and written to a *different* file in the same directory as the
        ``.launch`` file.

        All SIERRA configuration exposed via XML parameters use the ROS
        parameter server. See :ref:`plugins/expdef` for specifics.

#. ROS does not currently provide a way to shut down after a given # of
   iterations/timesteps, so SIERRA provides a ROS package with a node tracking
   the elapsed time in seconds, and which exits (and takes down the roslaunch
   when it does) after the specified experiment time has elapsed. This node is
   inserted into all ``.launch`` files. All ROS projects must depend on this
   `ROS bridge <https://github.com/jharwell/sierra_rosbridge>`_
   package so the necessary nodes can be found by ROS at runtime.

Cmdline Interface
-----------------

.. sphinx_argparse_cli::
   :module: sierra.core.ros1.cmdline
   :func: sphinx_cmdline_multistage
   :prog: sierra-cli

.. sphinx_argparse_cli::
   :module: sierra.core.ros1.cmdline
   :func: sphinx_cmdline_stage1
   :prog: sierra-cli

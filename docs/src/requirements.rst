.. _ln-sierra-req:

==========================
Requirements To Use SIERRA
==========================

This page details the parameters you must meet in order to be able to use SIERRA
in a more or less out-of-the-box fashion. Because SIERRA is highly modular, use
cases which don't meet one or more of the parameters described below can likely
still be accommodated with an appropriate plugin.

.. _ln-sierra-req-OS:

OS Requirements
===============

One of the following:

- Recent linux. SIERRA is tested with Ubuntu 20.04+, though it will probably
  work on less recent versions/other distros as well.

- Recent OSX. SIERRA is tested with OSX 12+, though it *might* work on less
  recent versions.


.. NOTE:: Windows is not supported currently. Not because it can't be supported,
          but because there are not current any platform plugins that which work
          on windows. SIERRA is written in pure python, and could be made to
          work on windows with a little work.

          If windows support would be helpful for your intended usage of SIERRA,
          please get in touch with me.

Python Requirements
===================

Python 3.8+. Tested with 3.8-3.9. It may work for newer versions, probably won't
for older.

.. _ln-sierra-req-exp:

Experimental Definition Requirements
====================================

General
-------

:term:`Experimental Runs<Experimental Run>` within each :term:`Experiment` are
entirely defined by the contents of the ``--template-input-file`` (which is
modified by SIERRA before being written out as one or more input XML files), so
SIERRA restricts the content of this file in a few modest ways.

#. Experimental inputs are specified as a single XML file
   (``--template-input-file``); SIERRA uses this to generate multiple XML input
   files defining :term:`Experiments <Experiment>`. If your experiments use
   require multiple XML input files, you will either have to consolidate them
   all into a single file, or point SIERRA to the "main" file in order to use
   SIERRA to generate experiments from some portion of your experimental
   definitions. As a result of this restriction, all experiments must read their
   definition from XML.

   XML was chosen over other input formats because:

   - It is not dependent on whitespace/tab/spaces for correctness, making it
     more robust to multiple platforms, simulators, parsers, users, etc.

   - Mature manipulation libraries exist for python and C++, so it should be
     relatively straightforward for projects to read experimental definitions
     from XML.

#. No reserved XML tokens are present. See :ref:`ln-sierra-req-xml` for details.

#. All experiments from which you want to generate statistics/graphs are:

   - The same length

   - Capture the same number of datapoints

   That is, experiments always obey ``--exp-setup``, regardless if early
   stopping conditions are met. For :term:`ROS1` platforms, the SIERRA
   timekeeper ensures that all experiments are the same length; it is up to you
   to make sure all experiments capture the same # of data points. For other
   :term:`Platforms <Platform>` (e.g., :term:`ARGoS`) it is up to you to ensure
   both conditions.

   This is a necessary restriction for deterministic and non-surprising
   statistics generation during stage 3. Pandas (the underlying data processing
   library) can of course handle averaging/calculating statistics from
   dataframes of different sizes (corresponding to experiments which had
   different lengths), but the generated statistics may not be as
   reliable/meaningful. For example, if you are interested in the steady state
   behavior of the system, then you might want to use the `last` datapoint in a
   given column as a performance measure, averaged across all experiments. If
   not all experiments have the same # of datapoints/same length, then the
   resulting confidence intervals around the average value (for example) may be
   larger.

   If you need to "stop" an experiment early, simply tell all agents/robots to
   stop moving/stop doing stuff once the stopping conditions have been met and
   continue to collect data as you normally would until the end of the
   experiment.

   If you do **NOT** want to use SIERRA to generate statistics/graphs from
   experimental data (e.g., you want to use it to capture videos only), then you
   can ignore this requirement.

:term:`Platforms <Platform>` may have additional experiment requirements, as
shown below.

.. _ln-sierra-req-exp-argos:

:term:`ARGoS` Platform
----------------------

#. All swarms are homogeneous (i.e., only contain 1 type of robot) if the size
   of the swarm changes across experiments (e.g., 1 robot in exp0, 2 in exp1,
   etc.). While SIERRA does not currently support multiple types of robots with
   varying swarm sizes, adding support for doing so would not be difficult. As a
   result, SIERRA assumes that the type of the robots you want to use is already
   set in the template input file (e.g., ``<entity/foot-bot>``) when using
   SIERRA to change the swarm size.

#. The distribution method via ``<distribute>`` in the ``.argos`` file is the
   same for all robots, and therefore only one such tag exists (not checked).

#. The ``<XXX_controller>`` tag representing the configuration for the
   ``--controller`` you want to use does not exist verbatim in the
   ``--template-input-file``. Instead, a placeholder ``__CONTROLLER__`` is used
   so that SIERRA can unambiguously set the "library" attribute of the
   controller; the ``__CONTROLLER__`` tag will replaced with the ARGoS name of
   the controller you selected via ``--controller`` specified in the
   ``controllers.yaml`` configuration file by SIERRA. You should have something
   like this in your template input file:

   .. code-block:: XML

      <argos-configuration>
         ...
         <controllers>
            ...
            <__CONTROLLER__>
               <param_set1>
                  ...
               </param_set1>
               ...
            <__CONTROLLER__/>
            ...
         </controllers>
         ...
      </argos-configuration>

   See also :ref:`ln-sierra-tutorials-project-main-config`.

:term:`ROS1`-based Platforms
----------------------------

These requirements apply to any :term:`Platform` which uses :term:`ROS1` (e.g.,
:term:`ROS1+Gazebo`, :term:`ROS1+Robot`).

#. All robot systems are homogeneous (i.e., only contain 1 type of robot). While
   SIERRA does not currently support multiple types of robots in ROS, adding
   support for doing so would not be difficult.

#. Since SIERRA operates on a single template input file
   (``--template-input-file``) when generating experimental definitions, all XML
   parameters you want to be able to modify with SIERRA must be present in a
   single ``.launch`` file. Other parameters you don't want to modify with
   SIERRA can be present in other ``.launch`` or ``.world`` files, and using the
   usual ``<include>`` mechanism. See also :ref:`ln-sierra-philosophy`.

#. Within the template ``.launch`` file (``--template-input-file``), the root
   XML tag must be ``<ros-configuration>`` . The
   ``<ros-configuration>`` tag is stripped out by SIERRA during
   generation, and exists solely for the purposes of conformance with the XML
   standard, which states that there can be only a single root element (i.e.,
   you can't have a ``<params>`` element and a ``<launch>`` element both at the
   root level--see options below). See
   :ref:`ln-sierra-tutorials-project-template-input-file` for details of required
   structure of passed ``--template-input-file``, and what changes are applied
   to them by SIERRA to use with ROS.

   :term:`Projects <Project>` can choose either of the following options for
   specifying controller parameters. See
   :ref:`ln-sierra-tutorials-project-template-input-file` for further details of
   required structure of passed ``--template-input-file``, and what changes are
   applied to them by SIERRA to use with ROS, depending on the option chosen.

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
        specifications (e.g., ``.//params/task_alloc/mymethod/threshold``), and
        for those which use :term:`ARGoS` for simulations and a ROS platform for
        real robots, as it maximizes code reuse. During stage 1 the modified
        ``<params>`` sub-tree is removed from the written ``.launch`` file if it
        exists and written to a `different` file in the same directory as the
        ``.launch`` file.

        All SIERRA configuration exposed via XML parameters uses the ROS
        parameter server. See :ref:`ln-sierra-tutorials-project-template-input-file`
        for specifics.

#. ROS does not currently provide a way to shut down after a given # of
   iterations/timesteps, so SIERRA provides a ROS package with a node tracking
   the elapsed time in seconds, and which exits (and takes down the roslaunch
   when it does) after the specified experiment time has elapsed. This node is
   inserted into all ``.launch`` files. All ROS projects must depend on this
   `ROS bridge <https://github.com/jharwell/sierra_rosbridge>`_
   package so the necessary nodes can be found by ROS at runtime.


Additional Platform Requirements
================================

:term:`ROS1+Robot` Platform
---------------------------

#. All data from multiple robots somehow ends up accessible through the
   filesystem on the host machine SIERRA is invoked on, as if the same
   experimental run was locally with a simulator. There are several ways to
   accomplish this:

   - Use SIERRA's ability to configure a "master" node on the host machine, and
     then setup streaming of robot data via ROS messages to this master
     node. Received data is processed as appropriate and then written out to the
     local filesystem so that it is ready for statistics generation during
     stage 3.

     .. IMPORTANT:: If you use this method, then you will need to handle robots
                    starting execution at slightly different times in your code
                    via (a) a start barrier triggered from the master node, or
                    else timestamp the data from robots and marshal it on the
                    master node in some fashion. The :ref:`SIERRA ROSBridge
                    <ln-sierra-packages-rosbridge>` provides some support for (a).

   - Mount a shared directory on each robot where it can write its data, and
     then after execution finishes but before your code exits you process the
     per-robot data if needed so it is ready for statistics generation during
     stage 3.

   - Record some/all messages sent and received via one or more ROSbag files,
     and then post-process these files into a set of dataframes which are
     written out to the local filesystem.

   - Record some/all messages sent and received via one or more ROSbag files,
     and use these files directly as a "database" to query during stage 3. This
     would require writing a SIERRA storage plugin (see
     :ref:`ln-sierra-tutorials-plugin-storage`).

     .. IMPORTANT:: This method requires that whatever is recorded into the
                    ROSbag file is per-run, not per-robot; that is, if a given
                    data source somehow built from messages sent from multiple
                    robots, those messages need to be processed/averaged/etc and
                    then sent to a dedicated topic to be recorded.


.. _ln-sierra-req-code:

Requirements For Project Code
=============================

General
-------

SIERRA makes a few assumptions about how :term:`Experimental Runs<Experimental
Run>` using your C/C++ library can be launched, and how they output data. If
your code does not meet these assumptions, then you will need to make some
(hopefully minor) modifications to it before you can use it with SIERRA.

#. Project code uses a configurable random seed. While this is not technically
   `required` for use with SIERRA, all research code should do this for
   reproducibility. See :ref:`ln-sierra-platform-plugins` for platform-specific
   details about random seeding and usage with SIERRA.

#. :term:`Experimental Runs<Experimental Run>` can be launched from `any`
   directory; that is, they do not require to be launched from the root of the
   code repository (for example).

#. All outputs for a single :term:`Experimental Run` will reside in a
   subdirectory in the directory that the run is launched from. For example, if
   a run is launched from ``$HOME/exp/research/simulations/sim1``, then its
   outputs need to appear in a directory such as
   ``$HOME/exp/research/simulations/sim1/outputs``. The directory within the
   experimental run root which SIERRA looks for simulation outputs is configured
   via YAML; see :ref:`ln-sierra-tutorials-project-main-config` for details.

   For HPC execution environments (see :ref:`ln-sierra-exec-env-hpc`), this requirement
   is easy to meet. For real robot execution environments
   (see :ref:`ln-sierra-exec-env-robot`), this can be more difficult to meet.

#. All experimental run outputs are in a format that SIERRA understands within
   the output directory for the run. See :ref:`ln-sierra-storage-plugins` for which
   output formats are currently understood by SIERRA. If your output format is
   not in the list, never fear! It's easy to create a new storage plugin, see
   :ref:`ln-sierra-tutorials-plugin-storage`.

ARGoS Platform
--------------

#. ``--project`` matches the name of the C++ library for the project
   (i.e. ``--project.so``), unless ``library_name`` is present in
   ``sierra.main.run`` YAML config. See :ref:`ln-sierra-tutorials-project-main-config`
   for details. For example if you pass ``--project=project-awesome``, then
   SIERRA will tell ARGoS to search in ``proj-awesome.so`` for both loop
   function and controller definitions via XML changes, unless you specify
   otherwise in project configuration. You *cannot* put the
   loop function/controller definitions in different libraries.

#. :envvar:`ARGOS_PLUGIN_PATH` is set up properly prior to invoking SIERRA.

ROS1+Gazebo Project Platform
----------------------------

#. :envvar:`ROS_PACKAGE_PATH` is set up properly prior to invoking SIERRA.

.. _ln-sierra-req-code-ros1robot:

ROS1+Robot Platform
-------------------

#. :envvar:`ROS_PACKAGE_PATH` is set up properly prior to invoking SIERRA on the
   local machine AND all robots are setup such that it is populated on login
   (e.g., an appropriate ``setup.bash`` is sourced in ``.bashrc``).

#. All robots have :envvar:`ROS_IP` or :envvar:`ROS_HOSTNAME` populated, or
   otherwise can correctly report their address to the ROS master. You can
   verify this by trying to launch a ROS master on each robot: if it launches
   without errors, then these values are setup properly.

.. _ln-sierra-req-models:

============================
Model Framework Requirements
============================

When running models during stage 4 (see
:ref:`ln-sierra-tutorials-project-models`) SIERRA requires that:

- All models return :class:`pandas.DataFrame` (if they don't do this natively,
  then their python bindings will have to do it). This is enforced by the
  interfaces models must implement.

.. _ln-sierra-req-xml:

XML Content Requirements
========================

Reserved Tokens
---------------

SIERRA uses some special XML tokens during stage 1, and although it is unlikely
that including these tokens would cause problems, because SIERRA looks for them
in `specific` places in the ``--template-input-file``, they should be avoided.

- ``__CONTROLLER__`` - Tag used when as a placeholder for selecting which
  controller present in an input file (if there are multiple) a user wants
  to use for a specific :term:`Experiment`. Can appear in XML attributes. This
  makes auto-population of the controller name based on the ``--controller``
  argument and the contents of ``controllers.yaml`` (see
  :ref:`ln-sierra-tutorials-project-main-config` for details) in template input files
  possible.

- ``__UUID__`` - XPath substitution optionally used when a :term:`ROS1` platform
  is selected in ``controllers.yaml`` (see
  :ref:`ln-sierra-tutorials-project-main-config`) when adding XML tags to force
  addition of the tag once for every robot in the experiment, with ``__UUID__``
  replaced with the configured robot prefix concatenated with its numeric ID
  (0-based). Can appear in XML attributes.

- ``sierra`` - Used when the :term:`ROS1+Gazebo` platform is selected.  Should
  not appear in XML tags or attributes.

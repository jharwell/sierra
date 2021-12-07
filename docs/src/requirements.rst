.. _ln-req:

==========================
Requirements to use SIERRA
==========================

.. _ln-req-exp:

Experiment Requirements
=======================

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

#. No reserved XML tokens are present. See :ref:`ln-req-xml` for details.

:term:`Platforms <Platform>` may have additional experiment requirements, as
shown below.

.. _ln-req-exp-argos:

Experiment Requirements For :term:`ARGoS`
-----------------------------------------

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

   See also :ref:`ln-tutorials-project-main-config`.

Requirements For :term:`ROS-Gazebo`
-----------------------------------

#. All robot systems are homogeneous (i.e., only contain 1 type of robot). While
   SIERRA does not currently support multiple types of robots on ROS/Gazebo,
   adding support for doing so would not be difficult.

#. Worlds within ROS/Gazebo are infinite from the perspective of physics
   engines, even though a finite area shows up in rendering. So, to place robots
   randomly in the arena at the start of simulation across :term:`Experimental
   Runs <Experimental Run>` (if you want to do that) "dimensions" for a given
   world must be specified as part of the ``--scenario`` argument. If you don't
   specify dimensions as part of the ``--scenario`` argument, then you need to
   supply a list of valid robot positions via ``--robot-positions`` which SIERRA
   will choose from randomly for each robot.

#. Since SIERRA operates on a single template input file
   (``--template-input-file``) when generating experimental definitions, all XML
   parameters you want to be able to modify with SIERRA must be present in a
   single ``.launch`` file. Other parameters you don't want to modify with
   SIERRA can be present in other ``.launch`` or ``.world`` files, and using the
   usual ``<include>`` mechanism. See also :ref:`ln-philosophy`.

#. Within the template ``.launch`` file (``--template-input-file``), the root
   XML tag must be ``<rosgazebo-configuration>`` . The
   ``<rosgazebo-configuration>`` tag is stripped out by SIERRA during
   generation, and exists solely for the purposes of conformance with the XML
   standard, which states that there can be only a single root element (i.e.,
   you can't have a ``<params>`` element and a ``<launch>`` element both at the
   root level--see options below). See
   :ref:`ln-tutorials-project-template-input-file` for details of required
   structure of passed ``--template-input-file``, and what changes are applied
   to them by SIERRA to use with ROS.

   :term:`Projects <Project>` can choose either of the following options for
   specifying controller parameters. See
   :ref:`ln-tutorials-project-template-input-file` for further details of
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

      - Use the ``<params>`` tag under ``<rosgazebo-configuration>`` to
        specify an XML tree of controller parameters.

        This is recommended for large projects, as it allows cleaner XPath
        specifications (e.g., ``.//params/task_alloc/mymethod/threshold``), and
        for those which use :term:`ARGoS` for simulations and a ROS platform for
        real robots, as it maximizes code reuse. During stage 1 the modified
        ``<params>`` sub-tree is removed from the written ``.launch`` file if it
        exists and written to a `different` file in the same directory as the
        ``.launch`` file. A single ROS parameter server parameter is inserted
        pointing to this file; see
        :ref:`ln-tutorials-project-template-input-file` for specifics.


#. Gazebo does not currently provide a way to shut down after a given # of
   iterations/timesteps, so SIERRA provides a ROS package with a node tracking
   the elapsed time in seconds, and which exits (and takes down the Gazebo node
   when it does) after the specified experiment time has elapsed. This node is
   inserted into all ``.launch`` files. All ROS projects must depend on this
   `ROS bridge <https://github.com/swarm-robotics/sierra_rosbridge.git>`_
   package so the necessary nodes can be found by ROS at runtime.

.. _ln-req-code:

SIERRA Requirements for Project Code
====================================

SIERRA makes a few assumptions about how :term:`Experimental Runs<Experimental
Run>` using your C++ library can be launched, and how they output data. If your
code does not meet these assumptions, then you will need to make some (hopefully
minor) modifications to it before you can use it with SIERRA.

#. Project code reads its input parameters (well, at least those processed by
   SIERRA) from XML files. See :ref:`ln-philosophy` for a discussion of this
   decision.

#. Project code uses a configurable random seed. While this is not technically
   `required` for use with SIERRA, all research code should do this for
   reproducibility. See :ref:`ln-platform-plugins` for platform-specific details
   about random seeding and usage with SIERRA.

#. :term:`Experimental Runs<Experimental Run>` can be launched from `any`
   directory; that is, they do not require to be launched from the root of the
   code repository (for example).

#. All outputs for a single :term:`Experimental Run` will reside in a
   subdirectory in the directory that the run is launched from. For example, if
   a run is launched from ``$HOME/exp/research/simulations/sim1``, then its
   outputs need to appear in a directory such as
   ``$HOME/exp/research/simulations/sim1/outputs``. The directory within the
   experimental run root which SIERRA looks for simulation outputs is configured
   via YAML; see :ref:`ln-tutorials-project-main-config` for details.

#. All experimental run outputs are in a format that SIERRA understands within
   the output directory for the run. See :ref:`ln-storage-plugins` for which
   output formats are currently understood by SIERRA. If your output format is
   not in the list, never fear! It's easy to create a new storage plugin, see
   :ref:`ln-tutorials-plugin-storage`.

SIERRA Requirements for ARGoS Project Code
------------------------------------------

#. ``--project`` matches the name of the C++ library for the project
   (i.e. ``--project.so``). For example if you pass
   ``--project=project-awesome``, then SIERRA will tell ARGoS to search in
   ``proj-awesome.so`` for both loop function and controller definitions via XML
   changes. You *cannot* put the loop function/controller definitions in
   different libraries.

#. :envvar:`ARGOS_PLUGIN_PATH` is set up properly prior to invoking SIERRA.

SIERRA Requirements for ROS/Gazebo Project Code
-----------------------------------------------

#. :envvar:`ROS_PACKAGE_PATH` is set up properly prior to invoking SIERRA.

.. _ln-req-xml:

SIERRA XML Requirements
=======================

Reserved Tokens
---------------

SIERRA uses some special XML tokens during stage 1, and although it is unlikely
that including these tokens would cause problems, because SIERRA looks for them
in `specific` places in the ``--template-input-file``, they should be avoided.

- ``__CONTROLLER__`` - Tag used when the :term:`ARGoS` :term:`Platform` is
  selected as a placeholder for selecting which controller present in a
  ``.argos`` file (if there are multiple) a user wants to use for a specific
  :term:`Experiment`. Can appear in XML attributes. This makes auto-population
  of the controller name based on the ``--controller`` argument and the contents
  of ``controllers.yaml`` (see :ref:`ln-tutorials-project-main-config` for
  details) in template input files possible.

- ``__UUID__`` - XPath substitution optionally used when the :term:`ROS-Gazebo`
  platform is selected in ``controllers.yaml`` (see
  :ref:`ln-tutorials-project-main-config`) when adding XML tags to force
  addition of the tag once for every robot in the experiment, with ``__UUID__``
  replaced with the configured robot prefix concatenated with its numeric ID
  (0-based). Can appear in XML attributes.

- ``sierra`` - Used when the :term:`ROS-Gazebo` platform is selected.  Should
  not appear in XML tags or attributes.
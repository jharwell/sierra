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
   ``--expdef-template``. Instead, a placeholder ``__CONTROLLER__`` is used
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

   See also :ref:`tutorials/project/config`.

#. ``--project`` matches the name of the C++ library for the project
   (i.e. ``--project.so``), unless ``library_name`` is present in
   ``sierra.main.run`` YAML config. See :ref:`tutorials/project/config` for
   details. For example if you pass ``--project=project-awesome``, then SIERRA
   will tell ARGoS to search in ``project-awesome.so`` for both loop function
   and controller definitions via XML changes, unless you specify otherwise in
   project configuration. You *cannot* put the loop function/controller
   definitions in different libraries.

#. :envvar:`ARGOS_PLUGIN_PATH` is set up properly prior to invoking SIERRA.

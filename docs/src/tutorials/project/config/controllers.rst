.. _tutorials/project/config/controllers:

=======================
config/controllers.yaml
=======================


Configuration for robot controllers. Optional. If this config file is present,
arguments to ``--controller`` must conform to the following schema::

  CATEGORY.TYPE

Both ``CATEGORY`` and ``TYPE`` are arbitrary strings, but must both be present
and separated by a ``.``. If the config file is not present, then arguments to
``--controller`` can be anything. This config file serves two purposes:

- Allows users to declare "simple" changes which should be applied to the
  ``--expdef-template`` dependent on the value of ``--controller``. If you need
  to do more complex things, see :ref:`tutorials/project/generators`.

- Allows users to declare what types of :ref:`products <plugins/prod>` should be
  considered for generation based on the value of ``--controller``).

This config file should contain project-dependent root-level dictionaries. Each
root-level dictionary is treated as the name of a :term:`Controller Category`
when ``--controller`` is parsed. For example, if you pass
``--controller=mycategory.FizzBuzz`` to SIERRA, then you need to have a root
level dictionary ``mycategory`` defined in ``controllers.yaml``.

.. _tutorials/project/config/controllers/blocks:

Special Block
=============

Each controller category and each individual controller may define any number of
{xml,json,yaml} blocks specifying changes to apply to the
:ref:`--expdef-template<src/reference/cli:sierra---expdef-template>`. Three
subsection keys are supported, each taking a list of three-element lists:

``attr_change``
   Modify an existing attribute. Format: ``[path, attr, value]`` where
   ``path`` is an expression for the **parent** element, ``attr`` is
   the attribute name, and ``value`` is the new value as a string.

``element_change``
   Modify an existing child element. Format: ``[path, child_tag, value]``.

``element_add``
   Add a new child element. Format: ``[path, child_tag, attr_dict]`` where
   ``attr_dict`` is a string passed to ``eval()`` to produce a Python
   dictionary of attribute names and values for the new element.

All three subsections are optional. The path syntax in each list entry depends
on your template format: XPath for XML, JSONPath for JSON, YAMLPath for YAML.
See :ref:`tutorials/plugins/expdef/format-restrictions` for the full format
reference.

.. _tutorials/project/config/controllers/tokens:

Special Tokens in ``controllers.yaml``
======================================

Two special tokens can appear in ``controllers.yaml`` path expressions and
values, regardless of template format. See
:ref:`tutorials/plugins/expdef/tokens` for their full definitions.

``__CONTROLLER__``
   Used in ``attr_change`` entries to target the controller element in the
   template. SIERRA replaces it with the resolved controller name regardless
   of template format. For XML templates (including ARGoS ``.argos`` files),
   the path expression uses XPath; for JSON/YAML templates it uses the
   equivalent path syntax for that format.

   The standard ARGoS entry:

   .. code-block:: yaml

      attr_change:
        - ['.//controllers', '__CONTROLLER__', 'MyControllerName']

   This is **required** for ARGoS projects to allow SIERRA to unambiguously
   set the controller's ``library`` attribute. JSON/YAML projects should use
   the equivalent JSONPath or YAMLPath expression for their controller key.

``__UUID__``
   Available in ROS1 ``.launch`` templates only. When ``__UUID__`` appears in
   an XPath expression inside ``element_add``, the tag is added once per robot
   (not once overall), with ``__UUID__`` expanded to the robot's namespace
   prefix and numeric ID. Use this to set per-robot parameters that cannot be
   controlled through batch criteria.

A complete ``controllers.yaml`` configuration is shown below, separated by
engine:

.. tab-set::

   .. tab-item:: ARGoS

      .. code-block:: YAML

         my_base_graphs:
           - LN_MyCategory1
           - LN_MyCategory2

         mycategory:

           # Optional: changes applied to the template for *all* controllers
           # in this category (e.g. setting ARGoS loop functions, or QT
           # visualization functions when --engine-vc is passed).
           xml:
             element_change:
               - ['.//loop-functions/parent', 'child', 'stepchild']
             attr_change:
               - ['.//loop-functions', 'label', 'my_category_loop_functions']
               - ['.//qt-opengl/user_functions', 'label', 'my_category_qt_loop_functions']
             element_add:
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
                   - ['.//controllers', '__CONTROLLER__', 'FizzBuzz']

               # Optional: inherit graph categories common to multiple controllers.
               graphs_inherit:
                 - *my_base_graphs

               # Graph categories to generate for this controller if the
               # necessary output CSVs exist.
               graphs: &FizzBuzz_graphs
                 - HM_MyCategory1
                 - HM_MyCategory2

   .. tab-item:: ROS1+Gazebo and ROS1+Robot

      .. code-block:: YAML

        my_base_graphs:
          - LN_MyCategory1
          - LN_MyCategory2

        mycategory:

          # Optional: changes applied to the template for *all* controllers
          # in this category. For ROS1+Gazebo, also use this to specify
          # changes needed for visual capture when --engine-vc is passed.
          xml:
            element_change:
              - ...
            attr_change:
              - ...
            element_add:
              - ...

          controllers:
            - name: FizzBuzz
              xml:
                element_add:
                  # __UUID__ causes this tag to be added once per robot,
                  # with __UUID__ expanded to <prefix><robot_id>.
                  - [".//launch/group/[@ns='__UUID__']", 'param', "{'name': 'topic_name', 'value':'mytopic'}"]

              # Optional: inherit graph categories common to multiple controllers.
              graphs_inherit:
                - *my_base_graphs

              # Graph categories to generate for this controller if the
              # necessary output CSVs exist.
              graphs: &FizzBuzz_graphs
                - HM_MyCategory1
                - HM_MyCategory2

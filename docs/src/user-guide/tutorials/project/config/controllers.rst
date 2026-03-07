Configuration for robot controllers. Optional. If this config file is present,
arguments to ``--controller`` must conform to the following schema::

  CATEGORY.TYPE

Both ``CATEGORY`` and ``TYPE`` are arbitrary strings, but must both be present
and separated by a ``.``. If the config file is not present, then arguments to
``--controller`` can be anything. This config file serves two purposes:

- Allows users to declare "simple" changes which should be applied to the
  ``--expdef`` dependent on the value of ``--controller``. If you need to do
  fancy things, see :ref:`tutorials/project/generators`.

- Allows users to declare what types of :ref:`products <plugins/prod>` should be
  considered for generation based on the value of ``--controller``.

This config file should contain project dependent root-level dictionaries. Each
root level dictionary is treated as the name of a :term:`Controller Category`
when ``--controller`` is parsed. For example, if you pass
``--controller=mycategory.FizzBuzz`` to SIERRA, then you need to have a root
level dictionary ``mycategory`` defined in ``controllers.yaml``.

A complete YAML configuration for a :term:`Controller Category`
``mycategory`` and a controller ``FizzBuzz`` is shown below, separated by
engine. This configuration specifies that all graphs in the categories
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
        # ``--engine-vc`` is passed, then this section should be used to
        # specify any changes to the XML needed to setup the selected
        # engine for frame capture/video rendering by specifying the QT
        # visualization functions to use.
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

                # The ``__CONTROLLER__`` tag in the
                # ``--expdef-template`` is REQUIRED to allow SIERRA to
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
            # generated for this controller, if the necessary input CSV
            # files exist.
            graphs: &FizzBuzz_graphs
              - HM_MyCategory1
              - HM_MyCategory2

   .. code-tab:: YAML ROS1+Gazebo and ROS1+Robot

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
        # ``--engine-vc`` is passed, then this section should be used to
        # specify any changes to the XML needed to setup ROS1+Gazebo for
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
          element_change:
            - ...
          attr_change:
            - ...
          element_add:
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
              element_add:
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
            # generated for this controller, if the necessary input CSV
            # files exist.
            graphs: &FizzBuzz_graphs
              - HM_MyCategory1
              - HM_MyCategory2

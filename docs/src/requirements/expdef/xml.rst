SIERRA uses some special XML tokens during stage 1, and although it is unlikely
that including these tokens would cause problems, because SIERRA looks for them
in *specific* places in the ``--expdef-template``, they should be avoided.

- ``__CONTROLLER__`` - Tag used when as a placeholder for selecting which
  controller present in an input file (if there are multiple) a user wants to
  use for a specific :term:`Experiment`. Can appear in XML attributes. This
  makes auto-population of the controller name based on the ``--controller``
  argument and the contents of ``controllers.yaml`` (see
  :ref:`tutorials/project/config` for details) in template input
  files possible.

- ``__UUID__`` - XPath substitution optionally used when a :term:`ROS1` engine
  is selected in ``controllers.yaml`` (see :ref:`tutorials/project/config`) when
  adding XML tags to force addition of the tag once for every robot in the
  experiment, with ``__UUID__`` replaced with the configured robot prefix
  concatenated with its numeric ID (0-based). Can appear in XML attributes.

- ``sierra`` - Used when the :term:`ROS1+Gazebo` engine is selected.  Should
  not appear in XML tags or attributes.

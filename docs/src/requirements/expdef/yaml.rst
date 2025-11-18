- ``__CONTROLLER__`` - Tag used when as a placeholder for selecting which
  controller present in an input file (if there are multiple) a user wants to
  use for a specific :term:`Experiment`. Can appear in YAML attributes. This
  makes auto-population of the controller name based on the ``--controller``
  argument and the contents of ``controllers.yaml`` (see
  :ref:`tutorials/project/config` for details) in template input files possible.

Furthermore, while YAML treats keys mapping to subtrees and keys mapping to
literal attributes equivalently, SIERRA does not, in order to provide uniformity
across the different input file types it can handle. Functionally this means
that if you ask SIERRA to update an attribute for a literal/scalar, and that
"attribute" actually maps to a sub-tree, you will get an error, even though
making a change of that nature is a perfectly valid YAML modification.

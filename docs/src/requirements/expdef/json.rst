.. SPDX-License-Identifier:  MIT

SIERRA uses some special JSON tokens during stage 1, and although it is unlikely
that including these tokens would cause problems, because SIERRA looks for them
in *specific* places in the ``--expdef-template``, they should be avoided.

- ``__CONTROLLER__`` - Tag used when as a placeholder for selecting which
  controller present in an input file (if there are multiple) a user wants to
  use for a specific :term:`Experiment`. Can appear in JSON attributes. This
  makes auto-population of the controller name based on the ``--controller``
  argument and the contents of ``controllers.yaml`` (see
  :ref:`tutorials/project/config` for details) in template input files possible.


Furthermore, while JSON treats keys mapping to subtrees and keys mapping to
literal attributes equivalently, SIERRA does not, in order to provide uniformity
across the different input file types it can handle. Functionally this means
that if you ask SIERRA to update an attribute for a file, and that "attribute"
actually maps to a sub-tree, you will get an error, even though making a change
of that nature is a perfectly valid JSON modification.

.. _ln-cli:

Command Line Interface
======================

Core
----

Unless an option says otherwise, it is applicable to all batch criteria. That
is, option batch criteria applicability is only documented for options which
apply to a subset of the available :ref:`Batch Criteria <ln-batch-criteria>`.

.. argparse::
   :filename: ../sierra//core/cmdline.py
   :func: sphinx_cmdline_bootstrap
   :prog: cmdline.py

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_core
   :prog: cmdline.py

FORDYCA Project Command Line Extensions
---------------------------------------

.. argparse::
   :filename: ../projects/fordyca/cmdline.py
   :func: sphinx_cmdline
   :prog: cmdline.py

SILICON Project Command Line Extensions
---------------------------------------

.. argparse::
   :filename: ../projects/silicon/cmdline.py
   :func: sphinx_cmdline
   :prog: cmdline.py

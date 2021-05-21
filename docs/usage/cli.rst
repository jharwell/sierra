.. _ln-cli:

Command Line Interface
======================

Unless an option says otherwise, it is applicable to all batch criteria. That
is, option batch criteria applicability is only documented for options which
apply to a subset of the available :ref:`Batch Criteria <ln-batch-criteria>`.

General Options
---------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra

Stage1
------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra

Stage2
------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage2
   :prog: sierra


Stage3
------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage3
   :prog: sierra


Stage4
------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage4
   :prog: sierra

Stage1
------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage5
   :prog: sierra


FORDYCA Project Command Line Extensions
---------------------------------------

.. argparse::
   :filename: ../projects/fordyca/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra

.. argparse::
   :filename: ../projects/fordyca/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra

SILICON Project Command Line Extensions
---------------------------------------

.. argparse::
   :filename: ../projects/silicon/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra

.. argparse::
   :filename: ../projects/silicon/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra

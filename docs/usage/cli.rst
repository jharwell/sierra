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

Stage1: Generating Experiments
------------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra

Stage2: Running Experiments
---------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage2
   :prog: sierra


Stage3: Processing Experiment Results
-------------------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage3
   :prog: sierra


Stage4: Deliverable Generation
------------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage4
   :prog: sierra

Stage5: Comparing Controllers
-----------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage5
   :prog: sierra


FORDYCA Project Command Line Extensions
=======================================

General Options
---------------

.. argparse::
   :filename: ../projects/fordyca/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra

Stage1: Generating Experiments
------------------------------

.. argparse::
   :filename: ../projects/fordyca/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra

SILICON Project Command Line Extensions
=======================================

General Options
---------------

.. argparse::
   :filename: ../projects/silicon/cmdline.py
   :func: sphinx_cmdline_multistage
   :prog: sierra

Stage1: Generating Experiments
------------------------------

.. argparse::
   :filename: ../projects/silicon/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: sierra

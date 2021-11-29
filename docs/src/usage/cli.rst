.. _ln-usage-cli:

======================
Command Line Interface
======================

Unless an option says otherwise, it is applicable to all batch criteria. That
is, option batch criteria applicability is only documented for options which
apply to a subset of the available :term:`Batch Criteria`.

If an option is given more than once on the command line, the last such
occurrence is used.

SIERRA Core
===========

These options are for all :term:`Platforms <Platform>`.

Multi-stage Options
-------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_multistage

Stage1: Generating Experiments
------------------------------

None for the moment.

Stage2: Running Experiments
---------------------------

None for the moment.


Stage3: Processing Experiment Results
-------------------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage3
   :prog: SIERRA


Stage4: Deliverable Generation
------------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage4
   :prog: SIERRA

Stage5: Comparing Controllers
-----------------------------

.. argparse::
   :filename: ../sierra/core/cmdline.py
   :func: sphinx_cmdline_stage5
   :prog: SIERRA

ARGoS Platform
==============

These options are enabled if ``--platform=platform.argos`` is passed.

Stage1: Generating Experiments
------------------------------

.. argparse::
   :filename: ../sierra/plugins/platform/argos/cmdline.py
   :func: sphinx_cmdline_stage1
   :prog: SIERRA

Stage2: Running Experiments
---------------------------

.. argparse::
   :filename: ../sierra/plugins/platform/argos/cmdline.py
   :func: sphinx_cmdline_stage2
   :prog: SIERRA

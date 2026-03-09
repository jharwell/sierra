.. _reference/cli:

==================================
SIERRA Core Command Line Reference
==================================

If an option is given more than once, the last such occurrence is
used. If both the shortform and longform variants of an option are passed with
different values, shortform wins.

See also :manpage:`sierra-examples`.

SIERRA Core
===========

These options apply to all :term:`Experiments <Experiment>`, :term:`Engines
<Engine>`, :term:`Batch Criteria`, etc.

Bootstrap Options
-----------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_bootstrap
   :prog: sierra-cli

Multi-stage Options
-------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_multistage


Stage1: Generating Experiments
------------------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage1

Stage2: Running Experiments
---------------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage2


Stage3: Processing Experiment Results
-------------------------------------

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage3


Stage4: Product Generation
--------------------------

None for the moment.

Stage5: Comparing Controllers
-----------------------------

None for the moment.

Plugins
=======

See docs for individual :ref:`plugins` for details.

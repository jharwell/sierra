.. _reference/cli:

===========================
Core Command Line Reference
===========================

If an option is given more than once, the last such occurrence is
used. If both the shortform and longform variants of an option are passed with
different values, shortform wins.

See also :ref:`user-guide/examples`.

SIERRA Core
===========

These options apply to all :term:`Experiments <Experiment>`, :term:`Engines
<Engine>`, :term:`Batch Criteria`, etc.

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_bootstrap
   :prog: sierra
   :title: Bootstrap Options

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_multistage
   :title: Multistage Options

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage1
   :title: Stage1 Options

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage2
   :title: Stage2 Options

.. sphinx_argparse_cli::
   :module: sierra.core.cmdline
   :func: sphinx_cmdline_stage3
   :title: Stage3 Options

Plugins
=======

See docs for individual :ref:`plugins` for details.

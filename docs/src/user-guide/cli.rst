.. _usage/cli:

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

Bootstrap+Multi-stage Options
-----------------------------

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


Stage4: Product Generation
--------------------------

None for the moment.

Stage5: Comparing Controllers
-----------------------------

None for the moment.

Plugins
=======

See docs for individual :ref:`plugins` for details.

These options are for all :term:`Platforms <Platform>`.

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

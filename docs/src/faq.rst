==========
SIERRA FAQ
==========

- Q: Do I need to re-run my experiments if I want to tweak a particular generated
  graph ?

  A: No! Experiment execution happens in stage 2, and graph generation happens
  in stage4. If you just want to add/remove lines from a graph, change the
  title, formatting, etc., you can just tell SIERRA to re-run stage 4 via
  ``--pipeline 4``. See :ref:`ln-usage-pipeline` for more details about pipeline
  stages.

- Q: How to I resume an experiment which got killed part of the way through by
  an HPC scheduler for exceeding its job time limit ?

  A: Run SIERRA just as you did before, but add ``--exec-resume``, which will
  tell SIERRA to pick up where it left off. See :ref:`ln-usage-cli` for the full
  cmdline reference.

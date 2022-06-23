.. _ln-sierra-faq:

===
FAQ
===

#. Q: I'm really confused by all the terminology that SIERRA uses--how can I
   better understand the documentation?

   A: Look at the :doc:`/src/glossary` for all of the terms which SIERRA defines
   specific names for.

#. Q: Do I need to re-run my experiments if I want to tweak a particular
   generated graph ?

   A: No! Experiment execution happens in stage 2, and graph generation happens
   in stage4. If you just want to add/remove lines from a graph, change the
   title, formatting, etc., you can just tell SIERRA to re-run stage 4 via
   ``--pipeline 4``. See :ref:`ln-sierra-usage-pipeline` for more details about
   pipeline stages.

#. Q: How to I resume an experiment which got killed part of the way through by
   an HPC scheduler for exceeding its job time limit ?

   A: Run SIERRA just as you did before, but add ``--exec-resume``, which will
   tell SIERRA to pick up where it left off. See :ref:`ln-sierra-usage-cli` for the full
   cmdline reference.

#. Q: How do I run a non-default set of pipeline stages, such as {3,4}?

   A: ``sierra-cli ... --pipeline 3 4``


   .. IMPORTANT:: If you run something other than ``--pipeline 1 2 3 4``, then
                  before stage X will run without crashing, you (probably) need
                  to run stage X-1. This is a logical limitation, because the
                  different pipeline stages build on each other.

#. Q: How do I prevent SIERRA from stripping out XML tags?

   A: There are 3 options for this: ``--with-robot-leds``, ``--with-robot-rab``,
   and ``--with-robot-battery``. More may be added in the future if needed.

#. Q: SIERRA crashed--why?

   A: The most likely cause of the crash is that stage X-1 of the pipeline did
   not successfully complete before you ran stage X. Pipeline stages build on
   each other, so previously stages need to complete before later stages can
   run.

#. Q: SIERRA hangs during stage {3,4}--why?

   A: The most likely cause is that not all runs generated outputs which
   resulted in ``.csv`` files of the same shape when read into SIERRA. E.g., for
   ``.csv`` file outputs, not all ``.csv`` files with the same name in the
   output directory for each run had the same number of rows and columns. SIERRA
   does not sanitize run outputs before processing them, and relies ``.csv``
   files of the same shape when processing results for generating
   statistics. Depending on the nature of the inconsistency, you may see a
   crash, or you may see it hang indefinitely as it waits for a sub-process
   which crashed to finish.

#. Q: SIERRA fails to run on my HPC environment?

   A: The most likely reason is that you don't have the necessary environment
   variables set up--see :ref:`ln-sierra-exec-env-hpc` for details on what is required.

#. Q: SIERRA doesn't generate any graphs during stage4/the graph I'm interested
   is not there.

   A: SIERRA matches the stem of an output ``.csv`` file with the stem in a
   ``.yaml`` configuration file; if these are not the same, then no graph will
   be generated. You can run SIERRA with ``--log-level=TRACE`` to during stage 4
   to see which graphs it is generating, and which it is not because the
   necessary source ``.csv`` file does not exist. This is usually enough to
   identify the culprit.

#. Q: Stage 3 takes a very long time--why?

   A: SIERRA is conservative, and attempts to verify all the results of all runs
   within each experiment it processes during stage 3, which can be VERY
   computationally intensive, depending on how many outputs are generated for
   each runs. During early experimental runs, this can be helpful to identify
   which runs crashed/did not finish/etc as a result of errors in the project
   C++ library. For later runs, or runs in which you are generating outputs for
   rendering, this is unnecessary, and can be disabled with
   ``--df-skip-verify``.

#. Q: SIERRA does not overwrite the input configuration for my experiment/SIERRA
   won't run my experiments again after they run the first time--why?

   A: This is by design: SIERRA `never ever never` deletes stuff for you in
   stages {1,2} that can result in lost experimental results in later
   stages. The files generated in stages {3,4,5} are generated `from` the
   earlier results, so it is OK to overwrite those. However, if you are sure you
   want to overwrite stuff, you can pass ``--exp-overwrite`` to disable this
   behavior during stages {1,2}. See also :ref:`ln-sierra-philosophy`.

#. Q: I need to apply very precise/nuanced configuration to experiments that is
   too specific to be easily captured in a :term:`Batch Criteria` or other
   variable. How can I do this?

   A: You could create one or more controller categories/controllers in
   ``controllers.yaml``. Within each category *AND* controller, you can specify
   arbitrary changes to the ``--template-input-file``: adding tags, removing
   tags, modifying attributes. This is a good way to apply tricky configuration
   which doesn't really fit anywhere else, or to try out some "quick and dirty"
   changes to see if they do what you want before codifying them with a
   python class. See :ref:`ln-sierra-tutorials-project-main-config` for details.

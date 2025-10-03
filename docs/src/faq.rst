.. _faq:

===
FAQ
===

#. Q: I'm getting an error about the output directory for my simulation run
   being missing--what is wrong? I told SIERRA where outputs should be created
   by following :ref:`tutorials/project/config`.

   A: SIERRA does *not* create the output directory you tell it that all outputs
   for a simulation run will lie under--that is the responsibility of the
   :term:`Engine` and/or :term:`Project`. SIERRA just reads outputs from the
   specified location.

#. Q: I'm really confused by all the terminology that SIERRA uses--how can I
   better understand the documentation?

   A: Look at the :doc:`/src/glossary` for all of the terms which SIERRA defines
   specific names for.

#. Q: Do I need to re-run my experiments if I want to tweak a particular
   generated graph ?

   A: No! Experiment execution happens in stage 2, and graph generation happens
   in stage4. If you just want to add/remove lines from a graph, change the
   title, formatting, etc., you can just tell SIERRA to re-run stage 4 via
   ``--pipeline 4``. See :ref:`usage/pipeline` for more details about
   pipeline stages.

#. Q: How to I resume an experiment which got killed part of the way through by
   an HPC scheduler for exceeding its job time limit ?

   A: Run SIERRA just as you did before, but add ``--exec-resume``, which will
   tell SIERRA to pick up where it left off. See :ref:`usage/cli` for
   more info.

#. Q: How do I run a non-default set of pipeline stages, such as {3,4}?

   A: ``sierra-cli ... --pipeline 3 4``


   .. IMPORTANT:: If you run something other than ``--pipeline 1 2 3 4``, then
                  before stage X will run without crashing, you (probably) need
                  to run stage X-1. This is a logical limitation, because the
                  different pipeline stages build on each other.

#. Q: How do I prevent SIERRA from stripping out ARGoS XML tags for
   sensors/actuators?

   A: There are 3 options for this: ``--with-robot-leds``, ``--with-robot-rab``,
   and ``--with-robot-battery``. More may be added in the future if needed.

#. Q: SIERRA crashed--why?

   A: The most likely cause of the crash is that stage X-1 of the pipeline did
   not successfully complete before you ran stage X. Pipeline stages build on
   each other, so previously stages need to complete before later stages can
   run.

#. Q: SIERRA hangs during stage {3,4}--why?

   A: The most likely cause is that not all runs generated outputs which
   resulted in CSV files of the same shape when read into SIERRA. E.g., for CSV
   file outputs, not all CSV files with the same name in the output directory
   for each run had the same number of rows and columns. SIERRA does not
   sanitize run outputs before processing them, and relies CSV files of the same
   shape when processing results for generating statistics. Depending on the
   nature of the inconsistency, you may see a crash, or you may see it hang
   indefinitely as it waits for a sub-process which crashed to finish.

#. Q: SIERRA fails to run on my HPC environment?

   A: The most likely reason is that you don't have the necessary environment
   variables set up--see :ref:`plugins/execenv/hpc` for details on what is
   required.

#. Q: SIERRA doesn't generate any graphs during stage4/the graph I'm interested
   is not there.

   A: SIERRA matches the stem of an output CSV file with the stem in a
   ``.yaml`` configuration file; if these are not the same, then no graph will
   be generated. You can run SIERRA with ``--log-level=TRACE`` to during stage 4
   to see which graphs it is generating, and which it is not because the
   necessary source CSV file does not exist. This is usually enough to
   identify the culprit.

#. Q: SIERRA does not overwrite the input configuration for my experiment/SIERRA
   won't run my experiments again after they run the first time--why?

   A: This is by design: SIERRA `never ever never` deletes stuff for you in
   stages {1,2} that can result in lost experimental results in later
   stages. The files generated in stages {3,4,5} are generated `from` the
   earlier results, so it is OK to overwrite those. However, if you are sure you
   want to overwrite stuff, you can pass ``--exp-overwrite`` to disable this
   behavior during stages {1,2}. See also :ref:`philosophy`.

#. Q: I need to apply very precise/nuanced configuration to experiments that is
   too specific to be easily captured in a :term:`Batch Criteria` or other
   variable. How can I do this?

   A: You could create one or more controller categories/controllers in
   ``controllers.yaml``. Within each category *AND* controller, you can specify
   arbitrary changes to the ``--expdef-template``: adding tags, removing tags,
   modifying attributes. This is a good way to apply tricky configuration which
   doesn't really fit anywhere else, or to try out some "quick and dirty"
   changes to see if they do what you want before codifying them with a python
   class (see :ref:`tutorials/project/config` for details on how to do that).

#. Q: SIERRA can't find a module it should be able to find via
   :envvar:`SIERRA_PLUGIN_PATH` or :envvar:`PYTHONPATH`. I know the module path
   is correct--why can't SIERRA find it?

   A: If you're sure you have the two environment variables set correctly, the
   reason is likely that you have an import *inside* the module you are trying
   to load which is not found. Try this::

     python3 -m full.path.to.module

   This command will attempt to find and load the problematic module, and will
   print any import errors. When you load modules dynamically in python, those
   errors don't get printed, python just says "can't find the module" instead of
   "found the module but I can't load it because of bad imports".


#. Q: I have multiple projects which all share batch
   criteria/generators/etc. How can I share this between projects?

   A: You have a couple options, depending on your preferences and the nature of
   what you want to share:

   - You could create a "common" project containing the reusable classes, and
     your other projects inherit from these classes as needed. This works if
     most of the stuff you want to share is class-based and does *not* need to
     be selectable via ``--batch-criteria``.

     Pros: Easy, straightforward.

     Cons: Being able to import stuff from a project which was not passed via
     ``--project`` is subject to :envvar:`SIERRA_PLUGIN_PATH`, which might make
     sharing classes trickier, because you will have to make sure the right
     version of a class is found by SIERRA (you can have it tell you via
     ``--log-level=TRACE``).

   - You can put common stuff into a separate python module/package/repo, and
     import it into your SIERRA project via :envvar:`PYTHONPATH`. This works if
     most of the stuff you want to share does *not* need to be selectable via
     ``--batch-criteria``.

     Pros: Clearer separation between shared and non-shared code.

     Cons: Debugging is more difficult because you now have multiple environment
     variables which need to be set in order to be able to run SIERRA.

   - You can put shared stuff into a common project, and then "lift" these
     classes declarations into your projects SIERRA import path as needed. For
     example, suppose you have a project ``laserblast`` on
     :envvar:`SIERRA_PLUGIN_PATH` as ``$HOME/git/sierra-projects/laser_blast``
     (i.e., :envvar:`SIERRA_PLUGIN_PATH`\=\ ``$HOME/git/sierra-projects``),
     which relies on some shared code in
     ``$HOME/git/sierra-projects/common``. Specifically a ``SimpleBlaster``
     class in ``common/variables/simple_blaster.py`` which you want to be
     selectable via ``--batch-criteria=simple_blaster.XX.YY.ZZ`` in the
     ``laser_blast`` project. You can create the following ``__init__.py`` file
     in ``laser_blast/variables/__init__.py``::

       import sys
       from common.variables simple_blaster

       sys.modules['laser_blast.variables.simple_blaster'] = simple_blaster

     Then, when SIERRA asks the python interpreter to find
     ``laser_blast.variables.simple_blaster``, it is as if you had defined this
     class in the ``laser_blast.variables`` namespace.

     This works well when the stuff you want to share between projects *does*
     need to be selectable via ``--batch-criteria``.

     Pros: Good code reuse, no danger of selecting the wrong version of a class.

     Cons: Sort of hacky from a python interpreter/language point of view.

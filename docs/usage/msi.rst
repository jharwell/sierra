.. _ln-msi-runtime:

How To Run on MSI
=================

This assumes you have already successfully completed the :ref:`ln-msi-setup`
steps. If not--shoo! Go do that first.

#. Copy and modify the ``example.pbs`` script under ``scripts/`` in the sierra repo
   for your experiment/batch experiment. You will need to change:

   - ``FORDYCA``: To the location of the where you cloned the fordyca repo
   - ``SIERRA``: To the location of the where you cloned the SIERRA repo
   - The contact email, number of requested nodes, etc. for the PBS script (you
     read the docs, right?)

#. Have your ``.pbs`` script script reviewed before submission (will likely save
   you a *LOTS* of time fighting with the job submission system).

#. Submit your job via::

     qsub your-pbs-script.pbs

   Note the job number that the job submission will print when you run this
   command--it is important to track job progress and to figure out what
   happened when things go wrong.

   It is also generally a good idea to give your PBS script a (fairly) unique as
   descriptive name when submitting, in order to make tracking down what
   stderr/stdout file belongs to what job when once you've run a few dozen jobs.

   You will get an email when your job starts, and when it finishes/crashes. To
   view the in-progress stdout of the job, look in the file called
   ``your-pbs-script.pbs.o1234`` where ``1234`` is the job number of your
   job. MSI will create this file in the directory you submit the job from, and
   direct your job's stdout to it. To view the stderr for your job, look in the
   file ``your-pbs-script.pbs.e1234`` where ``1234`` is the job number of your
   job. MSI will create this file in the directory you submit the job from, and
   direct your job's stderr to it.

#. Reap the rewards of research!

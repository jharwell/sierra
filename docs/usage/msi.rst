.. _ln-msi-runtime:

How To Run on MSI
=================

This assumes you have already successfully completed the :ref:`ln-msi-setup`
steps. If not--shoo! Go do that first.

#. Now that you have gotten things setup on MSI, read the documentation for PBS
   scripts and MSI job submission a queue on your chosen cluster:

   - https://www.msi.umn.edu/content/job-submission-and-scheduling-pbs-scripts
   - https://www.msi.umn.edu/queues

   Seriously--**READ THEM**.

#. Now that you have read the MSI docs, copy and modify ``scripts/example.pbs``
   script in the SIERRA repo for your experiment/batch experiment, and modify as
   needed:

   PBS parameters you **DO** need to change:

     - The email (I don't want to get emails about **YOUR** jobs).

   PBS parameters you **MIGHT** need to change:

     - The number of requested nodes.

   Other things you **MIGHT** need to change:

     - The location of the FORDYCA and SIERRA repos in the script, if you did
       not clone them to the same location as specified earlier in these steps.

#. Have your ``.pbs`` script script reviewed before submission (will likely save
   you a *LOTS* of time fighting with the job submission system).

#. Submit your job via::

     qsub your-pbs-script.pbs

   Note the job number that the job submission will print when you run this
   command--it is important to track job progress and to figure out what
   happened when (not if) things go wrong.

   It is also generally a good idea to get in the habit of giving your PBS
   scripts (fairly) unique and descriptive names when submitting, in order to
   make tracking down what stderr/stdout file belongs to what job when once
   you've run a few dozen jobs.

   You will get an email when your job starts, and when it finishes/crashes. To
   view the in-progress stdout of the job, look in the file called
   ``your-pbs-script.pbs.o1234`` where ``1234`` is the job number of your
   job. MSI will create this file in the directory you submit the job from, and
   direct your job's stdout to it. To view the stderr for your job, look in the
   file ``your-pbs-script.pbs.e1234`` where ``1234`` is the job number of your
   job. MSI will create this file in the directory you submit the job from, and
   direct your job's stderr to it.

   .. IMPORTANT:: The stdout and stderr files from your script will be created
                  in the directory you run the ``qsub`` command from. Make sure
                  you have write permission to the directory you submit from,
                  otherwise, you will probably get a cryptic error from the PBS
                  job scheduler.

#. Reap the rewards of research!

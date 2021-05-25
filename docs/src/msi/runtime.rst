===========
MSI Runtime
===========

.. IMPORTANT::
   Prior to executing these steps you should have:

   1. Already successfully completed the :doc:`/src/msi/setup` steps. If
      not--shoo! Go do that first.

Workflow
========

#. Read the documentation for SLURM scripts and MSI job submission to a
   partition on your chosen cluster:

   - https://www.msi.umn.edu/partitions
     https://www.msi.umn.edu/content/job-submission-and-scheduling-slurm

   Seriously--**READ THEM**.

#. Now that you have read the MSI docs, copy and modify ``scripts/example.sh``
   script in the SIERRA repo for your experiment/batch experiment, and modify as
   needed:

   Slurm parameters you **DO** need to change:

     - The email (I don't want to get emails about **YOUR** jobs).

   Slurm parameters you **MIGHT** need to change:

     - The number of requested nodes.

   Other things you **MIGHT** need to change:

     - The location of the FORDYCA and SIERRA repos in the script, if you did
       not clone them to the same location as specified earlier in these steps.

#. Have your jobs script reviewed before submission (will likely save you a
   *LOTS* of time fighting with the job submission system).

#. Submit your job via::

     sbatch your-script.sh

   Note the job number that the job submission will print when you run this
   command--it is important to track job progress and to figure out what
   happened when (not if) things go wrong.

   It is also generally a good idea to get in the habit of giving your PBS
   scripts (fairly) unique and descriptive names when submitting, in order to
   make tracking down what stderr/stdout file belongs to what job when once
   you've run a few dozen jobs.

   You will get an email when your job starts, aborts because of error, and
   finishes. To view the in-progress stdout of the job, look in your home
   directory for output/error files:

     - ``$HOME/R-your-jobname.1234.out`` where ``1234`` is the job number of
       your job. MSI will create this file in the directory you submit the job
       from, and direct your job's stdout to it.

     - ``$HOME/R-your-jobname.1234.err`` where ``1234`` is the job number of
       your job. MSI will create this file in the directory you submit the job
       from, and direct your job's stderr to it.

#. Reap the rewards of research!

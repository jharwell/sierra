.. Sierra documentation master file, created by
   sphinx-quickstart on Sat Oct 12 17:39:54 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Contributing
============

General Workflow
----------------

#. Find an issue on github to work on that looks interesting/doable, possibly
   discussing it with the project's main author(s).

#. Mark said task as ``Status: In Progress`` so no one else starts working on it
   too, and assign it to yourself if it is not already assigned to you.

#. Branch off of the ``devel`` branch with a branch with the *SAME* name as the
   issue.

#. Work on the issue/task, committing as needed. You should:

   - Push your changes regularly, so people can see that the issue is being
     actively worked on. Commit messages should follow the `Git Commit Guide
     https://github.com/swarm-robotics/libra/tree/devel/git-commit-guide.md` 

   - Merge in the ``devel`` branch into your branch periodicaly so that merge
     conflicts/headaches are minimized.

#. If you create any new functions/classes that can be unit tested, then define
   appropriate unit tests for them, and prepare a report documenting code
   coverage, as described above.

#. Run static analysis on the code from the root of SIERRA::

     pytype -k .

   Fix ANY and ALL errors that arise, as SIERRA should get a clean bill of
   health from the checker.

#. Change status to ``Status: Needs Review`` and open a pull request, and someone
   will review the commits. If you created unit tests, attach a log/run showing
   they all pass, as well as the code coverage report from gcov.

3. Once the task has been reviewed and given the green light, it will be merged
    into devel and marked as ``Status: Completed``, and closed (you generally
    don't need to do this).


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   variable.rst
   graphs.rst

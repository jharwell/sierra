Non-MSI Setup
=============

Before trying to use sierra with MSI, you should get it installed and running on
your local machine, and try a few small scale experiments.

#. Install python dependencies with ``pip3``:

   ``pip3 install pandas similaritymeasures fastdtw matplotlib pyyaml``

   - pandas (used for .csv file manipulation)
   - similaritymeasures (needed for temporal variance graph generation)
   - fastdtw (needed for temporal variance graph generation)
   - pyyaml (needed for .yaml configuration file parsing)

#. Install OS packages:

   - GNU parallel (``parallel`` on ubuntu)

**IMPORTANT**: When running sierra, unless you have added the sierra repo to your
``PYTHONPATH`` and/or ``sierra.py`` to your ``PATH``, you will only be able to
launch it from the root of the sierra repo.

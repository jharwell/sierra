.. _ln-local-setup:

Local Setup
=============

Before trying to use SIERRA with MSI (or any other HPC environment), you should
get it installed and running on your local machine, and try a few small scale
experiments (see :ref:`ln-usage` for post-setup "how-to"). The steps to setup
SIERRA to do so are outlined below.

#. Install python dependencies with ``pip3``::

     pip3 install -r requirements/common.txt

   - pandas (used for .csv file manipulation)
   - similaritymeasures (needed for temporal variance graph generation)
   - fastdtw (needed for temporal variance graph generation)
   - pyyaml (needed for .yaml configuration file parsing)
   - coloredlogs (for nice colored logging)
   - sympy (for graph label generation)

#. Install OS packages:

   - GNU parallel (``parallel`` on ubuntu)

     .. IMPORTANT:: When running SIERRA, unless you have added the sierra repo
               to your ``PYTHONPATH`` and/or ``sierra.py`` to your ``PATH``, you
               will only be able to launch it from the root of the SIERRA repo.

.. IMPORTANT:: Do not try to run sierra with a debug build of whatever project
               you are using (:xref:`FORDYCA`, :xref:`SILICON`, etc). It (probably)
               won't work and will be obnoxiously/irritatingly slow if it does.

#. Clone plugin for whatever project you are going to use into
   ``plugins``. SIERRA will (probably) refuse to do anything useful if there are
   no plugins installed. The repository should be cloned into a directory with
   the EXACT name you want it to be callable with on the cmdline via
   ``--plugin``.

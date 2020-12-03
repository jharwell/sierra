.. _ln-local-setup:

Local Setup
=============

Before trying to use SIERRA with MSI (or any other HPC environment), you should
get it installed and running on your local machine, and try a few small scale
experiments (see :ref:`ln-usage` for post-setup "how-to"). The steps to setup
SIERRA to do so are outlined below.

#. Install python dependencies with ``pip3``::

     pip3 install -r requirements/common.txt

#. Install OS packages:

   - GNU parallel (``parallel`` on ubuntu)

     .. IMPORTANT:: When running SIERRA, unless you have added the sierra repo
               to your ``PYTHONPATH`` and/or ``sierra.py`` to your ``PATH``, you
               will only be able to launch it from the root of the SIERRA repo.

.. IMPORTANT:: Do not try to run sierra with a debug build of whatever project
               you are using (:xref:`FORDYCA`, :xref:`SILICON`, etc). It will
               work but be obnoxiously/irritatingly slow.

#. Clone plugin for whatever project you are going to use into
   ``projects``. SIERRA will (probably) refuse to do anything useful if there are
   no project installed. The repository should be cloned into a directory with
   the EXACT name you want it to be callable with on the cmdline via
   ``--project``.

   Projects known to work with SIERRA/have reasonably well defined plugins are::

   - :xref:`FORDYCA`: `<https://github.com/swarm-robotics/sierra-plugin-fordyca.git>`_
   - :xref:`SILICON`:  `<https://github.com/swarm-robotics/sierra-plugin-silicon.git>`_

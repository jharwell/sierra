.. SIERRA documentation master file, created by
   sphinx-quickstart on Sat Oct 12 17:39:54 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Contributing
============

First, install additional dependencies::

  pip3 pytype pylint

General Workflow
----------------

For the general contribution workflow, see the docs over in `libra
<https://github.com/swarm-robotics/libra/tree/devel/workflow.md>`_.

For the static analysis step:

#. Run the following on the code from the root of SIERRA::

     pytype -k .

   Fix ANY and ALL errors that arise, as SIERRA should get a clean bill of health
   from the checker.

#. Run the following on any module directories you changed, from the root of SIERRA::

     pylint <directory name>

   Fix ANY errors your changes have introduced (there will probably still be
   errors in the pylint output, because cleaning up the code is always a work in
   progress).

.. toctree::
   :maxdepth: 2
   :caption: Full Docs:

   variable.rst
   graphs.rst

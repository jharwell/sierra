.. _ln-platform-plugins:

============================
Supported Robotics Platforms
============================

SIERRA supports a number of robotic :term:`platforms <Platform>`, all of which
can be used transparently for running experiments (well transparent from
SIERRA's point of view; you probably will still have to make code modifications
to switch between platforms).

- :ref:`ARGoS <ln-platform-plugins-argos>`

.. _ln-platform-plugins-argos:

ARGoS Platform
==============

This platform can be selected via ``--platform=platform.argos``.

This is the default platform on which SIERRA will run experiments, and using the
:term:`ARGoS` simulator. It cannot be used to run experiments on real robots.


.. toctree::
   :maxdepth: 2
   :caption: ARGoS-specific Configuration for SIERRA

   argos/variables.rst
   argos/batch_criteria.rst

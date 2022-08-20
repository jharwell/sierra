.. _ln-sierra-platform-plugins-argos:

==============
ARGoS Platform
==============

This platform can be selected via ``--platform=platform.argos``.

This is the default platform on which SIERRA will run experiments, and uses the
:term:`ARGoS` simulator. It cannot be used to run experiments on real robots.

.. toctree::

   batch_criteria.rst

Environment Variables
=====================

This platform respects :envvar:`SIERRA_ARCH`.

Random Seeding For Reproducibility
==================================

ARGoS provides its own random seed mechanism under ``<experiment>`` which SIERRA
uses to seed each experiment. :term:`Project` code should use this mechanism or
a similar random seed generator manager seeded by the same value so that
experiments can be reproduced exactly. By default SIERRA does not overwrite its
generated random seeds for each experiment once generated; you can override with
``--no-preserve-seeds``. See :ref:`ln-sierra-tutorials-project-template-input-file` and
:ref:`ln-sierra-req-exp` for details on the format of the provided seed.

.. _user-guide:

=================
SIERRA User Guide
=================

Task-oriented documentation for day-to-day SIERRA use. These pages assume you
have a working SIERRA installation and have completed either the
:ref:`getting-started/trial` or :ref:`getting-started/setup`.

.. list-table::
   :header-rows: 0
   :widths: 30 70

   * - :doc:`examples`
     - Annotated ``sierra-cli`` invocations covering common scenarios: local
       runs, HPC clusters, rendering, bivariate sweeps, selective pipeline
       stages, and stage 5 comparisons. Start here when crafting a new
       invocation.

   * - :doc:`variables`
     - The ``--exp-setup`` variable for configuring experiment duration and
       controller cadence — including which engines support it and what
       happens when they do.

.. toctree::
   :hidden:

   examples
   variables

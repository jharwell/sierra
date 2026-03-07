..
   Copyright 2026 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

=====================
Quickstart
=====================

This tutorial demonstrates how to run a simple SIERRA experiment.

In this guide you will:

1. Define an experiment
2. Expand batch criteria
3. Execute experiments
4. Generate results


Basic Workflow
==============

Running experiments with SIERRA typically follows this workflow:

1. Write an **experiment definition**
2. Specify **batch criteria** (parameter sweeps)
3. Run the experiment pipeline
4. Analyze results


Running Your First Experiment
=============================

Execute:

.. code-block:: bash

   sierra run examples/basic_exp.yaml

SIERRA will:

1. Expand the batch criteria
2. Generate experiment instances
3. Execute experiments
4. Store outputs


Expected Output
===============

After execution, the output directory will contain:

.. code-block:: text

   results/
       exp0/
       exp1/
       exp2/
       processed/
       artifacts/

Each directory corresponds to a specific experiment configuration.


Next Steps
==========

Learn the core concepts:

* :doc:`../concepts/experiments`
* :doc:`../concepts/batch-criteria`
* :doc:`../concepts/pipeline`

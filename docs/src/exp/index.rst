..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _exp:

================================
Experimental Design And Dataflow
================================

This is the landing page for designing experiments and working with data as it
flows through SIERRA.

.. _exp/design:

Experimental Design
===================

In SIERRA, there are 3 main faculties that are used to design experiments:

- The *controller*. In SIERRA, a ``--controller`` is simply a designation of
  some aspect of an algorithm which you are running. Even if what you designate
  as the controller is *not* actually controlling a significant part of the
  behaviors, it *IS* the controlling knob from the perspective of the experiment
  you want to run. Put another way, controllers designate the algorithm/thing
  under test.

- The *scenario*. In SIERRA, the ``--scenario`` is simply a designation of some
  aspect(s) of the experimental context in which the controller will run. This
  may be a more literal "scenario" in the sense of arena size, what it contains,
  etc., or it might just be a collection of features which are the inputs into
  your simulator, or anything in between.

  .. TIP:: The line between what a controller vs. scenario is intentionally
           blurry; SIERRA makes every effort in the source to treat them as
           equitably as possible, to allow you to define things with semantic
           labels which make sense to YOU.

- The :term:`Batch Criteria`. In SIERRA, the ``--batch-criteria`` is the main
  workhorse of designing experiments. It defines the *independent* variables
  (you can have any number, defining an N-D experimental space). Each variable
  can make pretty much any changes it wants to the experimental inputs, giving
  you *massive* flexibility on how to set up your experiments. Variables are
  combined combinatorically by the sets of changes they make to experimental
  inputs to define the N-D experimental space.


Beyond this, the *dependent* variables are those which you select as important
when you declare how you want your data to be :ref:`processed <plugins/proc>`,
and/or what :ref:`products/deliverables <plugins/prod>` you want to
generate. Selection is declarative; you just say something like "I'm interested
in THIS column of THIS .csv file under the different conditions present
throughout the different experiment, and I want the data to appear like THIS on
THIS type of graph". SIERRA handles the rest!

.. _exp/dataflow:

Dataflow
========

This section details SIERRA's builtin data model, as it pertains to data
generated in :term:`Experimental Runs <Experimental Run>`. That is, once data is
generated as a result of running things in stage 2, how it is processed and
transformed into deliverables in the later stages of the pipeline.

.. toctree::

   stage3-dataflow.rst
   stage4-dataflow.rst
   stage5-dataflow.rst

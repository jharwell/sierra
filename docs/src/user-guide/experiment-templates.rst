.. SPDX-License-Identifier: MIT

.. _user-guide/experiment-templates:

====================
Experiment Templates
====================

The experiment template---passed via
:ref:`--expdef-template<src/reference/cli:sierra-cli---expdef-template>`---is
the starting point for all experiment generation. Stage 1 reads it once, applies
modifications from your batch criteria and controller configuration, and writes
one input file per experimental run into the batch input tree. This page
explains the contract a valid template must satisfy and what stage 1 does with
it. For token syntax and format-specific restrictions, see
:ref:`plugins/expdef` for your chosen input file format.

.. _user-guide/experiment-templates/single-file:

The Single-File Requirement
===========================

SIERRA requires the template to be a single file. All parameters SIERRA
needs to vary must be reachable within that one file---anything outside
it is invisible to the modification pipeline.

If your simulator normally expects multiple configuration files (a common
pattern in ROS launch setups), you have two options:

#. Flatten the configuration into a single file before passing it to SIERRA. The
   :term:`Engine` plugin can provide an ``expdef_flatten()`` hook that SIERRA
   calls at the start of stage 1 to perform this transformation
   automatically. See :ref:`plugins/engine` for how to implement this hook.

#. Factor out only the parameters SIERRA needs to vary into the template and
   load the remaining files from fixed paths within your project.  This is the
   pragmatic approach for large legacy configurations where flattening is not
   practical.

See :ref:`reference/philosophy` for the design rationale behind this
requirement.

.. _user-guide/experiment-templates/what-stage1-does:

What Stage 1 Does With Your Template
======================================

For each experiment in the batch, stage 1 applies modifications from
batch criteria and ``controllers.yaml`` to the template, substitutes
tokens, then writes one copy per experimental run with a unique random
seed injected. Each copy is named ``<template-stem>_run<N>`` and placed
in the experiment's input directory under :ref:`--sierra-root
<sierra-cli---sierra-root>`. Stage 1 also writes a GNU parallel command
file for stage 2 to consume. See :ref:`concepts/run-time-tree` for the
full directory layout.

See :ref:`stage1 deep dive<arch/deep-dive/stage>` for the details of this
process.

.. _user-guide/experiment-templates/random-seeds:

Random Seeds
============

SIERRA injects a unique random seed into each run's copy of the
template. The seed is written to the location specified by your engine
plugin's random seed configuration — you do not need to add a token or
placeholder for it. SIERRA generates new seeds for each batch by
default; if you need to regenerate a batch with the same seed sequence
(for debugging or exact replication), pass :ref:`--exp-overwrite
<src/reference/cli:sierra-cli---exp-overwrite>`.

The ``random_seed`` attribute in the template file for the :xref:`ARGoS sample
project <SIERRA_SAMPLE_PROJECT>` (``framework/experiment/@random_seed``) is an
example. The value ``123`` in the template is overwritten by stage 1 for every
run---it is only there to make the template a valid standalone file.

.. _user-guide/experiment-templates/output-dir:

Output Directory Naming
=======================

SIERRA derives per-run input filenames from the template filename stem.  A
template named ``template.argos`` produces per-run input files named
``template_run0``, ``template_run1``, etc. Choose a descriptive stem---it
appears throughout the batch input tree and in log output. Where SIERRA looks
for run outputs is configured separately in ``main.yaml`` via
``run_metrics_leaf``; see :ref:`tutorials/project/config`.


.. _user-guide/experiment-templates/format-notes:

Format Notes
============

See :ref:`plugins/expdef` for per-format token syntax and restrictions. One
thing worth knowing when writing batch criteria: for JSON and YAML templates,
SIERRA treats keys mapping to scalars and keys mapping to nested objects
differently ---you can only target scalar-valued keys from
``gen_attr_changelist()``. Targeting a subtree key raises an error.  XPath
expressions in XML templates use standard Python :mod:`xml.etree.ElementTree`
syntax.

.. _user-guide/experiment-templates/examples:

Template Examples
=================

The :xref:`sample project<SIERRA_SAMPLE_PROJECT>` provides one template per
supported engine under ``exp/``. These serve as minimal valid starting points

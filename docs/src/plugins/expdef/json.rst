..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/expdef/json:

====
JSON
====

This expdef plugin can be selected via ``--expdef=expdef.json``. This plugin
supports flattening/nested configuration files.

.. IMPORTANT:: If multiple matches for a given JSONpath string are found, ALL
               are modified accordingly.

Experimental inputs are defined using JSON. See the section on JSON in
:ref:`tutorials/plugins/expdef/tokens` for restrictions on the contents of JSON
input files.

Reserved Tokens
===============

- ``__CONTROLLER__`` - Placeholder used to select which controller present in an
  input file (if there are multiple) a user wants to use for a specific
  :term:`Experiment`. Can appear in JSON attributes. This makes auto-population
  of the controller name based on the ``--controller`` argument and the contents
  of ``controllers.yaml`` (see :ref:`tutorials/project/config` for details) in
  template input files possible.

Attributes vs. elements
=======================

.. include:: attr-element-rule.rst

The JSON plugin supports *array-valued attributes*: a key whose value is a flat
list of scalars (e.g. ``"ports": [80, 443]``) is a valid attribute and can be
read and modified as one.

.. versionadded:: 1.3.19

.. versionchanged:: 1.5.10
   Flat arrays of scalars are now recognized as attributes (array-valued
   attributes), and setting an attribute value onto a key that maps to an
   element is now explicitly refused.

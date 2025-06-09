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
:ref:`req/expdef` for restrictions on the contents of JSON input files.


.. versionadded:: 1.3.19

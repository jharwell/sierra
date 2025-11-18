..
   Copyright 2025 John Harwell, All rights reserved.

   SPDX-License-Identifier:  MIT

.. _plugins/expdef/yaml:

====
YAML
====

This expdef plugin can be selected via ``--expdef=expdef.yaml``. This plugin
supports flattening/nested configuration files.

.. IMPORTANT:: If multiple matches for a given YAMLpath string are found, ALL
               are modified accordingly when updating attributes.

Experimental inputs are defined using YAML. See the section on YAML in
:ref:`req/expdef` for restrictions on the contents of YAML input files.


.. versionadded:: 1.5.2

#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""YAML loading and validation for SIERRA config.

This subpackage groups the two adjacent concerns of reading config off disk and
checking it, while keeping them in separate modules so their dependencies stay
separate:

- :mod:`sierra.core.pipeline.yaml` remains the *loader* (imported here for
  namespace convenience). It is intentionally left in place because its module
  path participates in the project-override tiered-loading contract
  (``module_load_tiered(path="pipeline.yaml")``): projects may ship their own
  ``pipeline/yaml.py`` to override ``load_config``, and moving core's copy would
  break that contract.

- :mod:`sierra.core.yaml.validate` is the *validator*, holding the strictyaml
  machinery. It is deliberately **not** re-exported here: importing this package
  for loading should not pull in strictyaml. Reach for validation explicitly
  with ``from sierra.core.yaml import validate`` (the submodule) or
  ``from sierra.core.yaml.validate import ConfigError, validate_entry``.
"""

# Core packages

# 3rd party packages

# Project packages

# Cheap re-export: the loader depends only on `yaml` + `utils`. The validator
# (strictyaml) is intentionally NOT imported here
from sierra.core.pipeline.yaml import load_config

__all__ = ["load_config"]

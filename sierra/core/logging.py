# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Extensions to the standard python ``logging`` module for SIERRA.

These include:

- Supporting the additional ``TRACE`` level. No idea why this is not supported
  by default...

- Adding nice colored logging which is helpful but not angry fruit salad.

"""
# Core packages
import logging

# 3rd party packages
import coloredlogs
from haggis import logs

# Project packages


def initialize(log_level: str):
    logs.add_logging_level(level_name='TRACE',
                           level_num=logging.DEBUG - 5,
                           method_name=None,
                           if_exists=logs.RAISE)
    # Needed for static analysis (mypy and/or pylint)
    setattr(logging, '_HAS_DYNAMIC_ATTRIBUTES', True)

    # Get nice colored logging output!
    coloredlogs.install(fmt='%(asctime)s %(levelname)s %(name)s - %(message)s',
                            level=eval("logging." + log_level))

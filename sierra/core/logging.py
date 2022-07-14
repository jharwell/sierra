# Copyright 2021 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
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

# Project packages

TRACE = logging.DEBUG - 5


def initialize(log_level):
    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(TRACE, message, *args, **kwargs)

    logging.addLevelName(TRACE, "TRACE")
    setattr(logging, "TRACE", TRACE)
    setattr(logging.getLoggerClass(), "trace", log_for_level)
    setattr(logging, "trace", log_to_root)

    # Needed for static analysis (mypy and/or pylint)
    setattr(logging, '_HAS_DYNAMIC_ATTRIBUTES', True)

    # Get nice colored logging output!
    coloredlogs.install(fmt='%(asctime)s %(levelname)s %(name)s - %(message)s',
                            level=eval("logging." + log_level))

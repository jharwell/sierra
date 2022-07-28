# Copyright 2022 John Harwell, All rights reserved.
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

# Core packages

# 3rd party packages
from xmldiff import main

# Project packages
from sierra.core.experiment.definition import XMLExpDef
from sierra.core.experiment import xml
import sierra.core.logging


def test_rdrw():
    sierra.core.logging.initialize('INFO')

    config = xml.WriterConfig([{'src_parent': None,
                                'src_tag': '.'}])
    exp1 = XMLExpDef(input_fpath="./tests/test1.xml",
                     write_config=config)

    exp1.write("/tmp/test1-out.xml")

    diff = main.diff_files("./tests/test1.xml", "/tmp/test1-out.xml")

    assert len(diff) == 0

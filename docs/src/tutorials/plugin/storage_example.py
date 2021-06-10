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

# Core packages

# 3rd party packages
import pandas as pd

# Project packages


def df_read(path: str, **kwargs) -> pd.DataFrame:
    """
    Return a dataframe containing the contains of the ``.csv`` at the specified path. For other
    storage methods (e.g. database), you can use a function of the path way to unique identify the
    file in the database (for example).
    """


def df_write(df: pd.DataFrame, path: str, **kwargs) -> None:
    """
    Write a dataframe containing to the specified path. For other
    storage methods (e.g. database), you can use a function of the path way to unique identify the
    file in the database (for example) when you add it.
    """

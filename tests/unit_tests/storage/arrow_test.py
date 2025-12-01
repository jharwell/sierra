# Copyright 2022 John Harwell, All rights reserved.

# Core packages

# 3rd party packages
import pandas as pd
import numpy as np

# Project packages
from sierra.plugins.storage.arrow import plugin as arrow


def test_rdrw():
    df = pd.DataFrame(np.random.randint(1, 10, size=(5, 3)), columns=["A", "B", "C"])

    arrow.df_write(df, "/tmp/random1.arrow")
    df2 = arrow.df_read("/tmp/random1.arrow")

    assert df.equals(df2)

"""
 Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

import os
from pipeline.exp_video_renderer import ExpVideoRenderer


class BatchedExpVideoRenderer:

    """
    Render the video for each experiment in the specified batch directory in sequence.

    Attributes:
      batch_exp_root(str): Root directory for the batch experiment.

    """

    def __init__(self, batch_exp_root):
        self.batch_exp_root = os.path.abspath(batch_exp_root)

    def render(self):
        """Render videos for all all experiments in the batch."""
        experiments = []
        # All dirs start with 'exp', so only sort on stuff after that. Running exp in order will
        # make collecting timing data/eyeballing runtimes much easier.
        sorted_dirs = sorted([d for d in os.listdir(self.batch_exp_root) if 'collated-csvs' not in d],
                             key=lambda e: int(e[3:]))
        experiments = [os.path.join(self.batch_exp_root, item) for item in sorted_dirs
                       if os.path.isdir(os.path.join(self.batch_exp_root, item))]
        for exp in experiments:
            ExpVideoRenderer(exp).render()

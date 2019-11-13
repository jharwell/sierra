# Copyright 2019 John Harwell, All rights reserved.
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


import os
import subprocess
import logging


class BatchedExpVideoRenderer:

    """
    Render the video for each experiment in the specified batch directory in sequence.

    Attributes:
      ro_params(dict): Dictionary of read-only parameters for batch rendering
      batch_exp_root(str): Root directory for the batch experiment.

    """

    def __init__(self, ro_params, batch_exp_root):
        self.batch_exp_root = os.path.abspath(batch_exp_root)
        self.cmd_opts = ro_params['cmd_opts']
        self.ofile_leaf = ro_params['ofile_leaf']
        self.ro_params = ro_params

    def render(self):
        """Render videos for all all experiments in the batch."""
        experiments = []
        sorted_dirs = sorted([d for d in os.listdir(self.batch_exp_root)
                              if self.ro_params['config']['sierra']['collate_csv_leaf'] not in d])
        experiments = [os.path.join(self.batch_exp_root, item) for item in sorted_dirs
                       if os.path.isdir(os.path.join(self.batch_exp_root, item))]
        for exp in experiments:
            ExpVideoRenderer(self.ro_params, exp).render()


class ExpVideoRenderer:
    """
    Render grabbed frames in ARGoS to a video file via ffmpeg.

    Attributes:
        ro_params(dict): Dictionary of read-only parameters for batch rendering.
        cmd_opts(str): Cmdline options to pass to ffmpeg.
        ofile_leaf(str): The name of the video output file (specified releative to simulation output
                         directory).
        config(dict): Parsed dictionary of main YAML configuration.
        exp_output_root(str): Root directory of simulation output (relative to current dir or
                              absolute).
    """

    kFramesFolderName = "frames"

    def __init__(self, ro_params, exp_output_root):
        self.ro_params = ro_params
        self.exp_output_root = exp_output_root

    def render(self):
        logging.info("Rendering videos in {0}:leaf={1}...".format(self.exp_output_root,
                                                                  self.ro_params['ofile_leaf']))

        opts = self.ro_params['cmd_opts'].split(' ')
        # Render videos in parallel--waaayyyy faster
        procs = []
        for d in os.listdir(self.exp_output_root):
            path = os.path.join(self.exp_output_root, d)
            if os.path.isdir(path) and self.ro_params['config']['sierra']['avg_output_leaf'] not in path:
                frames_path = os.path.join(path, self.ro_params['config']['sim']['frames_leaf'])
                cmd = ["ffmpeg",
                       "-y",
                       "-i", os.path.join(frames_path, "%*.png")]
                cmd.extend(opts)
                cmd.extend([os.path.join(path, self.ro_params['ofile_leaf'])])
                procs.append(subprocess.Popen(cmd,
                                              stderr=subprocess.DEVNULL,
                                              stdout=subprocess.DEVNULL))
                [p.wait() for p in procs]

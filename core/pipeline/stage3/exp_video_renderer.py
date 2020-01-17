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

"""
Classes for rendering frames captured by ARGoS during simulation.
"""

import os
import subprocess
import logging
import typing as tp


class BatchedExpVideoRenderer:
    """
    Render the video for each experiment in the specified batch directory in sequence.
    """

    def __call__(self, main_config: dict, render_opts: tp.Dict[str, str], batch_exp_root: str):
        """
        Arguments:
            main_config: Parsed dictionary of main YAML configuration.
            render_opts: Dictionary of render options.
            batch_exp_root: Root directory for the batch experiment.
        """
        experiments = []
        sorted_dirs = sorted([d for d in os.listdir(batch_exp_root)
                              if main_config['config']['sierra']['collate_csv_leaf'] not in d])
        experiments = [os.path.join(batch_exp_root, item) for item in sorted_dirs
                       if os.path.isdir(os.path.join(batch_exp_root, item))]
        for exp in experiments:
            ExpVideoRenderer(main_config, render_opts, exp)()


class ExpVideoRenderer:
    """
    Render grabbed frames in ARGoS to a video file via ffmpeg for each simulation in the experiment
    in parallel (for speed).

    Arguments:
        main_config: Parsed dictionary of main YAML configuration.
        render_opts: Dictionary of render options.
        exp_output_root: Absolute path to directory of simulation output for the experiment.
    """

    def __call__(self, main_config: dict, render_opts: tp.Dict[str, str], exp_output_root: str):
        logging.info("Rendering videos in %s:leaf=%s...", exp_output_root,
                     main_config['ofile_leaf'])

        opts = render_opts['cmd_opts'].split(' ')
        # Render videos in parallel--waaayyyy faster
        procs = []
        for d in os.listdir(exp_output_root):
            path = os.path.join(exp_output_root, d)

            if not os.path.isdir(path):
                logging.warning("Path %s does not exist", path)
                continue

            if main_config['config']['sierra']['avg_output_leaf'] not in path:
                frames_path = os.path.join(path, main_config['config']['sim']['frames_leaf'])
                cmd = ["ffmpeg",
                       "-y",
                       "-i",
                       os.path.join(frames_path, "%*.png")]
                cmd.extend(opts)
                cmd.extend([os.path.join(path, render_opts['ofile_leaf'])])
                procs.append(subprocess.Popen(cmd,
                                              stderr=subprocess.DEVNULL,
                                              stdout=subprocess.DEVNULL))
        [p.wait() for p in procs]

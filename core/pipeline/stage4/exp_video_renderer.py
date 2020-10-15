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
Classes for rendering frames (1) captured by ARGoS during simulation, (2) generated during stage 3
of SIERRA.
"""

import os
import subprocess
import logging
import typing as tp
import multiprocessing as mp
import queue
import copy


import core.utils


class BatchedExpVideoRenderer:
    """
    Render the video for each experiment in the specified batch directory in sequence.
    """

    def __call__(self,
                 main_config: dict,
                 render_opts: tp.Dict[str, str],
                 batch_exp_root: str) -> None:
        """
        Arguments:
            main_config: Parsed dictionary of main YAML configuration.
            render_opts: Dictionary of render options.
            batch_exp_root: Root directory for the batch experiment.
        """
        experiments = [d for d in os.listdir(batch_exp_root)
                       if main_config['sierra']['collate_csv_leaf'] not in d]
        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in experiments:
            exp_root = os.path.join(batch_exp_root, exp)

            if render_opts['project_rendering']:
                opts = copy.deepcopy(render_opts)

                frames_root = os.path.join(exp_root,
                                           main_config['sierra']['project_frames_leaf'])
                # Project render targets are in <averaged_output_root>/<metric_dir_name>, for all
                # directories in <averaged_output_root>.
                for d in os.listdir(frames_root):
                    src_dir = os.path.join(frames_root, d)
                    if os.path.isdir(src_dir):
                        opts['image_dir'] = src_dir
                        opts['output_dir'] = os.path.join(exp_root, 'videos')
                        opts['ofile_leaf'] = d + '.mp4'

                        core.utils.dir_create_checked(opts['output_dir'], True)
                        q.put(opts)

            if render_opts['argos_rendering']:
                opts = copy.deepcopy(render_opts)

                # ARGoS render targets are in <batch_output_root>/<exp>/<sim>/<argos_frames_leaf>,
                # for all simulations in a given experiment (which can be a lot!).
                for sim in self.__filter_sim_dirs(os.listdir(exp_root), main_config):
                    opts['ofile_leaf'] = sim + '.mp4'
                    frames_root = os.path.join(exp_root,
                                               sim,
                                               main_config['sim']['argos_frames_leaf'])
                    opts['image_dir'] = frames_root
                    opts['output_dir'] = os.path.join(exp_root, 'videos')

                    core.utils.dir_create_checked(opts['output_dir'], exist_ok=True)
                    q.put(copy.deepcopy(opts))

        # Render videos in parallel--waaayyyy faster
        for i in range(0, mp.cpu_count()):
            p = mp.Process(target=BatchedExpVideoRenderer.__thread_worker,
                           args=(q, main_config))
            p.start()

        q.join()

    @staticmethod
    def __thread_worker(q: mp.Queue, main_config: dict) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                render_opts = q.get(True, 3)
                ExpVideoRenderer()(main_config, render_opts)
                q.task_done()
            except queue.Empty:
                break

    @staticmethod
    def __filter_sim_dirs(sim_dirs: tp.List[str], main_config: dict) -> tp.List[str]:
        return [s for s in sim_dirs if s not in [main_config['sierra']['avg_output_leaf'],
                                                 main_config['sierra']['project_frames_leaf'],
                                                 'videos']]


class ExpVideoRenderer:
    """
    Render all frames (.png files) in a specified input directory to a video file via ffmpeg, output
    according to configuration.

    Arguments:
        main_config: Parsed dictionary of main YAML configuration.
        render_opts: Dictionary of render options.
    """

    def __call__(self, main_config: dict, render_opts: tp.Dict[str, str]) -> None:
        logging.info("Rendering images in %s,ofile_leaf=%s...",
                     render_opts['image_dir'],
                     render_opts['ofile_leaf'])
        opts = render_opts['cmd_opts'].split(' ')

        cmd = ["ffmpeg",
               "-y",
               "-pattern_type",
               "glob",
               "-i",
               "'" + os.path.join(render_opts['image_dir'], "*.png") + "'"]
        cmd.extend(opts)
        cmd.extend([os.path.join(render_opts['output_dir'],
                                 render_opts['ofile_leaf'])])
        p = subprocess.Popen(' '.join(cmd),
                             shell=True,
                             stderr=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL)
        p.wait()


__api__ = ['BatchedExpVideoRenderer', 'ExpVideoRenderer']

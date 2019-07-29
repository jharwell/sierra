"""
 Copyright 2019 John Harwell, All rights reserved.

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
import subprocess


class ExpVideoRenderer:
    """
    Render grabbed frames in ARGoS to a video file via ffmpeg.

    Attributes:
      exp_output_root(str): Root directory of simulation output (relative to current dir or
                            absolute).
      render_cmd_options(str): String of options to pass to ffmpeg between input and output file
                               specification.
      video_fname(str): Output path for rendered video.
    """

    kFramesFolderName = "frames"

    def __init__(self, exp_output_root, render_cmd_options, render_cmd_ofile):
        self.exp_output_root = exp_output_root
        self.render_cmd_options = render_cmd_options
        self.video_fname = render_cmd_ofile

    def render(self):
        print("-- Rendering video {0}...".format(self.video_fname))

        options = self.render_cmd_options.split(' ')
        # Render videos in parallel--waaayyyy faster
        procs = []
        for d in os.listdir(self.exp_output_root):
            path = os.path.join(self.exp_output_root, d)
            if os.path.isdir(path) and 'averaged-output' not in path:
                frames_path = os.path.join(path, ExpVideoRenderer.kFramesFolderName)
                cmd = ["ffmpeg",
                       "-y",
                       "-i", os.path.join(frames_path, "%*.png")]
                cmd.extend(options)
                cmd.extend([os.path.join(path, self.video_fname)])
                procs.append(subprocess.Popen(cmd,
                                              stderr=subprocess.DEVNULL,
                                              stdout=subprocess.DEVNULL))
                [p.wait() for p in procs]

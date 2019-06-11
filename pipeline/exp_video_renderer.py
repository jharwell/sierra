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
      exp_output_root(str): Root directory of simulation output (relative to current dir or absolute).
    """

    kFramesFolderName = "frames"

    def __init__(self, exp_output_root):
        self.exp_output_root = exp_output_root
        self.video_fname = os.path.join(os.path.abspath(exp_output_root), "video.mp4")

    def render(self):
        print("-- Rendering videos for experiment in {0}...".format(self.exp_output_root))

        # Render videos in parallel--waaayyyy faster
        procs = []
        for d in os.listdir(self.exp_output_root):
            path = os.path.join(self.exp_output_root, d)
            if os.path.isdir(path) and 'averaged-output' not in path:
                frames_path = os.path.join(path, ExpVideoRenderer.kFramesFolderName)
                procs.append(subprocess.Popen(["ffmpeg",
                                               "-y",
                                               "-r", "10",
                                               "-i", os.path.join(frames_path, "%*.png"),
                                               "-s:v", "1600x1200",
                                               "-c:v", "libx264",
                                               "-crf", "25",
                                               "-vf", "scale=-2:956",
                                               "-pix_fmt", "yuv420p",
                                               os.path.join(path, "video.mp4")],
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL))
        [p.wait() for p in procs]

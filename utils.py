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

import pickle
import os
from generators.generator_pair_parser import GeneratorPairParser


def unpickle_exp_def(exp_def_fpath):
    """
    Read in all the different sets of parameter changes that were pickled to make
    crucial parts of the experiment definition easily accessible. I don't know how
    many there are, so go until you get an exception.
    """
    try:
        with open(exp_def_fpath, 'rb') as f:
            exp_def = set()
            while True:
                exp_def = exp_def | pickle.load(f)
    except EOFError:
        pass
    return exp_def


def get_arena_dims(generator_str, batch_criteria, exp_num):
    # The scenario dimensions were specified on the command line
    # Format of '(<decomposition depth>.<controller>.[SS,DS,QS,RN,PL]>'
    pair = GeneratorPairParser()(generator_str, batch_criteria)
    if "Generator" not in pair[1]:
        try:
            x, y = pair[1].split('.')[1][2:].split('x')
        except ValueError:
            print("FATAL: Scenario dimensions should be specified on cmdline, but they were not")
            raise
        return (int(x), int(y))
    else:  # Scenario dimensions should be obtained from batch criteria
        return batch_criteria.arena_dims()[exp_num]


def get_n_blocks(cmdopts, batch_criteria, exp_num):
    if cmdopts['n_blocks'] is not None:
        return cmdopts['n_blocks']
    exp_def = unpickle_exp_def(os.path.join(cmdopts["generation_root"],
                                            batch_criteria.gen_exp_dirnames(
        cmdopts)[exp_num],
        "exp_def.pkl"))

    count = 0
    for path, attr, value in exp_def:
        if 'manifest' in path:
            if 'cube' in attr or 'ramp' in attr:
                count += int(value)
    return count

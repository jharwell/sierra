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
import math
import pickle
import yaml
from perf_measures import vcs

kValidBatchCriteria = ['swarm_size', 'swarm_density',
                       'temporal_variance', 'oracle', 'ta_policy_set']


def prettify_scenario_labels(criteria_category, scenarios):
    """
    criteria_category(str): String of batch criteria passed on command line.
    scenarios(list): SORTED list of directories in sierra root representing the scenarios
    that each controller was tested on.

    Returns a sorted list of prettified labels suitable for scenario comparison graphs.

    """
    if "swarm_size" in criteria_category:
        return [s[-4:] for s in scenarios]
    elif "swarm_density" in criteria_category:
        return [s[-5:-2].replace('p', '.') for s in scenarios]
    elif 'temporal_variance' in criteria_category:
        return scenarios
    else:
        return None


def sort_scenarios(criteria_category, scenarios):
    """
    criteria_category(str): String of batch criteria category passed on command line.
    scenarios(list):  List of directories in sierra root representing the scenarios
    that each controller was tested on.

    Returns a sorted list of scenarios.

    """
    if "swarm_size" in criteria_category:
        return scenarios  # No sorting needed
    elif "swarm_density" in criteria_category:
        return sorted(scenarios, key=lambda s: float(s.split('-')[2].split('.')[0][0:3].replace('p', '.')))
    elif 'temporal_variance' in criteria_category:
        return scenarios
    else:
        return None


def swarm_sizes(cmdopts):
    """
    Return the list of swarm sizes used during a batched experiment.
    """
    if not any(c in cmdopts["criteria_category"] for c in kValidBatchCriteria):
        return None
    sizes = []
    for d in exp_dirnames(cmdopts):
        exp_def = unpickle_exp_def(os.path.join(cmdopts['generation_root'],
                                                d,
                                                "exp_def.pkl"))
        for e in exp_def:
            if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                sizes.append(int(e[2]))
    return sizes


def graph_xvals(cmdopts):
    """
    Return a list of batch criteria-specific values to use as the x values for input into graph
    generation.

    Defined for the following batch criteria:

    - swarm_size -> # of robots in each experiment in the batch.
    - swarm_density -> Density [0, inf) of robots in each experiment in the batch.
    - temporal_variance -> Distance between ideal conditions and the variance for each experiment in
                           the batch.

    """
    assert cmdopts['criteria_category'] in kValidBatchCriteria,\
        "FATAL: Invalid batch criteria category '{0}'".format(cmdopts['criteria_category'])

    if "swarm_size" in cmdopts["criteria_category"]:
        ret = swarm_sizes(cmdopts)
    elif "swarm_density" in cmdopts["criteria_category"]:
        ret = __graph_xvals_density(cmdopts)
    elif "temporal_variance" in cmdopts["criteria_category"]:
        ret = [vcs.EnvironmentalCS(cmdopts, x)() for x in range(0, cmdopts["n_exp"])]
    elif 'oracle' in cmdopts['criteria_category']:
        ret = [i for i in range(1, cmdopts['n_exp'] + 1)]
    elif 'ta_policy_set' in cmdopts['criteria_category']:
        ret = [i for i in range(1, cmdopts['n_exp'] + 1)]

    if cmdopts['plot_log_xaxis']:
        return [math.log2(x) for x in ret]
    else:
        return ret


def graph_xlabel(cmdopts):
    """
    Return the X-label that should be used for the graphs of various performance measures across
    batch criteria.
    """
    assert cmdopts['criteria_category'] in kValidBatchCriteria,\
        "FATAL: Invalid batch criteria category '{0}'".format(cmdopts['criteria_category'])

    labels = {
        "swarm_size": "Swarm Size",
        "swarm_density": "Swarm Density",
        "temporal_variance": vcs.method_xlabel(cmdopts["envc_cs_method"]),
        "oracle": "Oracular Swarms",
        "ta_policy_set": "Task Allocation Policy"
    }
    return labels[cmdopts["criteria_category"]]


def exp_dir2num(cmdopts, exp_dir):
    return exp_dirnames(cmdopts).index(exp_dir)


def exp_dirnames(cmdopts, stage1=False):
    """
    Return the set of names that the experiment directories within the batch should have, given the
    batch criteria, sorted.

    stage1(bool): If True, then this function has been called from stage1 where the experiment
                  directories have not been written out yet, and so the directory names cannot
                  easily be obtained via a simple os.listdir(), and need to be obtained from .pkl
                  files that were written under /tmp for exactly this purpose.
    """
    assert cmdopts['criteria_category'] in kValidBatchCriteria,\
        "FATAL: Invalid batch criteria category '{0}'".format(cmdopts['criteria_category'])

    if stage1:
        return __exp_dirnames_stage1(cmdopts)
    else:
        return __exp_dirnames_general(cmdopts)


def exp_dirname(cmdopts, exp_num, stage1=False):
    """
    Return the name of the directory for the specified experiment number within the batch.

    stage1(bool): If True, then this function has been called from stage1 where the experiment
                  directories have not been written out yet, and so the directory names cannot
                  easily be obtained via a simple os.listdir(), and need to be obtained from .pkl
                  files that were written under /tmp for exactly this purpose.
    """
    return exp_dirnames(cmdopts, stage1)[exp_num]


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


def n_exp(cmdopts):
    main_config = yaml.load(open(os.path.join(cmdopts['config_root'],
                                              'main.yaml')))

    exps = [i for i in os.listdir(cmdopts["generation_root"]) if
            os.path.isdir(os.path.join(cmdopts["generation_root"], i)) and i not in
            main_config['sierra']['collate_csv_leaf']]
    return len(exps)


# Private functions
def __exp_dirnames_stage1(cmdopts):
    # We don't actually need the sizes themselves, just the # of sizes used (duplicate sizes OK)
    # so we know how many experiments there are.
    if not cmdopts['named_exp_dirs']:
        return ['exp' + str(x) for x in range(0, len(__swarm_sizes_from_pkl()))]

    criteria_str = cmdopts['criteria_category'] + '.' + cmdopts['criteria_def']

    # We are using named experiment dirs
    criteria = __import__("variables.{0}".format(
        cmdopts['criteria_category']), fromlist=["*"])
    criteria_generator = getattr(criteria, "Factory")(criteria_str)()

    if any(b in cmdopts['criteria_category'] for b in ['swarm_size', 'swarm_density', 'oracle', 'ta_policy_set']):
        return criteria_generator.gen_exp_dirnames(criteria_str)
    elif 'temporal_variance' in cmdopts['criteria_category']:
        assert False,\
            "FATAL: Named exp dirs not supported with temporal variance batch criteria"


def __exp_dirnames_general(cmdopts):
    main_config = yaml.load(open(os.path.join(cmdopts['config_root'],
                                              'main.yaml')))

    dirs = [i for i in os.listdir(cmdopts["generation_root"]) if
            os.path.isdir(os.path.join(cmdopts["generation_root"], i)) and i not in
            main_config['sierra']['collate_csv_leaf']]

    if not cmdopts['named_exp_dirs']:
        return sorted(dirs, key=lambda e: int(e[3:]))

    # We are using named experiment dirs
    if 'swarm_size' in cmdopts['criteria_category']:
        return sorted(dirs, key=lambda e: int(e[4:]))
    elif 'swarm_density' in cmdopts['criteria_category']:
        return sorted(dirs, key=lambda e: int(e[8:]))
    elif 'temporal_variance' in cmdopts['criteria_category']:
        assert False,\
            "FATAL: Named exp dirs not supported with temporal variance batch criteria"
    elif 'oracle' in cmdopts['criteria_category']:
        return dirs
    elif 'ta_policy_set' in cmdopts['criteria_category']:
        return dirs


def __swarm_sizes_from_pkl():
    """
    Retrieve the swarm sizes from temporary .pkl files written during stage1. Used to extract # of
    experiments.
    """
    sizes = []
    for d in os.listdir('/tmp'):
        pkl_path = os.path.join('/tmp', d)
        if 'sierra_pkl' in d and os.path.isfile(pkl_path):
            exp_def = unpickle_exp_def(pkl_path)
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    sizes.append(int(e[2]))

    return sorted(sizes)


def __graph_xvals_density(cmdopts):
    """
    Compute the X-values for graphs when the 'swarm_density' batch criteria is used.
    """
    densities = []
    for i in range(0, cmdopts["n_exp"]):
        pickle_fpath = os.path.join(cmdopts["generation_root"],
                                    exp_dirname(cmdopts, i),
                                    "exp_def.pkl")
        exp_def = unpickle_exp_def(pickle_fpath)
        for e in exp_def:
            if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                n_robots = int(e[2])
            if e[0] == ".//arena" and e[1] == "size":
                x, y, z = e[2].split(",")
        densities.append(n_robots / (int(x) * int(y)))
    return densities

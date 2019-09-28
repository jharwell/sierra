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

from variables.base_variable import BaseVariable
import os
import pickle
import yaml
import utils


class BatchCriteria(BaseVariable):
    """
    Defines the list of sets of changes to make to a template input file in order to run a related
    set of of experiments.

    Attributes:
      cmdline_str(str): Unparsed batch criteria string from command line.
      main_config(dict): Parsed dictionary of main YAML configuration.
      batch_generation_root(str): Absolute path to the directory where batch experiment directories
                                  should be created.
    """

    def __init__(self, cmdline_str, main_config, batch_generation_root):
        self.cmdline_str = cmdline_str
        self.main_config = main_config
        self.batch_generation_root = batch_generation_root

        self.cat_str = cmdline_str.split('.')[0]
        self.def_str = '.'.join(cmdline_str.split('.')[1:])

    def gen_attr_changelist(self):
        return []

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []

    def arena_dims(self):
        """
        Return the arena dimensions used for each experiment in the batch. Not applicable to all
        criteria.
        """
        dims = []
        for exp in self.gen_attr_changelist():
            for c in exp:
                if c[0] == ".//arena" and c[1] == "size":
                    x, y, z = c[2].split(',')
                    dims.append((int(x), int(y)))
        assert len(dims) > 0, "Scenario dimensions not contained in batch criteria"
        return dims

    def exp_dir2num(self, cmdopts, exp_dir):
        return self.gen_exp_dirnames(cmdopts).index(exp_dir)

    def n_exp(self):
        exps = [i for i in os.listdir(self.batch_generation_root) if
                os.path.isdir(os.path.join(self.batch_generation_root, i)) and i not in
                self.main_config['sierra']['collate_csv_leaf']]
        return len(exps)

    def cleanup_pkl_files(self, batch_root):
        defs = list(self.gen_attr_changelist())
        for i in range(0, len(defs)):
            pkl_path = os.path.join(batch_root, 'batch_pkl{0}'.format(i))
            if os.path.exists(pkl_path):
                os.remove(pkl_path)

    def pickle_exp_defs(self, cmdopts):
        defs = list(self.gen_attr_changelist())
        for i in range(0, len(defs)):
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            pkl_path = os.path.join(self.batch_generation_root, exp_dirname, 'exp_def.pkl')
            with open(pkl_path, 'ab') as f:
                pickle.dump(defs[i], f)

    def scaffold_exps(self, xml_luigi, batch_config_leaf, cmdopts):
        defs = list(self.gen_attr_changelist())
        for i in range(0, len(defs)):
            exp_dirname = self.gen_exp_dirnames(cmdopts)[i]
            exp_generation_root = os.path.join(self.batch_generation_root,
                                               str(exp_dirname))
            os.makedirs(exp_generation_root, exist_ok=True)
            for path, attr, value in defs[i]:
                xml_luigi.attr_change(path, attr, value)

                xml_luigi.output_filepath = os.path.join(exp_generation_root,
                                                         batch_config_leaf)
                xml_luigi.write()
        assert len(defs) == len(os.listdir(self.batch_generation_root)),\
            "FATAL: Size of batch criteria({0}) != # exp dirs ({1}): possibly caused by duplicate "\
            "named exp dirs... ".format(len(defs),
                                        len(os.listdir(self.batch_generation_root)))

    def is_binary(self):
        """
        Returns True if this class is a binary batch criteria instance, and False otherwise.
        """
        raise NotImplementedError

    def is_univar(self):
        """
        Returns True if this class is a unary batch criteria instance, and False otherwise.
        """
        raise NotImplementedError

    def gen_exp_dirnames(self, cmdopts):
        """
        Generate list of strings from the current changelist to use for directory names within a
        batched experiment.
        """
        raise NotImplementedError

    def sc_graph_labels(self, scenarios):
        """
        scenarios(list):  List of directories in sierra root representing the scenarios
                          that each controller was tested on.

        Returns a sorted list of prettified labels suitable for scenario comparison graphs from the
        directory names used for each scenario. Directory names are determined by controller
        used, batch criteria used, or both, so disambiguation is needed on a per-criteria basis.

        """
        raise NotImplementedError

    def sc_sort_scenarios(self, scenarios):
        """
        scenarios(list):  List of directories in sierra root representing the scenarios
                          that each controller was tested on. Directory names are determined by
                          controller used, batch criteria used, or both, so disambiguation is needed
                          on a per-criteria basis.

        Returns a sorted list of scenarios.

        """
        raise NotImplementedError

    def graph_xvals(self, cmdopts, exp_dirs=None):
        """
        cmdopts(dict): Dictionary of parsed command line options.
        exp_dirs(list): If not be None, then these directories will be used to calculate the swarm
                        sizes, rather than the results of gen_exp_dirnames().

        Return a list of criteria-specific values to use as the x values for input into graph
        generation.

        """
        raise NotImplementedError

    def graph_yvals(self, cmdopts, exp_dirs=None):
        """
        cmdopts(dict): Dictionary of parsed command line options.
        exp_dirs(list): If not be None, then these directories will be used to calculate the swarm
                        sizes, rather than the results of gen_exp_dirnames().

        Return a list of criteria-specific values to use as the y values for input into graph
        generation.

        """
        raise NotImplementedError

    def graph_xlabel(self, cmdopts):
        """
        Return the X-label that should be used for the graphs of various performance measures across
        batch criteria.
        """
        raise NotImplementedError

    def graph_ylabel(self, cmdopts):
        """
        Return the Y-label that should be used for the graphs of various performance measures across
        batch criteria. Only needed by bivar batch criteria.
        """
        raise NotImplementedError


class UnivarBatchCriteria(BatchCriteria):
    def is_bivar(self):
        return False

    def is_univar(self):
        return True

    def swarm_sizes(self, cmdopts, exp_dirs=None):
        """
        Return the list of swarm sizes used the batched experiment, sorted.

        cmdopts(dict): Dictionary of parsed command line options.
        exp_dirs(list): If not be None, then these directories will be used to calculate the swarm
                        sizes, rather than the results of gen_exp_dirnames().
        """
        sizes = []
        if exp_dirs is not None:
            dirs = exp_dirs
        else:
            dirs = self.gen_exp_dirnames(cmdopts)

        for d in dirs:
            exp_def = utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                          d,
                                                          "exp_def.pkl"))
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    sizes.append(int(e[2]))
        return sizes


class BivarBatchCriteria(BatchCriteria):
    """
    Combination of the definition of two separate batch criteria.

    """

    def __init__(self, criteria1, criteria2):
        BatchCriteria.__init__(self,
                               '+'.join([criteria1.cmdline_str, criteria2.cmdline_str]),
                               criteria1.main_config,
                               criteria1.batch_generation_root)
        self.criteria1 = criteria1
        self.criteria2 = criteria2

    def gen_attr_changelist(self):
        list1 = self.criteria1.gen_attr_changelist()
        list2 = self.criteria2.gen_attr_changelist()
        ret = []
        for l1 in list1:
            for l2 in list2:
                ret.append(l1 | l2)

        return ret

    def gen_tag_rmlist(self):
        ret = self.criteria1.gen_tag_rmlist().extend(self.criteria2.gen_tag_rmlist())
        return ret

    def gen_tag_addlist(self):
        ret = self.criteria1.gen_tag_addlist().extend(self.criteria2.gen_tag_addlist())
        return ret

    def gen_exp_dirnames(self, cmdopts):
        list1 = self.criteria1.gen_exp_dirnames(cmdopts)
        list2 = self.criteria2.gen_exp_dirnames(cmdopts)
        ret = []
        for l1 in list1:
            for l2 in list2:
                ret.append('+'.join(['c1-' + l1, 'c2-' + l2]))

        return ret

    def swarm_sizes(self, cmdopts):
        """
        Return a 2D array of swarm swarm sizes used the batched experiment, in the same order as the
        directories returned from gen_exp_dirnames() for each criteria along each axis
        """
        dirs = self.gen_exp_dirnames(cmdopts)

        sizes = [[0 for col in self.criteria2.gen_exp_dirnames(
            cmdopts)] for row in self.criteria1.gen_exp_dirnames(cmdopts)]

        for d in dirs:
            exp_def = utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                          d,
                                                          "exp_def.pkl"))
            for e in exp_def:
                if not (e[0] == ".//arena/distribute/entity" and e[1] == "quantity"):
                    continue

                index = dirs.index(d)
                i = int(index / len(self.criteria1.gen_attr_changelist()))
                j = index % len(self.criteria2.gen_attr_changelist())
                sizes[i][j] = int(e[2])

        return sizes

    def is_bivar(self):
        return True

    def is_univar(self):
        return False

    def sc_graph_labels(self, scenarios):
        raise NotImplementedError

    def sc_sort_scenarios(self, scenarios):
        raise NotImplementedError

    def graph_xvals(self, cmdopts, exp_dirs=None):
        dirs = []
        for c1 in self.criteria1.gen_exp_dirnames(cmdopts):
            for x in self.gen_exp_dirnames(cmdopts):
                if c1 in x.split('+')[0]:
                    dirs.append(x)
                    break

        assert len(dirs) == len(self.criteria1.gen_exp_dirnames(cmdopts)),\
            "FATAL: Bad xvals calculation"
        return self.criteria1.graph_xvals(cmdopts, dirs)

    def graph_yvals(self, cmdopts, exp_dirs=None):
        dirs = []
        for c2 in self.criteria2.gen_exp_dirnames(cmdopts):
            for x in self.gen_exp_dirnames(cmdopts):
                if c2 in x.split('+')[1]:
                    dirs.append(x)
                    break

        assert len(dirs) == len(self.criteria2.gen_exp_dirnames(cmdopts)),\
            "FATAL: Bad yvals calculation"

        return self.criteria2.graph_xvals(cmdopts, dirs)

    def graph_xlabel(self, cmdopts):
        return self.criteria1.graph_xlabel(cmdopts)

    def graph_ylabel(self, cmdopts):
        return self.criteria2.graph_xlabel(cmdopts)


def Factory(args):
    if 1 == len(args.batch_criteria):
        return __UnivarFactory(args, args.batch_criteria[0])
    elif 2 == len(args.batch_criteria):
        assert args.batch_criteria[0] != args.batch_criteria[1],\
            "FATAL: Duplicate batch criteria passed"
        return __BivarFactory(args)
    else:
        assert False, "FATAL: At most 2 batch criterias can be specified on the cmdline"


def __UnivarFactory(args, cmdline_str):
    """
    Construct a batch criteria object from a single cmdline argument.
    """
    category = cmdline_str.split('.')[0]

    module = __import__("variables.{0}".format(category), fromlist=["*"])
    main_config = yaml.load(open(os.path.join(args.config_root, 'main.yaml')))

    return getattr(module, "Factory")(cmdline_str,
                                      main_config,
                                      args.generation_root)()


def __BivarFactory(args):
    criteria0 = __UnivarFactory(args, args.batch_criteria[0])
    criteria1 = __UnivarFactory(args, args.batch_criteria[1])
    return BivarBatchCriteria(criteria0, criteria1)

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

    def swarm_sizes(self, cmdopts):
        """
        Return the list of swarm sizes used the batched experiment, in the same order as the
        directories returned from gen_exp_dirnames().
        """
        sizes = []
        for d in self.gen_exp_dirnames(cmdopts):
            exp_def = utils.unpickle_exp_def(os.path.join(self.batch_generation_root,
                                                          d,
                                                          "exp_def.pkl"))
            for e in exp_def:
                if e[0] == ".//arena/distribute/entity" and e[1] == "quantity":
                    sizes.append(int(e[2]))
        return sizes

    def arena_dims(self):
        """
        Return the arena dimensions used for each experiment in the batch. Not applicable to all
        criteria.
        """
        dims = []
        for exp in self.gen_attr_changelist():
            print(exp)
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

    def graph_xvals(self, cmdopts):
        """
        cmdopts(dict): Dictionary of parsed command line options.

        Return a list of batch criteria-specific values to use as the x values for input into graph
        generation.

        """
        raise NotImplementedError

    def graph_xlabel(self, cmdopts):
        """
        Return the X-label that should be used for the graphs of various performance measures across
        batch criteria.
        """
        raise NotImplementedError


def Factory(args):
    if args.batch_criteria is None:
        category = None
    else:
        category = args.batch_criteria.split('.')[0]

    module = __import__("variables.{0}".format(category), fromlist=["*"])
    main_config = yaml.load(open(os.path.join(args.config_root, 'main.yaml')))

    return getattr(module, "Factory")(args.batch_criteria,
                                      main_config,
                                      args.generation_root)()

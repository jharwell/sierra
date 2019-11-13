# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the terms of the GNU
#  General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#
"""
Command line parsing and validation classes.
"""

import argparse
import os


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass


class Cmdline:
    """
    Defines the command line arguments for SIERRA using :class:`argparse`
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='sierra',
                                              formatter_class=HelpFormatter)
        self.parser.add_argument("--template-input-file",
                                 metavar="filepath",
                                 help="""

                                 The template ``.argos`` input file for the batched experiment.

                                 Use=stage[1, 2, 3, 4}; can be omitted if only running other stages.

                                 """)

        self.parser.add_argument("--sierra-root",
                                 metavar="dirpath",
                                 help="""

                                 Root directory for all sierra generated/created files.

                                 Subdirectories for controllers, scenarios, experiment/simulation
                                 inputs/outputs will be created in this directory as needed. Can persist
                                 between invocations of sierra.

                                 """,
                                 default=os.path.expanduser("~") + "/exp")
        self.parser.add_argument("--config-root",
                                 help="""

                                 Root directory containing all .yaml files used by sierra for configuration.

                                 Within this directory, the following files must be present when running a
                                 stage that utilizes them:

                                 - ``intra-graphs.yaml`` - Configuration for intra-experiment graphs
                                 - ``inter-graphs.yaml`` - Configuration for inter-experiment graphs
                                 - ``controllers.yaml`` - Configuration for controllers (input file/graph generation).

                                 """,
                                 default="config")

        self.parser.add_argument("--controller",
                                 metavar="{depth0, depth1, depth2}.<controller>",
                                 help="""

                                 Which controller robots will use in the experiment. All robots use the same
                                 controller (homogeneous swarms).

                                 Valid controllers:

                                 - depth0.{CRW, DPO, MDPO},
                                 - depth1.{BITD_DPO, OBITD_DPO},
                                 - depth2.{BIRTD_DPO, OBIRTD_DPO}

                                 Use=stage{1,2,3,4}; can be omitted otherwise.

                                 """)

        self.parser.add_argument("--scenario",
                                 metavar="<block dist>.AxB[xC]",
                                 help="""

                                 Which scenario the defined controller should be run in. Scenario=block
                                 distribution type + arena dimensions.

                                 Valid block distribution types:

                                 - ``RN`` - Random
                                 - ``SS`` - Single source
                                 - ``DS`` - Dual source
                                 - ``QS`` - Quad source
                                 - ``PL`` - Power law

                                 A,B,C are the scenario X,Y,Z dimensions respectively (which can be any postive integer
                                 values). The X,Y dimensions are required, the Z dimension is optional and defaults to
                                 1.0 if omitted.

                                 Use=stage{1,2,3,4}; can be omitted otherwise.

                                 """)

        self.parser.add_argument("--batch-criteria",
                                 metavar="[<category>.<definition>,...]",
                                 help="""

                                 Definition of criteria(s) to use to defined the batched experiment.

                                 Specified as a list of 0 or 1 space separated strings, each with the following
                                 general structure:

                                 ``<category>.<definition>``

                                 ``<category>`` must be a filename from the ``variables/`` directory, and
                                 ``<definition>`` must be a parsable name (according to the requirements of the criteria
                                 defined by the parser for ``<category>``).

                                 Not all files within the ``variables/`` directory contain classes which can be used as
                                 top level batch criteria; the ones that can are:

                                 - swarm_size
                                 - constant_density
                                 - ta_policy_set
                                 - oracle
                                 - temporal_variance

                                 Use=stage{1,2,3,4,5}.

                                 """,
                                 nargs='+',
                                 default=[])

        self.parser.add_argument("--pipeline",
                                 metavar="stages",
                                 help="""
                                 Define which stages of the experimental pipeline to run:

                                 Stage1: Generate the experiment definition from the template input file, batch
                                 criteria, and other command line options. Part of default pipeline.

                                 Stage2: Run the batched experiment on a previously generated experiment. Part of
                                 default pipeline.

                                 Stage3: Process experimental results after running the batched experiment. Part of
                                 default pipeline.

                                 Stage4: Perform graph generation after processing results for a batched
                                 experiment. Part of default pipeline.

                                 Stage5: Perform graph generation for comparing controllers AFTER graph
                                 generation for batched experiments has been run. It is assumed that if this
                                 option is passed that the # experiments/batch criteria is the same for all
                                 controllers that will be compared. Not part of default pipeline.

                                 """,
                                 type=int,
                                 nargs='*',
                                 default=[1, 2, 3, 4]
                                 )

        self.parser.add_argument("--named-exp-dirs",
                                 help="""

                                 When passed, the names of directories within a batch experiment will be obtained from
                                 the batch criteria, rather than generically as ``expX``, (``X`` is unique non-negative
                                 integer) for each experiment in the batch.

                                 This option is NOT compatible with the following batch criteria:

                                 - temporal_variance
                                 """,
                                 action='store_true',
                                 default=False)

        self.parser.add_argument("--hpc-env",
                                 help="""

                                 The value of this argument determines if the ``--n-threads``, --physics-n-engines``,
                                 and ``--n-sims`` options will be inherited from the specified HPC
                                 environment. Otherwise, they must be specified on the cmdline.

                                 Value values:

                                 - MSI - The following PBS environment variables are used to infer the # threads, #
                                 physics engines, and # simulations to run, respectively: ``PBS_NUM_PPN``,
                                 ``PBS_NUM_PPN``, ``PBS_NUM_NODES``. ``MSICLUSTER`` is used to determine the names of
                                 ARGoS executables, ``PBS_NODEFILE`` and ``PBS_JOBID`` are used to launch simulations.

                                 """,
                                 choices=['MSI', None],
                                 default=None)

        self.parser.add_argument("--log-level",
                                 choices=["INFO", "DEBUG"],
                                 help="""

                                 The level of logging to use when running SIERRA.

                                 """,
                                 default="INFO")

        stage1 = self.parser.add_argument_group('Stage1: Generating experiments')

        stage1.add_argument("--time-setup",
                            help="""

                            The simulation time setup to use, which sets the simulation duration and metric reporting
                            interval.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            default="time_setup.T5000")

        stage1.add_argument("--n-sims",
                            type=int,
                            help="""

                            How many simulations should be averaged together to form a single experiment.

                            If ``--exec-method=hpc`` then the value of this option will be inherited from the HPC
                            environment specified by ``--hpc-env`` (can still be override on cmdline).

                            If ``exec-method=local`` then this option is required.

                            Use=stage{1}; can be omitted otherwise.

                            """)

        stage1.add_argument("--n-threads",
                            type=int,
                            help="""

                            How many ARGoS simulation threads to use for each simulation in each experiment.

                            If ``--exec-method=hpc`` then the value of this option will be inherited from the HPC
                            environment specified by ``--hpc-env`` (can still be override on cmdline).

                            If ``exec-method=local`` then this option is required.

                            Use=stage{1}; can be omitted otherwise.

                            """)

        stage1.add_argument("--static-cache-blocks",
                            help="""

                            # of blocks used when the static cache is respawned (depth1 controllers only).
                            Specify the

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            default=None)

        # Physics engines options
        physics = self.parser.add_argument_group('Stage1: Physics',
                                                 'Physics engine options for stage1')

        physics.add_argument("--physics-engine-type",
                             choices=['dynamics2d', 'dynamics3d', 'pointmass3d'],
                             help="""

                             Specify the type of physics engine to use, choosing one of the types that ARGoS supports.

                             """,
                             default='dynamics2d')

        physics.add_argument("--physics-n-engines",
                             choices=[1, 4, 8, 16, 24],
                             type=int,
                             help="""

                            # of physics engines to use during simulation (yay ARGoS!). If n > 1, the engines will
                            The
                            be tiled in a uniform grid within the arena (X and Y spacing may not be the same depending
                            on dimensions and how many engines are chosen, however), extending upward in Z to the height
                            specified by ``--scenario``.

                            If ``--exec-method=hpc`` then the value of this option will be inherited from the HPC
                            environment specified by ``--hpc-env`` (can still be overriden on cmdline).

                            If ``exec-method=local`` then this option is required.

                            Use=stage{1}; can be omitted otherwise.

                             """)
        physics.add_argument("--physics-iter-per-tick",
                             type=int,
                             help="""

                            The # of iterations all physics engines should perform per tick each time the
                            controller loops are run.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                             default=10)

        # Robot options
        robots = self.parser.add_argument_group('Stage1: Robots',
                                                'Robot options (stage1 only)')

        robots.add_argument("--with-robot-rab",
                            help="""

                            Include the Range and Bearing sensor/actuator in the generated input files for the
                            footbot. Otherwise, those tags are removed in the template input file if they exist.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)

        robots.add_argument("--with-robot-leds",
                            help="""

                            Include the footbot robot LED actuator in the generated input files. Otherwise, it is
                            removed if it exists.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)

        robots.add_argument("--with-robot-battery",
                            help="""

                            Include the robot battery sensor in the generated input files. Otherwise, it is removed if
                            it exists.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)

        robots.add_argument("--n-blocks",
                            help="""

                            # blocks that should be used in the simulation (evenly split between cube and
                            Specify the
                            ramp). Can be used to override batch criteria, or to supplement experiments that do not set
                            it so that manual modification of input file is unneccesary.

                            Use=stage{1}; can be omitted otherwise.
                            """,
                            type=int,
                            default=None)

        stage2 = self.parser.add_argument_group('Stage2: Running experiments')
        stage2.add_argument("--exec-method",
                            help="""

                            Specify the execution method to use when running experiments.

                            ``local` - Run the maximum # of simulations simultaneously on the local machine using GNU
                            parallel. # of simultaneous simulations is determined by # cores on machine / # ARGoS
                            threads.

                            ``hpc`` - Use GNU parallel in an HPC environment to run the specified # of simulations
                            simultaneously on a computing cluster. The ``$MSICLUSTER`` environment variable will be used
                            to identify the cluster sierra was invoked on and select the appropriate ARGoS
                            executable. For example, if ``$MSICLUSTER=itasca``, then ARGoS will be invoked via
                            ``argos3-itasca``. This option is provided so that in HPC environments with multiple
                            clusters with different architectures ARGoS can be compiled natively for each for maximum
                            performance.

                            Use=stage{2}; can be omitted otherwise.

                            """,
                            default="local")
        stage2.add_argument("--exec-exp-range",
                            help="""

                            Experiment numbers from the batch to run. Specified in the form
                            ``min_exp_num:max_exp_num``. If omitted, runs all experiments in the batch (default
                            behavior).

                            Use=stage{2}; can be omitted otherwise.

                            """)
        stage2.add_argument("--exec-resume",
                            help="""

                            Resume a batched experiment that was killed/stopped/etc last time sierra was run.

                            Use=stage{2}; can be omitted otherwise.

                            """,
                            action='store_true',
                            default=False)
        stage3 = self.parser.add_argument_group('Stage3: Preprocessing experiment results')
        stage3.add_argument('--exp-no-verify',
                            help="""

                            If TRUE, then the verification step will be skipped for the batched experiment, and outputs
                            will be averaged directly. If not all ``.csv`` files exist for all experiments and have the
                            # of rows, then SIERRA might crash during stage4, and NaNs will probably show up in
                            performance measure calculations. Use at your own risk. Verification can take a long time
                            if the # simulations for each experiment in the batch is large.

                            Use=stage{3}; can be omitted otherwise.

                            """,
                            action='store_true',
                            default=False)
        stage3.add_argument("--gen-stddev",
                            help="""

                            Calculate standard deviation calculated from averaged data and include error bars on all
                            generated intra-experiment linegraphs.

                            Use=stage{3}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)
        stage3.add_argument("--results-process-tasks",
                            help="""

                            Specify what tasks should be performed when processing simulation results before graph
                            generation.

                            Use=stage{3}; can be omitted otherwise.

                            """,
                            choices=['render', 'average', 'all'],
                            default=['all'])

        # Rendering options
        rendering = self.parser.add_argument_group(
            'Stage3: Rendering', 'Rendering options for stage3')
        rendering.add_argument("--with-rendering",
                               help="""

                               Specify that the ARGoS Qt/OpenGL visualization subtree should be left in the input ``.argos``
                               file. By default it is stripped out.

                               Any files in the ``frames/`` directory of each simulation will be rendered into a unique
                               video file with directory using ffmpeg (precise command configurable). This option
                               assumes that [ffmpeg, Xvfb] programs can be found.

                               Use=stage{1,2,3}; can be omitted otherwise.
                               """,
                               action='store_true')

        rendering.add_argument("--render-cmd-opts",
                               help="""

                               Specify the ffmpeg options to appear between the specification of the input .png files
                               and the specification of the output file. The default is suitable for use with ARGoS
                               frame grabbing set to a frames of 1600x1200 to output a reasonable quality video.

                               Use=stage{3}; can be omitted otherwise.

                               """,
                               default="-r 10 -s:v 800x600 -c:v libx264 -crf 25 -filter:v scale=-2:956 -pix_fmt yuv420p")

        rendering.add_argument("--render-cmd-ofile",
                               help="""

                               Specify the output filename and extension for the ffmpeg rendered video.

                               Use=stage{3}; can be omitted otherwise.

                               """,
                               default="video.mp4")

        stage4 = self.parser.add_argument_group('Stage4: Generating graphs')

        stage4.add_argument("--exp-graphs",
                            choices=['intra', 'inter', 'all'],
                            help="""

                            Specify which graphs should be generated: Only intra-experiment graphs, only
                            inter-experiment graphs, or both.

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            default='all')

        stage4.add_argument("--plot-log-xaxis",
                            help="""

                            Place the set of X values used to generate intra- and inter-experiment into the logarithmic
                            (base 2) space. Mainly useful when the batch criteria involves large swarm sizes, so that
                            the plots are more readable.

                            Use=stage{4}; can be omitted otherwise.
                            """,
                            default=False)

        # Variance curve similarity options
        vcs = self.parser.add_argument_group('Stage4: VCS',
                                             'Variance Curve Similarity options for stage4')

        vcs.add_argument("--gen-vc-plots",
                         help="""

                          Generate plots of ideal vs. observed swarm [reactivity, adaptability] for each experiment in
                          the batch.

                          Use=stage{4}; can be omitted otherwise.

                          """,
                         action="store_true")

        vcs.add_argument("--envc-cs-method",
                         help="""

                         Environmental conditions curve similarity method. Specify the method to use to calculate the
                         similarity between curves of applied variance (non-ideal conditions) and ideal conditions
                         (exp0). Only applies for ``temporal_variance`` batch criteria. Valid values:

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between` - Area between the two curves (Jekel2018)
                         - ``frechet` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                         curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="pcm")

        vcs.add_argument("--reactivity-cs-method",
                         help="""

                         Reactivity calculatation curve similarity method. Specify the method to use to calculate the
                         similarity between the inverted applied variance curve for a simulation and the corrsponding
                         performance curve.

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between` - Area between the two curves (Jekel2018)
                         - ``frechet` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                         curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="pcm")
        vcs.add_argument("--adaptability-cs-method",
                         help="""

                         Adaptability calculatation curve similarity method. Specify the method to use to calculate the
                         similarity between the inverted applied variance curve for a simulation and the corrsponding
                         performance curve.

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between` - Area between the two curves (Jekel2018)
                         - ``frechet` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                         curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="pcm")

        stage5 = self.parser.add_argument_group('Stage5', 'General stage5 options')

        stage5.add_argument("--controllers-list",
                            help="""

                            Comma separated list of controllers to compare within ``<sierra root>``. If None, then the
                            default set of controllers will be used for comparison.

                            The first controller in this list will be used for normalization comparison plots, if
                            ``--normalize-comparisons`` is passed.

                            Use=stage{5}; can be omitted otherwise.

                            """,
                            default='depth0.CRW,depth0.DPO,depth1.BITD_DPO,depth2.BIRTD_DPO')

        stage5.add_argument("--controllers-legend",
                            help="""

                            Comma separated list of names to use on the legend for the generated intra-scenario
                            controller comparison graphs (if applicable), specified in the same order as the
                            `--controllers-list`.

                            Use=stage{5}; can be omitted otherwise. If omitted, the raw controller names will be used.
                            """)
        stage5.add_argument("--comparison-type",
                            choices=['raw', 'scale3D', 'scale2D', 'diff3D', 'diff2D'],
                            help="""

                            Specify how controller comparisons should be performed (currently only used for bivariate
                            controller comparisons). Options are:

                            - ``raw`` - Output raw performance measures. This results in a set single stacked 3D surface plots
                              comparing all controllers (identical plots, but view from different angles). Uses
                              ``--controllers-legend`` if passed for legend.

                            - ``scale3D`` - Scale controller performance measures against those of the controller
                              of primary interest by dividing. This results in a set single stacked 3D surface plots
                              comparing all controllers (identical plots, but view from different angles). Uses
                              ``--controllers-legend`` if passed for legend.

                            - ``scale2D`` - Scale controller performance measures against those of the controller
                              of primary interest by dividing. This results in a set of 2D heatmaps, one for each
                              controller paired against the primary controller of interest.

                            - ``diff3D`` - Subtract the performance measure of the controller of primary interest from
                              each controller (including the primary). This results in a set single stacked 3D surface plots
                              comparing all controllers (identical plots, but view from different angles), in which the
                              controller of primary interest forms an (X,Y) plane at Z=0. Uses
                              ``--controllers-legend`` if passed for legend.

                            - ``diff2D`` - Subtract the performance measure of the controller of primary interest
                              against all other controllers, pairwise, outputting one 2D heatmap per comparison.

                            """,
                            default='raw')

        stage5.add_argument("--bc-univar",
                            help="""

                            Specify that the batch criteria is univariate. This cannot be deduced from the command line
                            ``--batch-criteria`` argument in all cases because we are comparing controllers `across`
                            scenarios, and each scenario (potentially) has a different batch criteria definition, which
                            will result in (potentially) erroneous comparisons if we don't re-generate the batch
                            criteria for each scenaro we compare controllers within.

                            """,
                            action='store_true')

        stage5.add_argument("--bc-bivar",
                            help="""

                            Specify that the batch criteria is bivariate. This cannot be deduced from the command line
                            ``--batch-criteria`` argument in all cases because we are comparing controllers `across`
                            scenarios, and each scenario (potentially) has a different batch criteria definition, which
                            will result in (potentially) erroneous comparisons if we don't re-generate the batch
                            criteria for each scenaro we compare controllers in.

                            """,
                            action='store_true')

    def __environ_or_required(key, default=None):
        if os.environ.get(key):
            return {'default': os.environ.get(key)}
        elif default is not None:
            return {'default': default}
        else:
            return {'required': True}


class HPCEnvInheritor():
    def __init__(self, env_type):
        self.env_type = env_type

    def __call__(self, args):
        if self.env_type is None:
            return args

        keys = ['MSICLUSTER', 'PBS_NUM_PPN', 'PBS_NUM_NODES']

        for k in keys:
            assert k in os.environ, \
                "FATAL: Attempt to run sierra in non-MSI environment: '{0}' not found".format(k)

        if 'MSI' == self.env_type:
            if args.physics_n_engines is None:
                args.physics_n_engines = int(os.environ['PBS_NUM_PPN'])
            if args.n_threads is None:
                args.n_threads = int(os.environ['PBS_NUM_PPN'])
            if args.n_sims is None:
                args.n_sims = int(os.environ['PBS_NUM_NODES'])
        else:
            assert False,\
                "FATAL: Bad HPC environment inheritance specification {0}".format(self.env_type)

        return args


class CmdlineValidator():
    """
    Validate the parsed command line arguments to ensure that the pipeline will work properly in all stages, given the
    options that were passed.
    """

    def __call__(self, args):
        assert len(args.batch_criteria) <= 2, "FATAL: Too many batch criteria passed"
        if 2 == len(args.batch_criteria):
            assert args.batch_criteria[0] != args.batch_criteria[1],\
                "FATAL: Duplicate batch criteria passed"

        if args.gen_stddev:
            assert 1 == len(args.batch_criteria),\
                "FATAL: Stddev generation only supported with univariate batch criteria"

        assert isinstance(args.batch_criteria, list),\
            'FATAL Batch criteria not passed as list on cmdline'

        if 'local' == args.exec_method and any([1, 2]) in args.pipeline:
            assert args.physics_n_engines is not None, '--physics-n-engines is required for --exec-method=local'
            assert args.n_threads is not None, '--n-threads is required for --exec-method=local'
            assert args.n_sims is not None, '--n-sims is required for --exec-method=local'

        if 5 in args.pipeline:
            assert args.bc_univar or args.bc_bivar,\
                '--bc-univar or --bc-bivar is required for stage 5'


def sphinx_argparse_object():
    """
    Return a handle to the argparse object for SIERRA in order for sphinx to autogenerate nice documentation from it.
    """
    return Cmdline().parser

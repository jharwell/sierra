"""
Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the terms of the GNU
  General Public License as published by the Free Software Foundation, either version 3 of the
  License, or (at your option) any later version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""

import argparse
import os.path


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass


class Cmdline:
    def init(self):
        """
        Defines the command line arguments for sierra. Returns a parser with the definitions.
        """
        parser = argparse.ArgumentParser(prog='sierra',
                                         formatter_class=HelpFormatter)
        parser.add_argument("--template-config-file",
                            metavar="filepath",
                            help="""

                            The template configuration file for the experiment. Use=stage[1, 2, 3, 4}; can be omitted if
                            only running other stages.

                            """)

        parser.add_argument("--sierra-root",
                            metavar="dirpath",
                            help="""

                            Root directory for all sierra generated/created files. Subdirectories for controllers,
                            scenarios, experiment/simulation inputs/outputs will be created in this directory as
                            needed. Can persist between invocations of sierra.

                            """,
                            default=os.path.expanduser("~") + "/exp")
        parser.add_argument("--config-root",
                            help="""

                            Path to root directory containing all .yaml files used by SIERRA for
                            configuration. Within this directory, the following files must be
                            present when running a stage that utilizes them:

                            intra-graphs.yaml - Configuration for intra-experiment graphs
                            inter-graphs.yaml - Configuration for inter-experiment graphs
                            controllers.yaml - Configuration for controllers (input file/graph generation)

                            """,
                            default="config")
        parser.add_argument("--generation-root",
                            metavar="dirpath",
                            help="""

                            Root directory to save generated experiment input files, or the directory which will contain
                            directories for each experiment's input files, for batch mode. You should almost never have
                            to change this from the default.

                            Use=stage{1,2,3}; can be omitted otherwise.
                            Default=<sierra_root>/<controller>/<scenario>/exp-inputs.

                            """)
        parser.add_argument("--output-root",
                            metavar="dirpath",
                            help="""

                            Root directory for saving simulation outputs a single experiment, or the root directory
                            which will contain directories for each experiment's outputs for batch mode). You should
                            almost never have to change this from the default.

                            Use=stage{3,4,5}; can be omitted otherwise.
                            Default=<sierra_root>/<controller>/<scenario>/exp-outputs

                            """)
        parser.add_argument("--graph-root",
                            metavar="dirpath",
                            help="""

                            Root directory for saving generated graph files for a single experiment, or the root
                            directory which will contain directories for each experiment's generated graphs for batch
                            mode. You should almost never have to change this from the default.

                            Use=stage{4,5}; can be omitted otherwise.
                            default=<sierra_root>/<controller>/<scenario>/graphs.
                            """)

        parser.add_argument("--controller",
                            metavar="{depth0, depth1, depth2}.<controller>",
                            help="""

                            Which controller robots will use in the experiment.

                            Valid controllers: {depth0.{CRW, DPO, MDPO},
                                                depth1.{BITD_DPO, OBITD_DPO},
                                                depth2.{BIRTD_DPO, OBIRTD_DPO}.

                            Use=stage{1,2,3,4}; can be omitted otherwise.

                            """)

        parser.add_argument("--scenario",
                            metavar="<block dist>.AxB",
                            help="""

                            Which scenario the defined controller should be run in. Scenario=block
                            distribution type + arena dimensions.

                            Valid block distribution types: {RN, SS, DS, QS, PL}, which correspond
                            to {random, single source, dual source, quad source, powerlaw} block
                            distributions.

                            A and B are the scenario X and Y dimensions (which can be any non-negative integer values);
                            the dimensions can be omitted for some batch criteria.

                            Use=stage{1,2,3,4}; can be omitted otherwise.

                            """)

        parser.add_argument("--batch-criteria",
                            metavar="[<filename>.<class name>,...]",
                            help="""

                            Name of criteria(s) to use to generate the batched experiments. <filename> must be from the
                            variables/ directory, and <class name> must be a class within that file. Not all classes
                            within the variables/ directory can be used as top level batch criteria; the ones that can
                            are:

                            - swarm_size
                            - swarm_density
                            - ta_policy_set
                            - oracle
                            - temporal_variance

                            Use=stage{1,2,3,4,5}.

                            """,
                            nargs='+',
                            default=[])

        parser.add_argument("--pipeline",
                            metavar="stages",
                            help="""


                            Define which stages of the experimental pipeline to run:

                            Stage1: Generate the config files and command file for an experiment/set of experiments.
                            Stage2: Run the experiments on previously generated set of input files for an experiment/set
                                    of experiments. Part of default pipeline.
                            Stage3: Perform CSpV averaging on a previously run experiment/set of experiments. Part of
                                    default pipeline.
                            Stage4: Perform graph generation on a previous run experiments/set of experiments. Part of
                                    default pipeline.
                            Stage5: Perform graph generation for comparing controllers AFTER graph generation for
                                    batched experiments has been run. It is assumed that if this option is passed that
                                    the # experiments/batch criteria is the same for all controllers that will be
                                    compared. Not part of default pipeline.

                            Specified as a space-separated list after the option.
                            """,
                            type=int,
                            nargs='*',
                            default=[1, 2, 3, 4]
                            )

        parser.add_argument("--named-exp-dirs",
                            help="""

                            If TRUE, then the names of directories within a batch experiment will be
                            obtained from the batch criteria, rather than named 'expX'. Note that
                            this optional is NOT compatible with the following batch criteria:

                            - temporal_variance
                            """,
                            action='store_true',
                            default=False)

        stage1 = parser.add_argument_group('stage1 (Generating experimental inputs)')

        stage1.add_argument("--time-setup",
                            help="""

                            The simulation time setup to use, which sets duration and metric
                            reporting interval. For options, see time_setup.py

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            default="time_setup.T5000")
        stage1.add_argument("--n-physics-engines",
                            choices=[1, 4, 8, 16, 24],
                            type=int,
                            help="""

                            The # of physics engines to use during simulation (yay ARGoS!). If n >
                            1, the engines will be tiled in a uniform grid within the arena (X and Y
                            spacing may not be the same depending on dimensions and how many engines
                            are chosen, however).

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            default=1)
        stage1.add_argument("--physics-iter-per-tick",
                            type=int,
                            help="""

                            The # of iterations all physics engines should perform per tick
                            between each time the controller loops are run.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            default=10)
        stage1.add_argument("--n-sims",
                            help="""

                            How many simulations should be averaged together to form a single
                            experiment.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            type=int,
                            default=1)
        stage1.add_argument("--n-threads",
                            help="""

                            How many ARGoS simulation threads to use for each simulation in each experiment.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            type=int,
                            default=1)
        stage1.add_argument("--with-robot-rab",
                            help="""

                            Include the Range and Bearing sensor/actuator in the generated input files for robot if
                            TRUE. Otherwise, those tags are removed in the template input file if they exist.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)
        stage1.add_argument("--with-robot-leds",
                            help="""

                            Include the robot LED actuator in the generated input files if TRUE. Otherwise, it is
                            removed if it exists.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)
        stage1.add_argument("--with-robot-battery",
                            help="""

                            Include the robot battery sensor in the generated input files if TRUE. Otherwise, it is
                            removed if it exists.

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            action="store_true",
                            default=False)

        stage1.add_argument("--with-rendering",
                            help="""

                            Specify that the ARGoS Qt/OpenGL visualization subtree should be left in the input .argos
                            file. By default it is stripped out.

                            If TRUE, then any files in the frames/ directory of each simulation will be rendered into a
                            unique video file with directory using ffmpeg (precise command configurable). This option
                            assumes that [ffmpeg, Xvfb] programs can be found.

                            Use=stage{1,2,3}; can be omitted otherwise.
                            """,

                            action='store_true')

        stage1.add_argument("--n-blocks",
                            help="""

                            Specify the # blocks that should be used in the simulation (evenly split between cube and
                            ramp). Can be used to override batch criteria, or to supplement experiments that do not set
                            it so that manual modification of input file is unneccesary.

                            Use=stage{1}; can be omitted otherwise.
                            """,
                            type=int,
                            default=None)
        stage1.add_argument("--static-cache-blocks",
                            help="""

                            Specify the # of blocks used when the static cache is respawned (depth1 controllers only).

                            Use=stage{1}; can be omitted otherwise.

                            """,
                            default=None)

        stage2 = parser.add_argument_group('stage2 (Running experiments)')
        stage2.add_argument("--exec-method",
                            help="""

                            Specify the execution method to use when running experiments.

                            local: Run the maximum # of simulations simultaneously on the local machine using GNU
                                   parallel. # of simultaneous simulations is determined by # cores on machine / # ARGoS
                                   threads.

                            hpc: Use GNU parallel in an HPC environment to run the specified # of
                                 simulations simultaneously on a computing cluster. The $MSICLUSTER
                                 environment variable will be used to identify the cluster sierra
                                 was invoked on and select the appropriate ARGoS executable. For
                                 example, if $MSICLUSTER=itasca, then ARGoS will be invoked via
                                 'argos3-itasca'. This option is provided so that in HPC
                                 environments with multiple clusters with different architectures
                                 ARGoS can be compiled natively for each for maximum performance.

                            Use=stage{2}; can be omitted otherwise.

                            """,
                            default="local")
        stage2.add_argument("--exec-exp-range",
                            help="""

                            Experiment numbers from the batch to run. Ignored if --batch-criteria is not
                            passed. Specified in the form a:b. If omitted, runs all experiments in the batch (default
                            behavior).

                            Use=stage{2}; can be omitted otherwise.

                            """)
        stage2.add_argument("--exec-resume",
                            help="""

                            Resume an experiment/batch experiment that was killed/stopped/etc last time sierra was run.

                            Use=stage{2}; can be omitted otherwise.

                            """,
                            action='store_true',
                            default=False)
        stage3 = parser.add_argument_group('stage3 (experiment averaging)')
        stage3.add_argument('--no-verify-results',
                            help="""

                            If TRUE, then the verification step will be skipped for the batched experiment, and outputs
                            will be averaged directly. If not all .csv files for all experiments exist and/or have the
                            same # of rows, then sierra will crash. Verification can take a long time with large # of
                            simulations per experiment.

                            Use=stage{3}; can be omitted otherwise.

                            """,
                            action='store_true',
                            default=False)
        stage3.add_argument("--gen-stddev",
                            help="""

                            If TRUE, then the standard deviation will be calculated from averaged data and error bars
                            will be included on all linegraphs (if they are generated).

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
        stage3.add_argument("--render-cmd-opts",
                            help="""

                            Specify the ffmpeg options to appear between the specification of the input .png files and
                            the specification of the output file. The default is suitable for use with ARGoS frame
                            grabbing set to a frames of 1600x1200 to output a reasonable quality video.

                            Use=stage{3}; can be omitted otherwise.

                            """,
                            default="-r 10 -s:v 800x600 -c:v libx264 -crf 25 -filter:v scale=-2:956 -pix_fmt yuv420p")
        stage3.add_argument("--render-cmd-ofile",
                            help="""

                            Specify the output filename and extension for the ffmpeg rendered video.

                            Use=stage{3}; can be omitted otherwise.

                            """,
                            default="video.mp4")

        stage4 = parser.add_argument_group('stage4 (graph generation)')

        stage4.add_argument("--with-hists",
                            help="""

                            Enable generation of intra-experiment histograms (if that part of the graph generation will
                            be run).

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            action="store_true")
        stage4.add_argument("--exp-graphs",
                            choices=['intra', 'inter', 'all'],
                            help="""

                            Specify which graphs should be generated: Only intra-experiment graphs, only
                            inter-experiment graphs, or both.

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            default='all')

        stage4.add_argument("--gen-vc-plots",
                            help="""

                            If TRUE, then the plots of ideal vs. observed swarm [reactivity,
                            adaptability] will be generated for each experiment.

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            action="store_true")

        stage4.add_argument("--plot-log-xaxis",
                            help="""

                            If TRUE, then the set of X values used to generate intra- and inter-batch plots will be
                            placed into the logarithmic (base 2) space. Mainly useful when the batch criteria involves
                            large swarm sizes, so that the plots are more readable.

                            Use=stage{4}; can be omitted otherwise.
                            """,
                            default=False)

        stage4.add_argument("--envc-cs-method",
                            help="""

                            Environmental conditions curve similarity method. Specify the method to use to calculate the
                            similarity between curves of applied variance (non-ideal conditions) and ideal conditions
                            (exp0). Only applies for temporal_variance batch criteria. Valid values are:

                            pcm:          Partial Curve Mapping (Witowski2012)
                            area_between: Area between the two curves (Jekel2018)
                            frechet:      Frechet distance (Frechet1906)
                            dtw:          Dynamic Time Warping (Berndt1994)
                            curve_length: Arc-length distance along the curve from the origin of (applied - ideal)
                                          curve (Andrade-campos2009).

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                            default="pcm")
        stage4.add_argument("--reactivity-cs-method",
                            help="""

                            Reactivity calculatation curve similarity method. Specify the method to use to calculate the
                            similarity between the inverted applied variance curve for a simulation and the corrsponding
                            performance curve.

                            pcm:          Partial Curve Mapping (Witowski2012)
                            area_between: Area between the two curves (Jekel2018)
                            frechet:      Frechet distance (Frechet1906)
                            dtw:          Dynamic Time Warping (Berndt1994)
                            curve_length: Arc-length distance along the curve from the origin of (applied - ideal)
                                          curve (Andrade-campos2009).

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                            default="pcm")
        stage4.add_argument("--adaptability-cs-method",
                            help="""

                            Adaptability calculatation curve similarity method. Specify the method to use to calculate
                            the similarity between the inverted applied variance curve for a simulation and the corrsponding
                            performance curve.

                            pcm:          Partial Curve Mapping (Witowski2012)
                            area_between: Area between the two curves (Jekel2018)
                            frechet:      Frechet distance (Frechet1906)
                            dtw:          Dynamic Time Warping (Berndt1994)
                            curve_length: Arc-length distance along the curve from the origin of (applied - ideal)
                                          curve (Andrade-campos2009).

                            Use=stage{4}; can be omitted otherwise.

                            """,
                            choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                            default="pcm")

        stage5 = parser.add_argument_group('stage5 (Inter-batch controller/scenario comparison)')

        stage5.add_argument("--inter-batch-controllers",
                            help="""

                            Comma separated list of controllers to compare within <sierra root>. If None, then the
                            default set of controllers will be used for comparison.

                            Use=stage{5}; can be omitted otherwise.

                            """,
                            default='depth0.CRW,depth0.DPO,depth1.BITD_DPO,depth2.BIRTD_DPO')
        return parser


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

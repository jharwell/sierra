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
Core command line parsing and validation classes.
"""

import argparse
import os
import multiprocessing


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    """
    Formatter to get (somewhat) better text wrapping of arguments with --help in the terminal.
    """


class BootstrapCmdline:
    """
    Defines the cmdline arguments that are used to bootstrap SIERRA. That is, the arguments that are
    needed to load the project plugin.
    """

    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='sierra',
                                              formatter_class=HelpFormatter)

        self.parser.add_argument("--plugin",
                                 choices=["fordyca", "silicon"],
                                 help="""

                                 Specify which plugin to load (really what project you want to use SIERRA with).

                                 Use=stage[1,2,3,4,5].
                                 """)
        self.parser.add_argument("--log-level",
                                 choices=["INFO", "DEBUG"],
                                 help="""

                                 The level of logging to use when running SIERRA.

                                 """,
                                 default="INFO")


class CoreCmdline:
    """
    Defines the core command line arguments for SIERRA using :class:`argparse`.

    Project plugins should inherit from this class and add to its arguments as necessary. The
    following arguments **MUST** be added (or SIERRA will probably crash):

    - ``--controllers``

    Attributes:
        parser: :class:`argparse.ArgumentParser`. Holds non stage-specific arguments.
        stage1: Cmdline arguments specific to stage1.
        stage2: Cmdline arguments specific to stage2.
        stage3: Cmdline arguments specific to stage3.
        stage4: Cmdline arguments specific to stage4.
        stage5: Cmdline arguments specific to stage5.
        """

    """
    Define the cmdline arguments.

    Arguments:
        scaffold_only: Boolean specifying whether actual definition should take place, or if the class should only
                       perform scaffolding. Used to correctly generate sphinx docs.
    """

    def __init__(self, scaffold_only: bool = False):
        self.parser = argparse.ArgumentParser(prog='sierra',
                                              formatter_class=HelpFormatter)
        self.stage1 = self.parser.add_argument_group(
            'Stage1: General options for generating experiments')
        self.stage2 = self.parser.add_argument_group(
            'Stage2: General options for running experiments')
        self.stage3 = self.parser.add_argument_group(
            'Stage3: General options for preprocessing experiment results')
        self.stage4 = self.parser.add_argument_group(
            'Stage4: General options for generating graphs')
        self.stage5 = self.parser.add_argument_group(
            'Stage5: General options for controller comparison')

        if scaffold_only:
            return

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
                                 top level batch criteria; see the docs for the ones that can:

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

                                 Stage3: Process experimental results after running the batched experiment; some parts
                                 of this can be done in parallel. Part of default pipeline.

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

        self.parser.add_argument("--hpc-env",
                                 help="""

                                 The value of this argument determines if the ``--n-threads``, --physics-n-engines``,
                                 and ``--n-sims`` options will be computed/inherited from the specified HPC
                                 environment. Otherwise, they must be specified on the cmdline.

                                 Value values:

                                 - ``MSI`` - The following PBS environment variables are used to infer the # threads, #
                                   physics engines, and # simulations to run, respectively: ``PBS_NUM_PPN``,
                                   ``PBS_NUM_PPN``, ``PBS_NUM_NODES``. ``MSICLUSTER`` is used to determine the names of
                                   ARGoS executables, so that in HPC environments with multiple clusters with different
                                   architectures ARGoS can be compiled natively for each for maximum
                                   performance.``PBS_NODEFILE`` and ``PBS_JOBID`` are used to configure simulation
                                   launches.

                                 """,
                                 choices=['MSI', None],
                                 default=None)

        self.init_stage1()
        self.init_stage2()
        self.init_stage3()
        self.init_stage4()
        self.init_stage5()

    def init_stage1(self):
        """
        Define cmdline arguments for stage 1.
        """
        self.stage1.add_argument("--time-setup",
                                 help="""

                                 The simulation time setup to use, which sets the simulation duration and metric reporting
                                 interval.

                                 Use=stage{1}; can be omitted otherwise.

                                 """,
                                 default="time_setup.T5000")

        self.stage1.add_argument("--n-sims",
                                 type=int,
                                 help="""

                                 How many simulations should be averaged together to form a single experiment.

                                 If ``--exec-method=hpc`` then the value of this option will be used to determine
                                 # jobs/HPC node, # physics engines/simulation, and # threads/simulation.


                                 Use=stage{1}; can be omitted otherwise.

                                 """)

        self.stage1.add_argument("--n-threads",
                                 type=int,
                                 help="""

                                 How many ARGoS simulation threads to use for each simulation in each experiment.

                                 If ``--exec-method=hpc`` then the value of this option will be set to the value of
                                 `--physics-n-engines`, per the findings of the original ARGoS paper, and the cmdline
                                 value (if any) is ignored.

                                 If ``exec-method=local`` then this option is required.

                                 Use=stage{1}; can be omitted otherwise.

                                 """)

        # Physics engines options
        physics = self.parser.add_argument_group('Stage1: Physics',
                                                 'Physics engine options for stage1')

        physics.add_argument("--physics-engine-type2D",
                             choices=['dynamics2d'],
                             help="""

                             Specify the type of 2D physics engines used for managing arena extents, choosing one of the
                             types that ARGoS supports.

                             """,
                             default='dynamics2d')

        physics.add_argument("--physics-engine-type3D",
                             choices=['dynamics3d', 'pointmass3d'],
                             help="""

                             Specify the type of 3D physics physics engine used for managing arena extents, choosing one
                             of the types that ARGoS supports.

                             """,
                             default='dynamics3d')
        physics.add_argument("--physics-n-engines",
                             choices=[1, 4, 8, 16, 24],
                             type=int,
                             help="""

                             # of physics engines to use during simulation (yay ARGoS!). If n > 1, the engines will be
                             tiled in a uniform grid within the arena (X and Y spacing may not be the same depending on
                             dimensions and how many engines are chosen, however), extending upward in Z to the height
                             specified by ``--scenario``.

                             If 2D and 3D physics engines are mixed, then half of the specified # of engines will be
                             allocated among all arena extents cumulatively managed by each type of engine. For example,
                             if 4 engines are used, with 1/3 of the arena managed by 2D engines and 2/3 by 3D, then 2
                             2D engines will manage 1/3 of the arena, and 2 3D engines will manage the other 2/3 of the
                             arena.

                             If ``--exec-method=hpc`` then the value of this option will be computed from the HPC
                             environment, and the cmdlin value (if any) will be ignored.

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

    def init_stage2(self):
        """
        Define cmdline arguments for stage 2.
        """
        self.stage2.add_argument("--exec-method",
                                 choices=['local', 'hpc'],
                                 help="""

                                 Specify the execution method to use when running experiments.

                                 - ``local`` - Run the maximum # of simulations simultaneously on the local machine
                                   using GNU parallel. # of simultaneous simulations is determined by # cores on machine
                                   / # ARGoS threads.

                                 - ``hpc`` - Use GNU parallel in an HPC environment to run the specified # of
                                   simulations simultaneously on a computing cluster. See ``--hpc-env`` for supported
                                   HPC environments.

                                 Use=stage{2}; can be omitted otherwise.

                                 """,
                                 default="local")
        self.stage2.add_argument("--exec-exp-range",
                                 help="""

                                 Experiment numbers from the batch to run. Specified in the form
                                 ``min_exp_num:max_exp_num``. If omitted, runs all experiments in the batch (default
                                 behavior).

                                 Use=stage{2}; can be omitted otherwise.

                                 """)
        self.stage2.add_argument("--exec-resume",
                                 help="""

                                 Resume a batched experiment that was killed/stopped/etc last time sierra was run.

                                 Use=stage{2}; can be omitted otherwise.

                                 """,
                                 action='store_true',
                                 default=False)

    def init_stage3(self):
        """
        Define cmdline arguments for stage 3.
        """
        self.stage3.add_argument('--no-verify-results',
                                 help="""

                                 If TRUE, then the verification step will be skipped for the batched experiment, and
                                 outputs will be averaged directly. If not all .csv files for all experiments exist
                                 and/or have the # of rows, then sierra will (probably) crash during
                                 stage4. Verification can take a same long time with large # of simulations per
                                 experiment.

                                 Use=stage{3}; can be omitted otherwise.

                                 """,
                                 action='store_true',
                                 default=False)
        self.stage3.add_argument("--gen-stddev",
                                 help="""

                                 Calculate standard deviation calculated from averaged data and include error bars on all
                                 generated intra-experiment linegraphs.

                                 Use=stage{3}; can be omitted otherwise.

                                 """,
                                 action="store_true",
                                 default=False)
        self.stage3.add_argument("--results-process-tasks",
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

    def init_stage4(self):
        """
        Define cmdline arguments for stage 4.
        """
        self.stage4.add_argument("--exp-graphs",
                                 choices=['intra', 'inter', 'all'],
                                 help="""

                                 Specify which graphs should be generated: Only intra-experiment graphs, only
                                 inter-experiment graphs, or both.

                                 Use=stage{4}; can be omitted otherwise.

                                 """,
                                 default='all')

        self.stage4.add_argument("--plot-log-xaxis",
                                 help="""

                                 Place the set of X values used to generate intra- and inter-experiment into the
                                 logarithmic (base 2) space. Mainly useful when the batch criteria involves large swarm
                                 sizes, so that the plots are more readable.

                                 Use=stage{4}; can be omitted otherwise.
                                 """,
                                 default=False)

        self.stage4.add_argument("--plot-regression-lines",
                                 help="""

                                 For all 2D generated scatterplots, plot a linear regression line and the equation of
                                 the line to the legend. Currently, this option affects the graphs generated when the
                                 following batch criteria are used:

                                 - ``saa_noise`` (bivariate)

                                 """)

        # Variance curve similarity options
        vcs = self.parser.add_argument_group('Stage4: VCS',
                                             'Variance Curve Similarity options for stage4')

        vcs.add_argument("--gen-vc-plots",
                         help="""

                          Generate plots of ideal vs. observed swarm [reactivity, adaptability] for each experiment in
                          the batch. Only applicable to ``flexibility`` batch criteria.

                          Use=stage{4}; can be omitted otherwise.

                          """,
                         action="store_true")

        vcs.add_argument("--rperf-cs-method",
                         help="""

                         Raw Performance curve similarity method. Specify the method to use to calculate the similarity
                         between raw performance curves from non-ideal conditions and ideal conditions (exp0). Only
                         applicable to ``saa_noise`` batch criteria. Value values:

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between`` - Area between the two curves (Jekel2018)
                         - ``frechet`` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                           curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="dtw")
        vcs.add_argument("--envc-cs-method",
                         help="""

                         Environmental conditions curve similarity method. Specify the method to use to calculate the
                         similarity between curves of applied variance (non-ideal conditions) and ideal conditions
                         (exp0). Only applicable to ``flexibility`` batch criteria, and only used to calculate axis tick
                         values on displayed graphs for that criteria. Valid values:

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between`` - Area between the two curves (Jekel2018)
                         - ``frechet`` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                           curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="dtw")

        vcs.add_argument("--reactivity-cs-method",
                         help="""

                         Reactivity calculatation curve similarity method. Specify the method to use to calculate the
                         similarity between the inverted applied variance curve for a simulation and the corrsponding
                         performance curve. Only applicable to ``flexibility`` batch criteria.

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between`` - Area between the two curves (Jekel2018)
                         - ``frechet`` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                           curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="dtw")
        vcs.add_argument("--adaptability-cs-method",
                         help="""

                         Adaptability calculatation curve similarity method. Specify the method to use to calculate the
                         similarity between the inverted applied variance curve for a simulation and the corrsponding
                         performance curve. Only applicable to ``flexibility`` batch criteria.

                         - ``pcm`` - Partial Curve Mapping (Witowski2012)
                         - ``area_between`` - Area between the two curves (Jekel2018)
                         - ``frechet`` -Frechet distance (Frechet1906)
                         - ``dtw`` - Dynamic Time Warping (Berndt1994)
                         - ``curve_length`` - Arc-length distance along the curve from the origin of (applied - ideal)
                           curve (Andrade-campos2009).

                         Use=stage{4}; can be omitted otherwise.

                         """,
                         choices=["pcm", "area_between", "frechet", "dtw", "curve_length"],
                         default="dtw")

    def init_stage5(self):
        """
        Define cmdline arguments for stage 5.
        """
        self.stage5.add_argument("--controllers-legend",
                                 help="""

                                 Comma separated list of names to use on the legend for the generated intra-scenario
                                 controller comparison graphs (if applicable), specified in the same order as the
                                 `--controllers-list`.

                                 Use=stage{5}; can be omitted otherwise. If omitted, the raw controller names will be used.
                                 """)
        self.stage5.add_argument("--comparison-type",
                                 choices=['raw1D', 'raw2D', 'raw3D', 'scale2D',
                                          'scale3D', 'diff2D', 'diff3D'],
                                 help="""

                                 Specify how controller comparisons should be performed.

                                 If the batch criteria is univariate, the options are:

                                 - ``raw1D`` - Output raw 1D performance measures using linegraphs.

                                 If the batch criteria is bivariate, the options are:

                                 - ``raw2D`` - Output raw 2D performance measures as a set of dual heatmaps comparing
                                   all controllers against the controller of primary interest (one per pair).

                                 - ``diff2D`` - Subtract the performance measure of the controller of primary interest
                                   against all other controllers, pairwise, outputting one 2D heatmap per comparison.

                                 - ``scale2D`` - Scale controller performance measures against those of the controller
                                   of primary interest by dividing, outputting one 2D heatmap per comparison.

                                 - ``raw3D`` - Output raw 3D performance measures as a single, stacked 3D surface
                                   plots comparing all controllers (identical plots, but view from different
                                   angles). Uses ``--controllers-legend`` if passed for legend.

                                 - ``scale3D`` - Scale controller performance measures against those of the controller
                                   of primary interest by dividing. This results in a single stacked 3D surface plots
                                   comparing all controllers (identical plots, but view from different angles). Uses
                                   ``--controllers-legend`` if passed for legend.

                                 - ``diff3D`` - Subtract the performance measure of the controller of primary interest
                                   from each controller (including the primary). This results in a set single stacked 3D
                                   surface plots comparing all controllers (identical plots, but view from different
                                   angles), in which the controller of primary interest forms an (X,Y) plane at
                                   Z=0. Uses ``--controllers-legend`` if passed for legend.

                                 """,
                                 default='raw1D')

        self.stage5.add_argument("--bc-univar",
                                 help="""

                                 Specify that the batch criteria is univariate. This cannot be deduced from the command
                                 line ``--batch-criteria`` argument in all cases because we are comparing controllers
                                 `across` scenarios, and each scenario (potentially) has a different batch criteria
                                 definition, which will result in (potentially) erroneous comparisons if we don't
                                 re-generate the batch criteria for each scenaro we compare controllers within.

                                 """,
                                 action='store_true')

        self.stage5.add_argument("--bc-bivar",
                                 help="""

                                 Specify that the batch criteria is bivariate. This cannot be deduced from the command
                                 line ``--batch-criteria`` argument in all cases because we are comparing controllers
                                 `across` scenarios, and each scenario (potentially) has a different batch criteria
                                 definition, which will result in (potentially) erroneous comparisons if we don't
                                 re-generate the batch criteria for each scenaro we compare controllers in.

                                 """,
                                 action='store_true')

        self.stage5.add_argument("--transpose-graphs",
                                 help="""

                                 Transpose the X,Y axes in generated graphs. Useful as a general way to tweak graphs for
                                 best use of space within a paper. Currently affects the following graphs:

                                 - :class:`~core.graphs.heatmap.Heatmap`

                                 Ignored for other graph types.
                                 Use=stage{5}; can be omitted otherwise.
                                 """,
                                 action='store_true')

        self.stage5.add_argument("--controllers-list",
                                 help="""

                                 Comma separated list of controllers to compare within ``<sierra root>``. If None, then the
                                 default set of controllers will be used for comparison.

                                 The first controller in this list will be used for as the controller of primary
                                 interest if ``--comparison-type`` is passed.

                                 Use=stage{5}; can be omitted otherwise.

                                 """)

        self.stage5.add_argument("--bc-undefined-exp0",
                                 help="""

                                 Specify that the batch criteria used is not defined for exp0. This is needed in stage
                                 5, but not for stage 4, because there is no general way to know if the batch criteria
                                 used is valid for exp0 or not (well you could put it in the batch criteria definition,
                                 but that has a code smell). Only affects graph generation for univariate batch
                                 criteria.
                                 """,
                                 action='store_true')


class HPCEnvInheritor():
    def __init__(self, env_type):
        self.env_type = env_type
        self.environs = ['mesabi', 'mangi']

    def __call__(self, args):
        # non-MSI
        if self.env_type is None:
            if any(s in args.pipeline for s in [1, 2]):
                args.__dict__['n_jobs_per_node'] = min(args.n_sims,
                                                       max(1,
                                                           int(multiprocessing.cpu_count() / float(args.n_threads))))
            else:
                args.__dict__['n_jobs_per_node'] = 0

            return args

        keys = ['MSICLUSTER', 'PBS_NUM_PPN', 'PBS_NUM_NODES']

        for k in keys:
            assert k in os.environ,\
                "FATAL: Attempt to run sierra in non-MSI environment: '{0}' not found".format(k)

        if self.env_type == 'MSI':
            assert os.environ['MSICLUSTER'] in self.environs,\
                "FATAL: Unknown MSI cluster '{0}'".format(os.environ['MSICLUSTER'])
            assert args.n_sims >= int(os.environ['PBS_NUM_NODES']),\
                "FATAL: Too few simulations requested: {0} < {1}".format(args.n_sims,
                                                                         os.environ['PBS_NUM_NODES'])
            assert args.n_sims % int(os.environ['PBS_NUM_NODES']) == 0,\
                "FATAL: # simulations ({0}) not a multiple of # nodes ({1})".format(args.n_sims,
                                                                                    os.environ['PBS_NUM_NODES'])

            # For HPC, we want to use the the maximum # of simultaneous jobs per node such that
            # there is no thread oversubscription. We also always want to allocate each physics
            # engine its own thread for maximum performance, per the original ARGoS paper.
            args.__dict__['n_jobs_per_node'] = int(
                float(args.n_sims) / int(os.environ['PBS_NUM_NODES']))
            args.physics_n_engines = int(float(os.environ['PBS_NUM_PPN']) / args.n_jobs_per_node)
            args.n_threads = args.physics_n_engines
        return args


class CoreCmdlineValidator():
    """
    Validate the core command line arguments to ensure that the pipeline will work properly in all stages, given the
    options that were passed.
    """

    def __call__(self, args):
        assert len(args.batch_criteria) <= 2, "FATAL: Too many batch criteria passed"

        if len(args.batch_criteria) == 2:
            assert args.batch_criteria[0] != args.batch_criteria[1],\
                "FATAL: Duplicate batch criteria passed"

        if args.gen_stddev:
            assert len(args.batch_criteria) == 1,\
                "FATAL: Stddev generation only supported with univariate batch criteria"

        assert isinstance(args.batch_criteria, list),\
            'FATAL Batch criteria not passed as list on cmdline'

        if any([1, 2]) in args.pipeline:
            assert args.n_sims is not None, '--n-sims is required'
            if args.exec_method == 'local':
                assert args.physics_n_engines is not None,\
                    '--physics-n-engines is required for --exec-method=local'
                assert args.n_threads is not None,\
                    '--n-threads is required for --exec-method=local'

        if 5 in args.pipeline:
            assert args.bc_univar or args.bc_bivar,\
                '--bc-univar or --bc-bivar is required for stage 5'


def sphinx_cmdline_core():
    """
    Return a handle to the core cmdline object for SIERRA in order for sphinx to autogenerate nice
    documentation from it.
    """
    return CoreCmdline().parser


def sphinx_cmdline_bootstrap():
    """
    Return a handle to the bootstrap cmdline object for SIERRA in order for sphinx to autogenerate
    nice documentation from it.
    """
    return BootstrapCmdline().parser

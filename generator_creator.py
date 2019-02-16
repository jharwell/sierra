"""
Copyright 2018 John Harwell, All rights reserved.

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

from pipeline.batched_exp_input_generator import BatchedExpInputGenerator
from generators.generator_factory import GeneratorPairFactory
from generators.generator_factory import ScenarioGeneratorFactory
from variables.temporal_variance_parser import TemporalVarianceParser


class GeneratorCreator:
    """
    Get the joint controller+scenario input generator to use to create experiment/batch inputs.
    """

    def __call__(self, args, generator_names):
        if any([[2], [3], [4]]) == args.pipeline:
            return None

        # Running stage 4 or 5
        if generator_names is None:
            return None

        # This is the dictionary of all cmdline options used during stage 1. This is here, rather
        # than in the exp pipeline, because the generator is passed INTO the pipeline.
        sim_opts = {
            "n_sims": args.n_sims,
            "n_threads": args.n_threads,
            "n_physics_engines": args.n_physics_engines,
            "physics_iter_per_tick": args.physics_iter_per_tick,
            "time_setup": args.time_setup,
            "with_robot_rab": args.with_robot_rab,
            "with_robot_leds": args.with_robot_leds,
            "with_robot_battery": args.with_robot_battery,
            "with_visualizations": args.with_visualizations,
            'n_blocks': args.n_blocks,
            'static_cache_blocks': args.static_cache_blocks,
        }
        if args.batch_criteria is not None:
            criteria = __import__("variables.{0}".format(
                args.batch_criteria.split(".")[0]), fromlist=["*"])
            sim_opts["arena_dim"] = None

            criteria_generator = getattr(criteria, "Factory")(args.batch_criteria)()
            print("- Parse batch criteria into generator governor '{0}'".format(
                criteria_generator.__class__.__name__))
            return BatchedExpInputGenerator(batch_config_template=args.template_config_file,
                                            batch_generation_root=args.generation_root,
                                            batch_output_root=args.output_root,
                                            exp_generator_pair=generator_names,
                                            batch_criteria=criteria_generator.gen_attr_changelist(),
                                            sim_opts=sim_opts)
        else:
            # The scenario dimensions were specified on the command line. Format of:
            # 'generators.<scenario>.<dimensions>'
            if len(generator_names[1].split('.')[1]) > 2:
                x, y = generator_names[1].split('.')[1][2:].split('x')
                sim_opts["arena_dim"] = (int(x), int(y))

            scenario_name = generator_names[1].split(
                '.')[0] + "." + generator_names[1].split('.')[1][:2] + "Generator"

            scenario = ScenarioGeneratorFactory(controller='generators.' + generator_names[0] + "Generator",
                                                scenario='generators.' + scenario_name,
                                                template_config_file=args.template_config_file,
                                                generation_root=args.generation_root,
                                                exp_output_root=args.output_root,
                                                exp_def_fname="exp_def.pkl",
                                                sim_opts=sim_opts)

            return GeneratorPairFactory(controller='generators.' + generator_names[0] + "Generator",
                                        scenario=scenario,
                                        template_config_file=args.template_config_file,
                                        generation_root=args.generation_root,
                                        exp_output_root=args.output_root,
                                        exp_def_fname="exp_def.pkl",
                                        sim_opts=sim_opts)

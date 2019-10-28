# Copyright 2018 John Harwell, All rights reserved.
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


from generators.batched_exp_input_generator import BatchedExpInputGenerator


class GeneratorCreator:
    """
    Get the joint controller+scenario input generator to use to create experiment/batch inputs.
    """

    def __call__(self, args, parsed_controller, parsed_scenario, batch_criteria, cmdopts):
        if any([[2], [3], [4]]) == args.pipeline:
            return None

        # Running stage 4 or 5
        if parsed_controller is None and parsed_scenario is None:
            return None

        # This is the dictionary of all cmdline options used during stage 1. This is here, rather
        # than in the exp pipeline, because the generator is passed INTO the pipeline.
        cmdopts_new = {
            "n_sims": args.n_sims,
            "n_threads": args.n_threads,
            "physics_n_engines": args.physics_n_engines,
            "physics_iter_per_tick": args.physics_iter_per_tick,
            "time_setup": args.time_setup,
            "with_robot_rab": args.with_robot_rab,
            "with_robot_leds": args.with_robot_leds,
            "with_robot_battery": args.with_robot_battery,
            "with_rendering": args.with_rendering,
            'n_blocks': args.n_blocks,
            'static_cache_blocks': args.static_cache_blocks,
            'exec_method': args.exec_method,
            'config_root': args.config_root,
            'named_exp_dirs': args.named_exp_dirs,
            'hpc_env': args.hpc_env
        }
        cmdopts.update(cmdopts_new)

        return BatchedExpInputGenerator(batch_config_template=args.template_input_file,
                                        controller_name=parsed_controller,
                                        scenario_basename=parsed_scenario,
                                        criteria=batch_criteria,
                                        cmdopts=cmdopts)

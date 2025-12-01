#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import typing as tp
import os
import subprocess

# 3rd party packages
import csv

# Project packages

versions = ["3.9", "3.10", "3.11", "3.12"]


def stage1_univar_check_outputs(
    engine: str,
    parallelism: str,
    input_root: pathlib.Path,
    cardinality: int,
    n_runs: int,
) -> None:
    # Check stage1 generated files
    for i in range(cardinality):
        # Check that commands.txt does NOT exist in experiment directories
        if parallelism == "per-batch":
            commands_file = f"{input_root}/c1-exp{i}/commands.txt"
            assert not os.path.isfile(
                commands_file
            ), f"File {commands_file} should not exist"

            commands_file = f"{input_root}/commands.txt"
            assert not os.path.isfile(commands_file), f"File {commands_file} not exist"
        elif parallelism == "per-exp":
            commands_file = f"{input_root}/c1-exp{i}/commands.txt"
            assert os.path.isfile(commands_file), f"File {commands_file} should exist"

            commands_file = f"{input_root}/commands.txt"
            assert not os.path.isfile(commands_file), f"File {commands_file} exists"

        exp_dir = input_root / f"c1-exp{i}"

        # Check that required files DO exist
        exp_def_file = f"{input_root}/c1-exp{i}/exp_def.pkl"
        seeds_file = f"{input_root}/c1-exp{i}/seeds.pkl"
        assert os.path.isfile(exp_def_file), f"File {exp_def_file} does not exist"
        assert os.path.isfile(seeds_file), f"File {seeds_file} does not exist"

        # Check run files
        for run in range(n_runs):
            if engine == "argos":
                run_file = f"{input_root}/c1-exp{i}/template_run{run}.argos"
                assert os.path.isfile(run_file), f"File {run_file} does not exist"
            elif engine == "jsonsim":
                run_file = f"{input_root}/c1-exp{i}/template_run{run}.json"
                assert os.path.isfile(run_file), f"File {run_file} does not exist"
                content = pathlib.Path(run_file).read_text()
                assert "-1" not in content, f"File {run_file} contains '-1'"
                assert "foobar" not in content, f"File {run_file} contains 'foobar'"
            elif engine == "ros1robot":
                required_files = [
                    f"commands_run{run}_master.txt",
                    f"commands_run{run}_slave.txt",
                    f"turtlebot3_run{run}_master.launch",
                    f"turtlebot3_run{run}_robot{i}.launch",
                ]

                for filename in required_files:
                    file_path = exp_dir / filename
                    assert file_path.is_file(), f"File {file_path} does not exist"
            elif engine == "ros1gazebo":
                master_launch = exp_dir / f"turtlebot3_house_run{run}_master.launch"
                robots_launch = exp_dir / f"turtlebot3_house_run{run}_robots.launch"

                assert master_launch.is_file(), f"File {master_launch} missing"
                assert robots_launch.is_file(), f"File {robots_launch} missing"


def stage2_univar_check_outputs(
    engine: str,
    batch_root: pathlib.Path,
    cardinality: int,
    n_runs: int,
) -> None:
    output_root = batch_root / "exp-outputs"

    # Check SIERRA directory structure. ros1+gazebo doesn't currently output
    # anything, so this check will fail.
    if engine != "ros1gazebo":
        for i in range(cardinality):
            for run in range(4):  # {0..3}
                output_dir = f"{output_root}/c1-exp{i}/template_run{run}_output"
                assert os.path.isdir(
                    output_dir
                ), f"Directory {output_dir} does not exist"

    # Check stage2 generated data
    for i in range(cardinality):
        for run in range(n_runs):
            if engine == "argos":
                data_file = f"{output_root}/c1-exp{i}/template_run{run}_output/output/collected-data.csv"
                assert os.path.isfile(data_file), f"File {data_file} does not exist"
            elif engine == "jsonsim":
                files = [
                    f"{output_root}/c1-exp{i}/template_run{run}_output/output/output1D.csv",
                    f"{output_root}/c1-exp{i}/template_run{run}_output/output/output2D.csv",
                    f"{output_root}/c1-exp{i}/template_run{run}_output/output/subdir1/subdir2/output1D.csv",
                    f"{output_root}/c1-exp{i}/template_run{run}_output/output/subdir1/subdir2/output2D.csv",
                    f"{output_root}/c1-exp{i}/template_run{run}_output/output/subdir3/output1D.csv",
                    f"{output_root}/c1-exp{i}/template_run{run}_output/output/subdir3/output2D.csv",
                ]
                for f in files:
                    assert os.path.isfile(f), f"File {f} does not exist"
            elif engine == "ros1gazebo":
                pass  # Nothing currently generated
            else:
                assert False, f"Unhandled engine case {engine}"


def stage3_univar_check_outputs(
    engine: str, batch_root: pathlib.Path, cardinality: int, stats: list[str]
):
    """Helper function to check stage 3 outputs."""
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality):
        exp_dir = stat_root / f"c1-exp{i}"
        assert exp_dir.is_dir(), f"Directory {exp_dir} does not exist"

    # Don't check for yamlsim, since that is the one which we use for testing
    # the pseudostats plugin.
    if engine != "yamlsim":
        interexp_dir = stat_root / "inter-exp"
        assert interexp_dir.is_dir(), f"Directory {interexp_dir} does not exist"

    if engine == "argos":
        _stage3_univar_check_outputs_argos(stat_root, cardinality, stats)
    elif engine == "jsonsim":
        _stage3_univar_check_outputs_jsonsim(stat_root, cardinality, stats)
    elif engine == "yamlsim":
        _stage3_univar_check_outputs_yamlsim(stat_root, cardinality, stats)


def _stage3_univar_check_outputs_yamlsim(
    stat_root: pathlib.Path,
    cardinality: int,
    stats: list[str],
    check_interexp: bool = True,
):
    # Check stage3 generated statistics
    for i in range(0, cardinality):
        for stat in stats:
            exp_dir = stat_root / f"c1-exp{i}"
            intraexp_items = [
                {"path": exp_dir / f"output1D.{stat}", "lines": 51, "cols": 5},
                {
                    "path": exp_dir / f"output1D.{stat}",
                    "lines": 51,
                    "cols": 5,
                },
                {
                    "path": exp_dir / f"confusion-matrix.{stat}",
                    "lines": -1,
                    "cols": 3,
                },
            ]

            for item in intraexp_items:
                assert item["path"].is_file(), f"File {item['path']} does not exist"

            # Check row and column counts
            with item["path"].open() as f:
                reader = csv.reader(f)
                lines = list(reader)
                if item["lines"] != -1:
                    assert (
                        len(lines) == item["lines"]
                    ), f"{item['path']} should have {item['lines']} rows, got {len(lines)}"
                assert (
                    len(lines[0]) == item["cols"]
                ), f"{item['path']} should have {item['cols']} columns, got {len(lines[0])}"

            # Check interexp files
            if not check_interexp:
                return

            interexp_items = [
                {
                    "path": stat_root / f"inter-exp/c1-exp{i}/output1D-col1.csv",
                    "lines": 51,
                    "cols": 4,
                },
            ]

            for item in interexp_items:
                assert item["path"].is_file(), f"File {item['path']} does not exist"

                with item["path"].open() as f:
                    reader = csv.reader(f)
                    lines = list(reader)
                    assert (
                        len(lines) == item["lines"]
                    ), f"{item['path']} should have {item['lines']} rows, got {len(lines)}"
                    assert (
                        len(lines[0]) == item["cols"]
                    ), f"{item['path']} should have {item['cols']} columns, got {len(lines[0])}"


def _stage3_univar_check_outputs_jsonsim(
    stat_root: pathlib.Path, cardinality: int, stats: list[str]
):
    # Check stage3 generated statistics
    for i in range(0, cardinality):
        for stat in stats:
            exp_dir = stat_root / f"c1-exp{i}"
            items = [
                {"path": exp_dir / f"output1D.{stat}", "lines": 51, "cols": 5},
                {"path": exp_dir / f"output2D.{stat}", "lines": 49, "cols": 3},
                {
                    "path": exp_dir / f"subdir1/subdir2/output1D.{stat}",
                    "lines": 51,
                    "cols": 5,
                },
                {
                    "path": exp_dir / f"subdir1/subdir2/output2D.{stat}",
                    "lines": 49,
                    "cols": 3,
                },
                {"path": exp_dir / f"subdir3/output1D.{stat}", "lines": 51, "cols": 5},
                {"path": exp_dir / f"subdir3/output2D.{stat}", "lines": 49, "cols": 3},
            ]

            for item in items:
                assert item["path"].is_file(), f"File {item['path']} does not exist"

            # Check row and column counts
            with item["path"].open() as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == item["lines"]
                ), f"{item['path']} should have {item['lines']} rows, got {len(lines)}"
                assert (
                    len(lines[0]) == item["cols"]
                ), f"{item['path']} should have item['cols'] columns, got {len(lines[0])}"

            # Check interexp files
            interexp_items = [
                {
                    "path": stat_root
                    / f"inter-exp/c1-exp{i}/subdir1/subdir2/output1D-col1.csv",
                    "lines": 51,
                    "cols": 4,
                },
                {
                    "path": stat_root
                    / f"inter-exp/c1-exp{i}/subdir3/output1D-col2.csv",
                    "lines": 51,
                    "cols": 4,
                },
            ]

            for item in interexp_items:
                assert item["path"].is_file(), f"File {item['path']} does not exist"
                # Check interexp file dimensions
                with item["path"].open() as f:
                    reader = csv.reader(f)
                    lines = list(reader)
                    assert (
                        len(lines) == item["lines"]
                    ), f"{item['path']} should have {item['lines']} rows, got {len(lines)}"
                assert (
                    len(lines[0]) == item["cols"]
                ), f"{item['path']} should have {item['cols']} columns, got {len(lines[0])}"


def _stage3_univar_check_outputs_argos(
    stat_root: pathlib.Path, cardinality: int, stats: list[str]
):
    """Helper function to check stage 3 outputs for ARGoS."""
    interexp_dir = stat_root / "inter-exp"
    assert interexp_dir.is_dir(), f"Directory {interexp_dir} does not exist"

    # Check stage3 generated statistics
    for stat in stats:
        # Check interexp stats
        interexp_file = interexp_dir / "c1-exp0/collected-data-collected_food.csv"
        assert interexp_file.is_file(), f"File {interexp_file} does not exist"

        # Check individual experiment stats
        for i in range(cardinality):
            stat_file = stat_root / f"c1-exp{i}/collected-data.{stat}"
            assert stat_file.is_file(), f"File {stat_file} does not exist"


def stage4_univar_check_outputs(
    engine: str, batch_root: pathlib.Path, cardinality: int, stats: list[str]
):
    """Helper function to check stage 4 outputs."""
    graph_root = batch_root / "graphs"
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality):
        exp_dir = graph_root / f"c1-exp{i}"
        assert exp_dir.is_dir(), f"Directory {exp_dir} does not exist"

    interexp_dir = graph_root / "inter-exp"
    assert interexp_dir.is_dir(), f"Directory {interexp_dir} does not exist"

    if engine == "argos":
        _stage4_univar_check_outputs_argos(graph_root, stat_root, cardinality, stats)
    elif engine == "jsonsim":
        _stage4_univar_check_outputs_jsonsim(graph_root, stat_root, cardinality, stats)
    elif engine == "yamlsim":
        _stage4_univar_check_outputs_yamlsim(graph_root, stat_root, cardinality, stats)
    else:
        raise RuntimeError(f"Engine {engine} checks not implemented")


def _stage4_univar_check_outputs_argos(
    graph_root: pathlib.Path,
    stat_root: pathlib.Path,
    cardinality: int,
    stats: list[str],
):
    """Helper function to check stage 4 outputs for ARGoS."""
    # Check stage4 generated .csvs
    for stat in stats:
        interexp_csvs = [
            f"food-counts.{stat}",
            f"robot-counts-resting.{stat}",
            f"robot-counts-walking.{stat}",
            f"swarm-energy.{stat}",
        ]
        for f in interexp_csvs:
            path = stat_root / "inter-exp" / f
            assert path.is_file(), f"File {f} does not exist"

    # Check intra-exp graphs
    for i in range(cardinality):
        intraexp_graphs = [
            graph_root / f"c1-exp{i}/SLN-food-counts.png",
            graph_root / f"c1-exp{i}/SLN-robot-counts.png",
            graph_root / f"c1-exp{i}/SLN-swarm-energy.png",
        ]

        for f in intraexp_graphs:
            assert f.is_file(), f"File {f} does not exist"

    interexp_graphs = [
        graph_root / "inter-exp/SLN-food-counts.png",
        graph_root / "inter-exp/SLN-robot-counts-walking.png",
        graph_root / "inter-exp/SLN-robot-counts-resting.png",
        graph_root / "inter-exp/SLN-swarm-energy.png",
    ]
    for f in interexp_graphs:
        assert f.is_file(), f"File {f} does not exist"


def _stage4_univar_check_outputs_jsonsim(
    graph_root: pathlib.Path,
    stat_root: pathlib.Path,
    cardinality: int,
    stats: list[str],
):
    """Helper function to check stage 4 outputs for JSONSIM."""
    # Check stage4 generated .csvs
    for stat in stats:
        interexp_csvs = [
            f"random-noise2-col2.{stat}",
            f"random-noise3-col2.{stat}",
            f"random-noise-col1.{stat}",
        ]
        for f in interexp_csvs:
            path = stat_root / "inter-exp" / f
            assert path.is_file(), f"File {f} does not exist"

    # Check intra-exp graphs
    for i in range(cardinality):
        intraexp_graphs = [
            graph_root / f"c1-exp{i}/HM-output2D-1.png",
            graph_root / f"c1-exp{i}/HM-output2D-2.png",
            graph_root / f"c1-exp{i}/SLN-random-noise.png",
            graph_root / f"c1-exp{i}/SLN-random-noise2.png",
            graph_root / f"c1-exp{i}/SLN-random-noise3.png",
        ]

        for f in intraexp_graphs:
            assert f.is_file(), f"File {f} does not exist"

    interexp_graphs = [
        graph_root / "inter-exp/SLN-random-noise2-col2.png",
        graph_root / "inter-exp/SLN-random-noise-col1.png",
        graph_root / "inter-exp/SM-random-noise3-col2.png",
    ]
    for f in interexp_graphs:
        assert f.is_file(), f"File {f} does not exist"


def _stage4_univar_check_outputs_yamlsim(
    graph_root: pathlib.Path,
    stat_root: pathlib.Path,
    cardinality: int,
    stats: list[str],
):
    """Helper function to check stage 4 outputs for YAMLSIM."""
    # Check stage4 generated .csvs
    for stat in stats:
        interexp_csvs = [
            f"random-noise-col1.{stat}",
        ]
        for f in interexp_csvs:
            path = stat_root / "inter-exp" / f
            assert path.is_file(), f"File {f} does not exist"

    # Check intra-exp graphs
    for i in range(cardinality):
        intraexp_graphs = [
            graph_root / f"c1-exp{i}/CM-confusion-matrix.png",
            graph_root / f"c1-exp{i}/SLN-random-noise.png",
        ]

        for f in intraexp_graphs:
            assert f.is_file(), f"File {f} does not exist"

    interexp_graphs = [
        graph_root / "inter-exp/SLN-random-noise-col1.png",
    ]
    for f in interexp_graphs:
        assert f.is_file(), f"File {f} does not exist"


def stage1_bivar_check_outputs(
    engine: str,
    input_root: pathlib.Path,
    cardinality0: int,
    cardinality1: int,
    n_runs: int,
) -> None:
    # Check directory structure
    for i in range(cardinality0):
        for j in range(cardinality1):
            dir_path = f"{input_root}/c1-exp{i}+c2-exp{j}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} not found"

    # Check generated files
    for i in range(cardinality0):
        for j in range(cardinality1):
            # Check max_speed occurrences
            if engine == "argos":
                cmd = f'grep -r "max_speed=" {input_root}/c1-exp{i}+c2-exp{j}/*.argos | wc -l'

                result = subprocess.check_output(cmd, shell=True).decode().strip()
                assert (
                    int(result) == n_runs
                ), f'Expected {n_runs} occurrences of max_speed="1.0", found {result}'

                # Check for required files
                assert os.path.isfile(
                    f"{input_root}/c1-exp{i}+c2-exp{j}/commands.txt"
                ), "commands.txt not found"
                assert os.path.isfile(
                    f"{input_root}/c1-exp{i}+c2-exp{j}/exp_def.pkl"
                ), "exp_def.pkl not found"
                assert os.path.isfile(
                    f"{input_root}/c1-exp{i}+c2-exp{j}/seeds.pkl"
                ), "seeds.pkl not found"

                # Check for run files
                for run in range(n_runs):
                    assert os.path.isfile(
                        f"{input_root}/c1-exp{i}+c2-exp{j}/template_run{run}.argos"
                    ), f"template_run{run}.argos not found"

            else:
                assert False, f"Unhandled engine case {engine}"


def stage3_bivar_check_outputs(
    engine: str,
    batch_root: pathlib.Path,
    cardinality0: int,
    cardinality1: int,
    to_check: list[str],
):
    """Check stage 3 bivariate outputs."""
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality0):
        for j in range(cardinality1):
            dir_path = f"{stat_root}/c1-exp{i}+c2-exp{j}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

    # Check interexp directory
    interexp_dir = f"{stat_root}/inter-exp"
    assert os.path.isdir(interexp_dir), f"Directory {interexp_dir} does not exist"

    # Check stage3 generated statistics
    for stat in to_check:
        for i in range(cardinality0):
            for j in range(cardinality1):
                if engine == "argos":
                    stat_file = f"{stat_root}/c1-exp{i}+c2-exp{j}/collected-data.{stat}"

                    csv_file = f"{stat_root}/inter-exp/c1-exp{i}+c2-exp{j}/collected-data-collected_food.csv"
                    assert os.path.isfile(stat_file), f"File {stat_file} does not exist"
                    assert os.path.isfile(csv_file), f"File {csv_file} does not exist"

                else:
                    assert False, f"Unhandled engine case {engine}"


def stage4_bivar_check_outputs(
    engine: str,
    batch_root: str,
    cardinality0: int,
    cardinality1: int,
    to_check: list[str],
):
    """Check stage 4 bivariate outputs."""
    graph_root = batch_root / "graphs"
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality0):
        for j in range(cardinality1):
            dir_path = f"{graph_root}/c1-exp{i}+c2-exp{j}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

    # Check interexp directory
    interexp_dir = f"{graph_root}/inter-exp"
    assert os.path.isdir(interexp_dir), f"Directory {interexp_dir} does not exist"

    # Check stage4 generated .csvs
    for stat in to_check:
        if engine == "argos":
            food_counts = f"{stat_root}/inter-exp/food-counts.{stat}"
            robot_counts_resting = f"{stat_root}/inter-exp/robot-counts-resting.{stat}"
            robot_counts_walking = f"{stat_root}/inter-exp/robot-counts-walking.{stat}"
            swarm_energy = f"{stat_root}/inter-exp/swarm-energy.{stat}"

            assert os.path.isfile(food_counts), f"File {food_counts} does not exist"
            assert os.path.isfile(
                robot_counts_resting
            ), f"File {robot_counts_resting} does not exist"
            assert os.path.isfile(
                robot_counts_walking
            ), f"File {robot_counts_walking} does not exist"
            assert os.path.isfile(swarm_energy), f"File {swarm_energy} does not exist"

        else:
            assert False, f"Unhandled engine case {engine}"
    # Check stage4 generated graphs
    for i in range(cardinality0):
        for j in range(cardinality1):
            if engine == "argos":
                food_counts = f"{graph_root}/c1-exp{i}+c2-exp{j}/SLN-food-counts.png"
                robot_counts = f"{graph_root}/c1-exp{i}+c2-exp{j}/SLN-robot-counts.png"
                swarm_energy = f"{graph_root}/c1-exp{i}+c2-exp{j}/SLN-swarm-energy.png"

                assert os.path.isfile(food_counts), f"File {food_counts} does not exist"
                assert os.path.isfile(
                    robot_counts
                ), f"File {robot_counts} does not exist"
                assert os.path.isfile(
                    swarm_energy
                ), f"File {swarm_energy} does not exist"
            else:
                assert False, f"Unhandled engine case {engine}"

    # Check interexp graphs
    if engine == "argos":
        hm_food = f"{graph_root}/inter-exp/HM-food-counts2.png"
        hm_robot_walking = f"{graph_root}/inter-exp/HM-robot-counts-walking2.png"
        hm_robot_resting = f"{graph_root}/inter-exp/HM-robot-counts-resting2.png"
        hm_swarm_energy = f"{graph_root}/inter-exp/HM-swarm-energy2.png"

        assert os.path.isfile(hm_food), f"File {hm_food} does not exist"
        assert os.path.isfile(
            hm_robot_walking
        ), f"File {hm_robot_walking} does not exist"
        assert os.path.isfile(
            hm_robot_resting
        ), f"File {hm_robot_resting} does not exist"
        assert os.path.isfile(hm_swarm_energy), f"File {hm_swarm_energy} does not exist"

    else:
        assert False, f"Unhandled engine case {engine}"


def stage5_univar_check_cc_outputs(session, engine: str):
    """Check controller comparison outputs."""
    if engine == "argos":
        cc_csv_root = pathlib.Path(
            f"{session.env['SIERRA_ROOT']}/projects.sample_argos/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-csvs"
        )
        cc_graph_root = pathlib.Path(
            f"{session.env['SIERRA_ROOT']}/projects.sample_argos/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-graphs"
        )

        # Check file counts
        csvs = [d for d in cc_csv_root.iterdir()]
        graphs = [d for d in cc_graph_root.iterdir()]

        assert len(csvs) == 18, f"Expected 18 CSV files, found {len(csvs)}"
        assert len(graphs) == 2, f"Expected 2 graph files, found {len(graphs)}"

        for path in csvs:
            n_cols = len(next(csv.reader(open(path))))
            # +1 for the index column
            assert n_cols == 3, f"Expected 2 controllers in {path}, got {n_lines}"

    else:
        assert False, f"Unhandled engine case {engine}"


def stage5_univar_check_sc_outputs(session, engine: str):
    """Check scenario comparison outputs."""
    if engine == "argos":
        sc_csv_root = pathlib.Path(
            f"{session.env['SIERRA_ROOT']}/projects.sample_argos/LowBlockCount.10x10x2+HighBlockCount.10x10x2-sc-csvs"
        )
        sc_graph_root = pathlib.Path(
            f"{session.env['SIERRA_ROOT']}/projects.sample_argos/LowBlockCount.10x10x2+HighBlockCount.10x10x2-sc-graphs"
        )

        # Check file counts
        csvs = [d for d in sc_csv_root.iterdir()]
        graphs = [d for d in sc_graph_root.iterdir()]

        assert len(csvs) == 18, f"Expected 18 CSV files, found {len(csvs)}"
        assert len(graphs) == 2, f"Expected 2 graph files, found {len(graphs)}"

        for path in csvs:
            n_cols = len(next(csv.reader(open(path))))
            # +1 for the index column
            assert n_cols == 3, f"Expected 2 controllers in {path}, got {n_lines}"

    else:
        assert False, f"Unhandled engine case {engine}"


def stage5_bivar_check_cc_outputs(cc_graph_root: pathlib.Path, n_files: int):
    """Check controller comparison outputs for bivariate analysis."""
    # Count files in the directory
    file_count = len(list(cc_graph_root.iterdir()))

    # Assert the correct number of files
    assert (
        file_count == n_files
    ), f"Expected {n_files} files in {cc_graph_root}, found {file_count}"

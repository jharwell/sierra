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
    # Check SIERRA directory structure
    for i in range(cardinality):
        for run in range(4):  # {0..3}
            output_dir = f"{output_root}/c1-exp{i}/template_run{run}_output"
            assert os.path.isdir(output_dir), f"Directory {output_dir} does not exist"

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
            else:
                assert False, f"Unhandled engine case {engine}"


def stage3_univar_check_outputs(
    engine: str, batch_root: pathlib.Path, cardinality: int, stats: tp.List[str]
):
    """Helper function to check stage 3 outputs."""
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality):
        exp_dir = stat_root / f"c1-exp{i}"
        assert exp_dir.is_dir(), f"Directory {exp_dir} does not exist"

    collated_dir = stat_root / "collated"
    assert collated_dir.is_dir(), f"Directory {collated_dir} does not exist"

    # Check stage3 generated statistics
    for stat in stats:
        # Check collated stats
        if engine == "argos":
            collated_file = collated_dir / f"c1-exp0/collected-data-collected_food.csv"
            assert collated_file.is_file(), f"File {collated_file} does not exist"

            # Check individual experiment stats
            for i in range(cardinality):
                stat_file = stat_root / f"c1-exp{i}/collected-data.{stat}"
                assert stat_file.is_file(), f"File {stat_file} does not exist"

        elif engine == "jsonsim":
            exp_dir = stat_root / f"c1-exp{i}"
            file_paths = [
                exp_dir / "output1D.mean",
                exp_dir / "output2D.mean",
                exp_dir / "subdir1/subdir2/output1D.mean",
                exp_dir / "subdir1/subdir2/output2D.mean",
                exp_dir / "subdir3/output1D.mean",
                exp_dir / "subdir3/output2D.mean",
            ]

            for file_path in file_paths:
                assert file_path.is_file(), f"File {file_path} does not exist"

            # Check row and column counts
            # output1D.mean
            with open(exp_dir / "output1D.mean") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 51
                ), f"output1D.mean should have 51 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 5
                ), f"output1D.mean should have 5 columns, got {len(lines[0])}"

            # output2D.mean
            with open(exp_dir / "output2D.mean") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 49
                ), f"output2D.mean should have 49 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 3
                ), f"output2D.mean should have 3 columns, got {len(lines[0])}"

            # subdir1/subdir2/output1D.mean
            with open(exp_dir / "subdir1/subdir2/output1D.mean") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 51
                ), f"subdir1/subdir2/output1D.mean should have 51 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 5
                ), f"subdir1/subdir2/output1D.mean should have 5 columns, got {len(lines[0])}"

            # subdir1/subdir2/output2D.mean
            with open(exp_dir / "subdir1/subdir2/output2D.mean") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 49
                ), f"subdir1/subdir2/output2D.mean should have 49 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 3
                ), f"subdir1/subdir2/output2D.mean should have 3 columns, got {len(lines[0])}"

            # subdir3/output1D.mean
            with open(exp_dir / "subdir3/output1D.mean") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 51
                ), f"subdir3/output1D.mean should have 51 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 5
                ), f"subdir3/output1D.mean should have 5 columns, got {len(lines[0])}"

            # subdir3/output2D.mean
            with open(exp_dir / "subdir3/output2D.mean") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 49
                ), f"subdir3/output2D.mean should have 49 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 3
                ), f"subdir3/output2D.mean should have 3 columns, got {len(lines[0])}"

            # Check collated files
            collated_files = [
                stat_root / f"collated/c1-exp{i}/subdir1/subdir2/output1D-col1.csv",
                stat_root / f"collated/c1-exp{i}/subdir3/output1D-col2.csv",
            ]

            for file_path in collated_files:
                assert file_path.is_file(), f"File {file_path} does not exist"

            # Check collated file dimensions
            with open(
                stat_root / f"collated/c1-exp{i}/subdir1/subdir2/output1D-col1.csv"
            ) as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 51
                ), f"collated/output1D-col1.csv should have 51 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 4
                ), f"collated/output1D-col1.csv should have 4 columns, got {len(lines[0])}"

            with open(stat_root / f"collated/c1-exp{i}/subdir3/output1D-col2.csv") as f:
                reader = csv.reader(f)
                lines = list(reader)
                assert (
                    len(lines) == 51
                ), f"collated/output1D-col2.csv should have 51 rows, got {len(lines)}"
                assert (
                    len(lines[0]) == 4
                ), f"collated/output1D-col2.csv should have 4 columns, got {len(lines[0])}"


def stage4_univar_check_outputs(
    engine: str, batch_root: pathlib.Path, cardinality: int, stats: tp.List[str]
):
    """Helper function to check stage 4 outputs."""
    graph_root = batch_root / "graphs"
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality):
        exp_dir = graph_root / f"c1-exp{i}"
        assert exp_dir.is_dir(), f"Directory {exp_dir} does not exist"

    collated_dir = graph_root / "collated"
    assert collated_dir.is_dir(), f"Directory {collated_dir} does not exist"

    # Check stage4 generated .csvs
    for stat in stats:
        if engine == "argos":
            assert (
                stat_root / f"collated/food-counts.{stat}"
            ).is_file(), f"File food-counts.{stat} does not exist"
            assert (
                stat_root / f"collated/robot-counts-resting.{stat}"
            ).is_file(), f"File robot-counts-resting.{stat} does not exist"
            assert (
                stat_root / f"collated/robot-counts-walking.{stat}"
            ).is_file(), f"File robot-counts-walking.{stat} does not exist"
            assert (
                stat_root / f"collated/swarm-energy.{stat}"
            ).is_file(), f"File swarm-energy.{stat} does not exist"

    # Check stage4 generated graphs
    for i in range(cardinality):
        if engine == "argos":
            assert (
                graph_root / f"c1-exp{i}/SLN-food-counts.png"
            ).is_file(), f"File c1-exp{i}/SLN-food-counts.png does not exist"
            assert (
                graph_root / f"c1-exp{i}/SLN-robot-counts.png"
            ).is_file(), f"File c1-exp{i}/SLN-robot-counts.png does not exist"
            assert (
                graph_root / f"c1-exp{i}/SLN-swarm-energy.png"
            ).is_file(), f"File c1-exp{i}/SLN-swarm-energy.png does not exist"

        if engine == "jsonsim":
            for i in range(cardinality):
                exp_files = [
                    "SLN-random-noise.png",
                    "SLN-random-noise2.png",
                    "SLN-random-noise3.png",
                    "HM-output2D-1.png",
                    "HM-output2D-2.png",
                    "SLN-random-noise.html",
                    "SLN-random-noise2.html",
                    "SLN-random-noise3.html",
                    "HM-output2D-1.html",
                    "HM-output2D-2.html",
                ]

                for file_name in exp_files:
                    file_path = graph_root / f"c1-exp{i}" / file_name
                    assert file_path.is_file(), f"File {file_path} does not exist"

    # Check collated graphs
    if engine == "argos":
        assert (
            graph_root / "collated/SLN-food-counts.png"
        ).is_file(), "File collated/SLN-food-counts.png does not exist"
        assert (
            graph_root / "collated/SLN-robot-counts-walking.png"
        ).is_file(), "File collated/SLN-robot-counts-walking.png does not exist"
        assert (
            graph_root / "collated/SLN-robot-counts-resting.png"
        ).is_file(), "File collated/SLN-robot-counts-resting.png does not exist"
        assert (
            graph_root / "collated/SLN-swarm-energy.png"
        ).is_file(), "File collated/SLN-swarm-energy.png does not exist"

    elif engine == "jsonsim":
        # Check collated files
        collated_files = [
            "SLN-random-noise-col1.png",
            "SLN-random-noise2-col2.png",
            "SM-random-noise3-col2.png",
            "SLN-random-noise-col1.html",
            "SLN-random-noise2-col2.html",
            "SM-random-noise3-col2.html",
        ]

        for file_name in collated_files:
            file_path = graph_root / "collated" / file_name
            assert file_path.is_file(), f"File {file_path} does not exist"


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
                ), f"commands.txt not found"
                assert os.path.isfile(
                    f"{input_root}/c1-exp{i}+c2-exp{j}/exp_def.pkl"
                ), f"exp_def.pkl not found"
                assert os.path.isfile(
                    f"{input_root}/c1-exp{i}+c2-exp{j}/seeds.pkl"
                ), f"seeds.pkl not found"

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
    to_check: tp.List[str],
):
    """Check stage 3 bivariate outputs."""
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality0):
        for j in range(cardinality1):
            dir_path = f"{stat_root}/c1-exp{i}+c2-exp{j}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

    # Check collated directory
    collated_dir = f"{stat_root}/collated"
    assert os.path.isdir(collated_dir), f"Directory {collated_dir} does not exist"

    # Check stage3 generated statistics
    for stat in to_check:
        for i in range(cardinality0):
            for j in range(cardinality1):
                if engine == "argos":
                    stat_file = f"{stat_root}/c1-exp{i}+c2-exp{j}/collected-data.{stat}"

                    csv_file = f"{stat_root}/collated/c1-exp{i}+c2-exp{j}/collected-data-collected_food.csv"
                    assert os.path.isfile(stat_file), f"File {stat_file} does not exist"
                    assert os.path.isfile(csv_file), f"File {csv_file} does not exist"

                else:
                    assert False, f"Unhandled engine case {engine}"


def stage4_bivar_check_outputs(
    engine: str,
    batch_root: str,
    cardinality0: int,
    cardinality1: int,
    to_check: tp.List[str],
):
    """Check stage 4 bivariate outputs."""
    graph_root = batch_root / "graphs"
    stat_root = batch_root / "statistics"

    # Check SIERRA directory structure
    for i in range(cardinality0):
        for j in range(cardinality1):
            dir_path = f"{graph_root}/c1-exp{i}+c2-exp{j}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

    # Check collated directory
    collated_dir = f"{graph_root}/collated"
    assert os.path.isdir(collated_dir), f"Directory {collated_dir} does not exist"

    # Check stage4 generated .csvs
    for stat in to_check:
        if engine == "argos":
            food_counts = f"{stat_root}/collated/food-counts.{stat}"
            robot_counts_resting = f"{stat_root}/collated/robot-counts-resting.{stat}"
            robot_counts_walking = f"{stat_root}/collated/robot-counts-walking.{stat}"
            swarm_energy = f"{stat_root}/collated/swarm-energy.{stat}"

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

    # Check collated graphs
    if engine == "argos":
        hm_food = f"{graph_root}/collated/HM-food-counts2.png"
        hm_robot_walking = f"{graph_root}/collated/HM-robot-counts-walking2.png"
        hm_robot_resting = f"{graph_root}/collated/HM-robot-counts-resting2.png"
        hm_swarm_energy = f"{graph_root}/collated/HM-swarm-energy2.png"

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
        cc_csv_root = f"{session.env['SIERRA_ROOT']}/projects.sample_argos/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-csvs"
        cc_graph_root = f"{session.env['SIERRA_ROOT']}/projects.sample_argos/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-graphs"

        # Check file counts
        csv_count = len(os.listdir(cc_csv_root))
        graph_count = len(os.listdir(cc_graph_root))

        assert csv_count == 18, f"Expected 18 CSV files, found {csv_count}"
        assert graph_count == 2, f"Expected 2 graph files, found {graph_count}"

    else:
        assert False, f"Unhandled engine case {engine}"


def stage5_univar_check_sc_outputs(session, engine: str):
    """Check scenario comparison outputs."""
    if engine == "argos":
        sc_csv_root = f"{session.env['SIERRA_ROOT']}/projects.sample_argos/LowBlockCount.10x10x2+HighBlockCount.10x10x2-sc-csvs"
        sc_graph_root = f"{session.env['SIERRA_ROOT']}/projects.sample_argos/LowBlockCount.10x10x2+HighBlockCount.10x10x2-sc-graphs"

        # Check file counts
        csv_count = len(os.listdir(sc_csv_root))
        graph_count = len(os.listdir(sc_graph_root))

        assert csv_count == 18, f"Expected 18 CSV files, found {csv_count}"
        assert graph_count == 2, f"Expected 2 graph files, found {graph_count}"

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

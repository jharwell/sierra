#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import os
import shutil
import psutil
import pathlib
import subprocess
import time

# 3rd party packages
import requests
import nox

# Project packages
from sierra.core import batchroot
from tests.smoke_tests import utils, setup


@nox.session(python=utils.versions, tags=["hpc"])
@nox.parametrize("env", ["hpc.local", "hpc.adhoc", "hpc.slurm", "hpc.pbs"])
@nox.parametrize(
    "engine",
    ["engine.argos", "engine.ros1gazebo", "plugins.jsonsim", "plugins.yamlsim"],
)
@setup.session_setup
@setup.session_teardown
def execenv_hpc(session, env, engine):
    """Check that all HPC plugins work across multiple engines.

    Currently just JSONSIM and ARGoS, but more should be added as more engines
    make it into the core.
    """
    if engine == "engine.argos":
        bc = ["population_size.Linear3.C3"]
        template_stem = "template"
        scenario = "LowBlockCount.10x10x2"
        leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
        batch_root = batchroot.ExpRoot(
            sierra_root=f"{session.env['SIERRA_ROOT']}",
            project="projects.sample_argos",
            controller="foraging.footbot_foraging",
            leaf=leaf,
            scenario=scenario,
        ).to_path()

        sierra_cmd = (
            f"{session.env['ARGOS_BASE_CMD']} "
            f"--controller=foraging.footbot_foraging "
            f"--batch-criteria population_size.Linear3.C3 "
            f"--pipeline 1 2"
        )
        cardinality = 3

    elif engine == "plugins.jsonsim":
        bc = ["max_speed.1.9.C5"]
        template_stem = "template"
        scenario = "scenario1"
        leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
        batch_root = batchroot.ExpRoot(
            sierra_root=f"{session.env['SIERRA_ROOT']}",
            project="projects.sample_jsonsim",
            controller="default.default",
            leaf=leaf,
            scenario=scenario,
        ).to_path()

        sierra_cmd = (
            f"{session.env['JSONSIM_BASE_CMD']} "
            f"--controller=default.default "
            f"--batch-criteria max_speed.1.9.C5 "
            f"--pipeline 1 2 "
            f"--exec-jobs-per-node 4"
        )
        cardinality = 5
    elif engine == "plugins.yamlsim":
        bc = ["max_speed.1.9.C5"]
        template_stem = "template"
        scenario = "scenario1"
        leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
        batch_root = batchroot.ExpRoot(
            sierra_root=f"{session.env['SIERRA_ROOT']}",
            project="projects.sample_yamlsim",
            controller="default.default",
            leaf=leaf,
            scenario=scenario,
        ).to_path()

        sierra_cmd = (
            f"{session.env['YAMLSIM_BASE_CMD']} "
            f"--controller=default.default "
            f"--batch-criteria tolerance.1.9.C5 "
            f"--pipeline 1 2 "
            f"--exec-jobs-per-node 4"
        )
        cardinality = 5

    elif engine == "engine.ros1gazebo":
        bc = ["population_size.Linear3.C3"]
        template_stem = "turtlebot3_house"
        scenario = "HouseWorld.10x10x2"
        leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
        batch_root = batchroot.ExpRoot(
            sierra_root=session.env["SIERRA_ROOT"],
            project="projects.sample_ros1gazebo",
            controller="turtlebot3.wander",
            leaf=leaf,
            scenario=scenario,
        ).to_path()
        sierra_cmd = (
            f"{session.env['ROS1GAZEBO_BASE_CMD']} "
            f"--batch-criteria population_size.Linear3.C3 "
            f"--pipeline 1 2"
        )
        cardinality = 3

    output_root = batch_root / "exp-outputs"
    scratch_root = batch_root / "scratch"

    if env == "hpc.local":
        # Test with regular output
        session.run(*sierra_cmd.split(), f"--execenv={env}", silent=True)
        utils.stage2_univar_check_outputs(
            engine.split(".")[1], batch_root, cardinality, 4
        )

        # Clear sierra root directory
        if os.path.exists(session.env["SIERRA_ROOT"]):
            shutil.rmtree(session.env["SIERRA_ROOT"])

        # Test with devnull output
        session.run(
            *sierra_cmd.split(),
            "--exec-devnull",
            f"--execenv={env}",
            "--exec-parallelism-paradigm=per-exp",
        )
        utils.stage2_univar_check_outputs(
            engine.split(".")[1], batch_root, cardinality, 4
        )

        # Check engine produced no output
        for i in range(3):
            for stdout_file in os.listdir(scratch_root / f"c1-exp{i}/1"):
                stdout_path = scratch_root / f"c1-exp{i}/1/{stdout_file}/stdout"

                stderr_path = scratch_root / f"c1-exp{i}/1/{stdout_file}/stderr"
                assert not os.path.getsize(
                    stdout_path
                ), f"File {stdout_path} is not empty"
                assert not os.path.getsize(
                    stderr_path
                ), f"File {stderr_path} is not empty"

    elif env == "hpc.adhoc":
        # Set up node file for adhoc execution
        with open("/tmp/nodefile", "w") as f:
            f.write(":")  # ":" means run on localhost in GNU parallel

        session.env["SIERRA_NODEFILE"] = "/tmp/nodefile"
        session.run(
            *sierra_cmd.split(),
            f"--execenv={env}",
            "--exec-parallelism-paradigm=per-exp",
            silent=True,
        )
        utils.stage2_univar_check_outputs(
            engine.split(".")[1], batch_root, cardinality, 4
        )

    elif env == "hpc.slurm":
        os.environ["SIERRA_CMD"] = sierra_cmd
        session.run(
            "sbatch",
            "--wait",
            "-v",
            "--export=ALL",
            "./tests/smoke_tests/slurm-test.sh",
            external=True,
            silent=True,
        )
        utils.stage2_univar_check_outputs(
            engine.split(".")[1], batch_root, cardinality, 4
        )

    elif env == "hpc.pbs":
        os.environ["SIERRA_CMD"] = sierra_cmd

        # 2025-09-19 [JRH]: I can't get OpenPBS to work and the documentation is
        # pretty terrible, and I ESPECIALLY can't get it to work in a
        # container. Therefore, the test for this execution environment is a
        # (much) lower fidelity mock:
        #
        # - We manually set the necessary PBS environment variables.
        #
        # - We don't submit our script to the server via qsub, but rather just
        #   run it directly.
        session.run(
            "./tests/smoke_tests/pbs-test.sh",
            external=True,
            silent=True,
        )
        utils.stage2_univar_check_outputs(
            engine.split(".")[1], batch_root, cardinality, 4
        )


@nox.session(python=utils.versions, tags=["prefectserver"])
@nox.parametrize("env", ["prefectserver.local"], ["prefectserver.dockerremote"])
@setup.session_setup
@setup.session_teardown
def execenv_prefectserver(session, env):
    """Check prefect execution environments work.

    Currently only tests with JSONSIM engine.
    """
    bc = ["max_speed.1.9.C5"]
    template_stem = "template"
    scenario = "scenario1"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_jsonsim",
        controller="default.default",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    # Base command
    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 1 2"
    )

    prefect_api_url = "http://127.0.0.1:4200/api"
    # Set prefect API URL
    session.env["PREFECT_API_URL"] = prefect_api_url
    os.environ["PREFECT_API_URL"] = prefect_api_url

    worker_process = None
    server_process = None

    if env == "prefectserver.local":
        # Clear prefect directory
        prefect_dir = pathlib.Path.home() / ".prefect"
        if prefect_dir.exists():
            shutil.rmtree(prefect_dir)

        session.run(*f"{sierra_cmd} --execenv=prefectserver.local".split(), silent=True)

    elif env == "prefectserver.dockerremote":
        # Clear prefect directory
        prefect_dir = pathlib.Path.home() / ".prefect"
        if prefect_dir.exists():
            shutil.rmtree(prefect_dir)

        # Build docker image
        username = subprocess.check_output(["whoami"]).decode().strip()
        session.run(
            "docker",
            "build",
            ".",
            "-f",
            "tests/smoke_tests/prefectserver.dockerremote.Dockerfile",
            "-t",
            "sierra-test:latest",
            "--build-arg",
            f"USERNAME={username}",
            external=True,
        )

        # Start prefect server
        server_process = subprocess.Popen(["prefect", "server", "start"])

        # Wait for Prefect server to be ready
        session.log("Waiting for Prefect server to be ready...")
        max_retries = 30
        count = 0
        while True:
            try:
                response = requests.get(f"{prefect_api_url}/health", timeout=5)
                if response.ok:
                    break
            except requests.RequestException:
                pass

            count += 1
            if count >= max_retries:
                session.error("Error: Timed out waiting for Prefect server to start")

            session.log(f"Waiting for server to be ready... ({count}/{max_retries})")
            time.sleep(2)

        session.log("Prefect server is ready!")

        # Create work pool and queue
        try:
            session.run(
                "prefect",
                "work-pool",
                "create",
                "sierra-pool",
                "--type",
                "docker",
            )
        except Exception:
            session.log("Pool already exists")

        try:
            session.run(
                "prefect",
                "work-queue",
                "create",
                "sierra-queue",
                "--pool",
                "sierra-pool",
            )
        except Exception:
            session.log("Queue already exists")

        # Inspect pool and queue
        session.run("prefect", "work-pool", "inspect", "sierra-pool")
        session.run("prefect", "work-queue", "inspect", "sierra-queue")

        # Start worker
        worker_process = subprocess.Popen(
            [
                "prefect",
                "worker",
                "start",
                "--type",
                "docker",
                "--pool",
                "sierra-pool",
                "--work-queue",
                "sierra-queue",
            ]
        )

        # Wait for worker to be ready
        session.log("Waiting for worker to be ready...")
        max_retries = 30
        count = 0
        while True:
            # Check if worker process is still running
            if worker_process.poll() is not None:
                session.error("Error: Worker process exited unexpectedly")

            # Check if worker is connected to the pool
            try:
                result = subprocess.check_output(
                    ["prefect", "work-pool", "ls"]
                ).decode()
                if "sierra" in result:
                    break
            except Exception:
                pass

            count += 1
            if count >= max_retries:
                session.error("Error: Timed out waiting for Prefect worker to start")

            session.log(f"Waiting for worker to be ready... ({count}/{max_retries})")
            time.sleep(2)

        session.log("Prefect worker is ready!")

        # Run with prefect docker remote
        sierra_repo = os.getcwd()
        sample_root = session.env["SIERRA_SAMPLE_ROOT"]

        session.run(
            *f"{sierra_cmd} --execenv=prefectserver.dockerremote".split(),
            "--docker-extra-mounts",
            f"{sierra_repo}:{sierra_repo}",
            f"{sample_root}:{sample_root}",
            "--docker-image",
            "sierra-test:latest",
            silent=True,
        )

    utils.stage2_univar_check_outputs("jsonsim", batch_root, 5, 4)

    # Kill any prefect processes
    subprocess.run("killall prefect", check=False, shell=True)

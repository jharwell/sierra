#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
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
from tests._framework import engines, verify
from tests._framework import env as fwenv
from tests._framework.command import SierraCommand


#: Per-engine execenv extras that are NOT part of the EngineSpec (which only
#: describes the engine's own identity/outputs, not how a particular smoke
#: session drives it). Keyed by the engine-string the session parametrizes over.
#: ``extra_flags`` are appended to the spec-built command for that engine.
_EXECENV_EXTRAS = {
    "engine.argos": {"extra_flags": ()},
    "plugins.jsonsim": {"extra_flags": ("--exec-jobs-per-node", "4")},
    "plugins.yamlsim": {"extra_flags": ("--exec-jobs-per-node", "4")},
    "engine.ros1gazebo": {"extra_flags": ()},
}


def _execenv_setup(session, engine_str):
    """Resolve the EngineSpec for an execenv engine-string and build its batch
    root + base command, entirely from the spec.

    Every field (project/controller/scenario/template_stem/batch_criteria/
    cardinality) comes from the spec, so the batch root and the command are
    guaranteed consistent: the spec's ``batch_criteria`` feeds BOTH the computed
    root and the ``--batch-criteria`` flag, so the path can never diverge from
    where SIERRA actually writes output.
    """
    spec = engines.BY_NAME[engine_str.split(".")[1]]
    bc = spec.batch_criteria

    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=spec.template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project=spec.project,
        controller=spec.controller,
        leaf=leaf,
        scenario=spec.scenario,
    ).to_path()

    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--controller", spec.controller)
        .set("--batch-criteria", bc)
        .pipeline(1, 2)
    )
    for i in range(0, len(_EXECENV_EXTRAS[engine_str]["extra_flags"]), 2):
        flag, val = _EXECENV_EXTRAS[engine_str]["extra_flags"][i : i + 2]
        cmd.set(flag, val)

    return spec, batch_root, cmd


@nox.session(python=fwenv.VERSIONS, tags=["hpc", "presence", "smoke"])
@nox.parametrize(
    "env", ["hpc.local", "hpc.adhoc", "hpc.slurm", "hpc.pbs", "hpc.awsbatch"]
)
@nox.parametrize(
    "eng",
    ["engine.argos", "engine.ros1gazebo", "plugins.jsonsim", "plugins.yamlsim"],
    # ids are the short engine names, NOT the engine_module strings: nox matches
    # ``-k`` expressions against the full parametrized session name, so a raw
    # value like ``engine.argos`` would make this hpc-tagged session also match
    # the ``engine`` keyword of the plugin-engine slice and run there too.
    ids=["argos", "ros1gazebo", "jsonsim", "yamlsim"],
    # Tag the ros1gazebo row `ros` so it selects only into the ubuntu20.04 `ros`
    # slice (and even there the unsupported-execenv guard skips it, since ROS1
    # rejects the HPC schedulers). Non-ROS rows carry no extra tag.
    tags=[[], ["ros"], [], []],
)
@fwenv.session_setup
@fwenv.session_teardown
def execenv_hpc(session, env, eng):
    """Check that all HPC plugins work across multiple engines.

    Currently just JSONSIM and ARGoS, but more should be added as more engines
    make it into the core.
    """
    # Some engine/execenv pairings are unsupported by SIERRA itself (the
    # ros1gazebo plugin rejects the HPC-scheduler execenvs), and some execenvs
    # need daemons/toolchains that aren't present in every CI container. Skip
    # (rather than fail) those so the slice reflects "unsupported here", not a
    # regression. Engines absent from the map support every execenv.
    _UNSUPPORTED_EXECENV = {
        # ROS1+Gazebo doesn't support the HPC scheduler execenvs; keep it to
        # the local/adhoc set it can actually run.
        "engine.ros1gazebo": {"hpc.slurm", "hpc.pbs", "hpc.awsbatch"},
    }
    if env in _UNSUPPORTED_EXECENV.get(eng, set()):
        session.skip(f"{env} is unsupported on {eng}")

    spec, batch_root, cmd = _execenv_setup(session, eng)
    cardinality = spec.cardinality
    # The SLURM/PBS/awsbatch branches drive SIERRA through a shell script and
    # pass the command via os.environ["SIERRA_CMD"], which must be a string; the
    # hpc.local/adhoc branches append per-execenv flags to the builder directly.
    sierra_cmd = " ".join(cmd.render())

    scratch_root = batch_root / "scratch"

    if env == "hpc.local":
        # Test with regular output
        session.run(*cmd.copy().set("--execenv", env).render(), silent=True)
        verify.verify_stage(
            spec,
            2,
            batch_root,
            max_tier=1,
            cardinality_override=cardinality,
        )

        # Clear sierra root directory
        fwenv.reset_root(session)

        # Test with devnull output
        session.run(
            *cmd.copy()
            .set("--exec-devnull")
            .set("--execenv", env)
            .set("--exec-parallelism-paradigm", "per-exp")
            .render()
        )
        verify.verify_stage(
            spec,
            2,
            batch_root,
            max_tier=1,
            cardinality_override=cardinality,
        )

        # Check the engine produced no output, over its actual cardinality.
        for i in range(cardinality):
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
        # Set up node file for adhoc execution, under the per-session scratch
        # dir rather than a hardcoded /tmp path.
        nodefile = pathlib.Path(session.env["SIERRA_SCRATCH"]) / "adhoc-nodefile"
        nodefile.write_text(":")  # ":" means run on localhost in GNU parallel

        session.env["SIERRA_NODEFILE"] = str(nodefile)
        session.run(
            *cmd.copy()
            .set("--execenv", env)
            .set("--exec-parallelism-paradigm", "per-exp")
            .render(),
            silent=True,
        )
        verify.verify_stage(
            spec,
            2,
            batch_root,
            max_tier=1,
            cardinality_override=cardinality,
        )

    elif env == "hpc.slurm":
        # Bring slurm up
        session.run(
            "bash",
            "./tests/smoke/slurm-start.sh",
            external=True,
        )
        os.environ["SIERRA_CMD"] = sierra_cmd
        session.run(
            "sbatch",
            "--wait",
            "-v",
            "--export=ALL",
            "./tests/smoke/slurm-test.sh",
            external=True,
            silent=True,
        )
        verify.verify_stage(
            spec,
            2,
            batch_root,
            max_tier=1,
            cardinality_override=cardinality,
        )

    elif env == "hpc.pbs":
        os.environ["SIERRA_CMD"] = sierra_cmd

        # Bring PBS fully up: postgres -> daemons -> node registration ->
        # scheduling on -> wait for the node to reach 'free'. This must run
        # through a real shell because the script uses source/&&/${}/pipes;
        # session.run(..., external=True) execs a single program with argv and
        # does NOT go through a shell, so those constructs would be passed
        # literally.
        session.run(
            "bash",
            "./tests/smoke/pbs-start.sh",
            external=True,
        )

        # `qsub -W block=true` makes qsub wait for the job to finish before
        # returning, so the output check below runs against completed results
        # (the analog of the SLURM path's `sbatch --wait`). `-V` exports the
        # submitter environment into the job.
        session.run(
            "/opt/pbs/bin/qsub",
            "-V",
            "-W",
            "block=true",
            "./tests/smoke/pbs-test.sh",
            external=True,
            silent=True,
            success_codes=[0, 1],
        )
        session.run(
            "sh",
            "-c",
            "find /github/home/test .  -name 'sierra_smoke.o*' -o -name 'sierra_smoke.e*' "
            "-o -name '*.o0' -o -name '*.e0' 2>/dev/null | xargs -r cat; true",
            external=True,
        )
        # job id is 0.<host> for the first job; dump its output files
        session.run(
            "sh",
            "-c",
            "cat pbs-test.sh.o* pbs-test.sh.e* 2>/dev/null || true",
            external=True,
        )

        # PBS's own stitched log for the job
        session.run(
            "/opt/pbs/bin/tracejob", "0", success_codes=range(0, 256), external=True
        )
        session.run("sh", "-c", "cat /tmp/pbs-test.out; true", external=True)
        verify.verify_stage(
            spec,
            2,
            batch_root,
            max_tier=1,
            cardinality_override=cardinality,
        )

    elif env == "hpc.awsbatch":
        os.environ["SIERRA_CMD"] = sierra_cmd

        # Real awsbatch testing would cost $ on AWS, so this execenv is a
        # (much) lower-fidelity mock.
        session.run(
            "./tests/smoke/awsbatch-test.sh",
            external=True,
            silent=True,
        )
        verify.verify_stage(
            spec,
            2,
            batch_root,
            max_tier=1,
            cardinality_override=cardinality,
        )


@nox.session(python=fwenv.VERSIONS, tags=["prefectserver", "presence", "smoke"])
@nox.parametrize("env", ["prefectserver.local"], ["prefectserver.dockerremote"])
@fwenv.session_setup
@fwenv.session_teardown
def execenv_prefectserver(session, env):
    """Check prefect execution environments work.

    Currently only tests with JSONSIM engine.
    """
    spec = engines.BY_NAME["jsonsim"]
    bc = spec.batch_criteria

    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=spec.template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project=spec.project,
        controller=spec.controller,
        leaf=leaf,
        scenario=spec.scenario,
    ).to_path()

    # Base command builder; branches below append --execenv (and, for the
    # dockerremote case, mount/image flags) via .copy().set(...).
    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--controller", spec.controller)
        .set("--batch-criteria", bc)
        .pipeline(1, 2)
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

        session.run(
            *cmd.copy().set("--execenv", "prefectserver.local").render(), silent=True
        )

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
            "tests/smoke/prefectserver.dockerremote.Dockerfile",
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
            *cmd.copy().set("--execenv", "prefectserver.dockerremote").render(),
            "--docker-extra-mounts",
            f"{sierra_repo}:{sierra_repo}",
            f"{sample_root}:{sample_root}",
            "--docker-image",
            "sierra-test:latest",
            silent=True,
        )

    verify.verify_stage(
        spec,
        2,
        batch_root,
        max_tier=1,
        cardinality_override=spec.cardinality,
    )

    # Kill any prefect processes
    subprocess.run("killall prefect", check=False, shell=True)

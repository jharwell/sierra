#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import os
import functools
import shutil
import subprocess
import site

# 3rd party packages
import nox

# Project packages


def setup_env(session) -> None:
    session.install("-e", ".")

    # Default to local testing
    argos_install_prefix = pathlib.Path.home() / ".local"
    sierra_sample_root = pathlib.Path.home() / "git/thesis/sierra-sample-project"

    session.env["SIERRA_ROOT"] = pathlib.Path.home() / "test"

    # This is for running on github actions in a container.
    if "GITHUB_ACTIONS" in os.environ:
        session.log("Initialize env for running in github CI")
        argos_install_prefix = pathlib.Path("/usr/local")
        sierra_sample_root = (
            pathlib.Path(os.getenv("GITHUB_WORKSPACE")) / "sierra-sample-project"
        )

    if "LD_LIBRARY_PATH" in os.environ:
        session.log("Appending to LD_LIBRARY_PATH")
        session.env["LD_LIBRARY_PATH"] = "{0}:{1}".format(
            os.environ["LD_LIBRARY_PATH"], str(argos_install_prefix / "lib/argos3")
        )
    else:
        session.env["LD_LIBRARY_PATH"] = str(argos_install_prefix / "lib/argos3")

    session.env["ARGOS_INSTALL_PREFIX"] = argos_install_prefix
    session.env["SIERRA_SAMPLE_ROOT"] = sierra_sample_root

    # This is for running on github actions NOT in a container
    if "SIERRA_PLUGIN_PATH" in os.environ:
        session.env["SIERRA_PLUGIN_PATH"] = "{0}:{1}".format(
            os.environ["SIERRA_PLUGIN_PATH"], session.env["SIERRA_SAMPLE_ROOT"]
        )
    else:
        session.env["SIERRA_PLUGIN_PATH"] = session.env["SIERRA_SAMPLE_ROOT"]

    session.env["ARGOS_PLUGIN_PATH"] = "{0}:{1}".format(
        session.env["ARGOS_INSTALL_PREFIX"] / "lib/argos3",
        session.env["SIERRA_SAMPLE_ROOT"] / "argos/build",
    )
    session.log(f"{session.env['SIERRA_PLUGIN_PATH']=}")
    session.log(f"{session.env['ARGOS_PLUGIN_PATH']=}")
    session.log(f"{session.env['LD_LIBRARY_PATH']=}")

    session.env["PARALLEL"] = "--env ARGOS_PLUGIN_PATH --env LD_LIBRARY_PATH"

    # Display which python we're using
    session.run("which", "python3", external=True)

    # Create a nodefile for SIERRA
    with open("/tmp/nodefile", "w") as f:
        f.write("localhost\n")
    session.env["SIERRA_NODEFILE"] = "/tmp/nodefile"

    # Remove any existing SIERRA config
    rcpath = pathlib.Path("$HOME/.sierrarc")
    if rcpath.exists():
        rcpath.unlink()


def session_setup(func):
    @functools.wraps(func)
    def wrapper(session, *args, **kwargs):
        setup_env(session)
        executable = session.run(
            "which",
            "sierra-cli",
            silent=True,
        )
        coverage_cmd = f"coverage run --debug=debug {executable}"

        session.env["COVERAGE_CMD"] = coverage_cmd

        # 2025-09-25 [JRH]: The factor here is from the hard-coded output
        # interval of 10 in the ARGoS sample project.
        session.env["ARGOS_BASE_CMD"] = (
            f"{coverage_cmd} "
            f"--sierra-root={session.env['SIERRA_ROOT']} "
            f"--controller=foraging.footbot_foraging "
            f"--engine=engine.argos "
            f"--project=projects.sample_argos "
            f"--exp-setup=exp_setup.T50.K5 "
            f"--n-runs=4 "
            f"--physics-n-engines=1 "
            f"-xstrict "
            f"--expdef-template={session.env['SIERRA_SAMPLE_ROOT']}/exp/argos/template.argos "
            f"--scenario=LowBlockCount.10x10x2 "
            f"--with-robot-leds "
            f"--with-robot-rab "
            f"--log-level=TRACE "
            f"--df-verify "
            f"--exp-n-datapoints-factor=0.1 "
        )

        session.env["JSONSIM_BASE_CMD"] = (
            f"{coverage_cmd} "
            f"--sierra-root={session.env['SIERRA_ROOT']} "
            f"--controller=default.default "
            f"--engine=plugins.jsonsim "
            f"--project=projects.sample_jsonsim "
            f"--exp-setup=exp_setup.T50 "
            f"--n-runs=4 "
            f"-xstrict "
            f"--expdef-template={session.env['SIERRA_SAMPLE_ROOT']}/exp/jsonsim/template.json "
            f"--scenario=scenario1 "
            f"-xno-devnull "
            f"--expdef=expdef.json "
            f"--jsonsim-path={session.env['SIERRA_SAMPLE_ROOT']}/plugins/jsonsim/jsonsim.py "
            f"--log-level=TRACE "
            f"--df-verify "
            f"--proc proc.statistics proc.collate "
        )

        session.env["YAMLSIM_BASE_CMD"] = (
            f"{coverage_cmd} "
            f"--sierra-root={session.env['SIERRA_ROOT']} "
            f"--controller=default.default "
            f"--engine=plugins.yamlsim "
            f"--project=projects.sample_yamlsim "
            f"--n-runs=4 "
            f"-xstrict "
            f"--expdef-template={session.env['SIERRA_SAMPLE_ROOT']}/exp/yamlsim/template.yaml "
            f"--scenario=scenario1 "
            f"-xno-devnull "
            f"--expdef=expdef.yaml "
            f"--yamlsim-path={session.env['SIERRA_SAMPLE_ROOT']}/plugins/yamlsim/yamlsim.py "
            f"--log-level=TRACE "
            f"--proc proc.statistics proc.collate "
        )

        session.env["ROS1ROBOT_BASE_CMD"] = (
            f"{session.env['COVERAGE_CMD']} "
            f"--sierra-root={session.env['SIERRA_ROOT']} "
            f"--engine=engine.ros1robot "
            f"--project=projects.sample_ros1robot "
            f"--exp-setup=exp_setup.T10.K5.N50 "
            f"--n-runs=4 "
            f"--expdef-template={session.env['SIERRA_SAMPLE_ROOT']}/exp/ros1robot/turtlebot3.launch "
            f"--scenario=OutdoorWorld.10x10x2 "
            f"--controller=turtlebot3.wander "
            f"--robot turtlebot3 "
            f"--execenv robot.turtlebot3 "
            f"-sonline-check "
            f"-ssync "
            f"--log-level=TRACE "
            f"--df-verify "
        )

        session.env["ROS1GAZEBO_BASE_CMD"] = (
            f"{session.env['COVERAGE_CMD']} "
            f"--sierra-root={session.env['SIERRA_ROOT']} "
            f"--engine=engine.ros1gazebo "
            f"--project=projects.sample_ros1gazebo "
            f"--exp-setup=exp_setup.T5.K2 "
            f"--n-runs=4 "
            f"-xstrict "
            f"--expdef-template={session.env['SIERRA_SAMPLE_ROOT']}/exp/ros1gazebo/turtlebot3_house.launch "
            f"--scenario=HouseWorld.10x10x2 "
            f"--controller=turtlebot3.wander "
            f"--robot turtlebot3 "
            f"--log-level=TRACE "
            f"--df-verify "
        )
        session.log("Setting up environment...")

        # Clear sierra root directory
        if session.env["SIERRA_ROOT"].exists():
            shutil.rmtree(session.env["SIERRA_ROOT"])

        return func(session, *args, **kwargs)

    return wrapper


def session_teardown(func):
    @functools.wraps(func)
    def wrapper(session, *args, **kwargs):
        session.log("Cleaning up environment...")

        # Clear sierra root directory
        if session.env["SIERRA_ROOT"].exists():
            shutil.rmtree(session.env["SIERRA_ROOT"])

        return func(session, *args, **kwargs)

    return wrapper

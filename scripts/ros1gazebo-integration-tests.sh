#!/bin/bash -l
#
################################################################################
# Setup Environment
################################################################################
export SIERRA_ROOT=$HOME/test

if [ "$GITHUB_ACTIONS" = true ]; then
    export SAMPLE_ROOT=$HOME/work/sierra-sample-project
else
    export SAMPLE_ROOT=$HOME/git/sierra-sample-project
fi

export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT/projects
export SIERRA_ROSBRIDGE_INSTALL_PREFIX=$HOME/.local

. $SIERRA_ROSBRIDGE_INSTALL_PREFIX/setup.bash

export SIERRA_BASE_CMD="sierra-cli \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.ros1gazebo \
       --project=ros1gazebo_project \
       --exp-setup=exp_setup.T10.K5\
       --n-runs=4 \
       --exec-strict\
       --template-input-file=$SAMPLE_ROOT/exp/ros1gazebo/turtlebot3_house.launch \
       --scenario=HouseWorld.10x10x1 \
       --controller=turtlebot3.wander \
       --robot turtlebot3\
       --exec-no-devnull \
       --log-level=TRACE"

sanity_check_pipeline() {
    SIERRA_CMD="$*"

    rm -rf $SIERRA_ROOT

    # The ROS1+gazebo sample project does not current output anything, so we
    # can't run stage 3 or 4 :-(.
    $SIERRA_CMD --pipeline 1

    $SIERRA_CMD --pipeline 2

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --pipeline 1 2
}

################################################################################
# Check that the batch criteria that come with SIERRA for ROS1+Gazebo work.
################################################################################
batch_criteria_test() {
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3"

    sanity_check_pipeline $SIERRA_CMD

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Log8"

    sanity_check_pipeline $SIERRA_CMD

}

################################################################################
# Run Tests
################################################################################
# Exit anytime SIERRA crashes or a command fails
set -e

# Echo cmds to stdout
set -x

rospack find sierra_rosbridge

cd $SAMPLE_ROOT
ls -alh
python3 -m projects.ros1gazebo_project.generators.scenario_generators

batch_criteria_test

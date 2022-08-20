#!/bin/bash -l
#
################################################################################
# Setup Environment
################################################################################
setup_env() {
    export SIERRA_ROOT=$HOME/test

    if [ "$GITHUB_ACTIONS" = true ]; then
        export SAMPLE_ROOT=$HOME/work/sierra-sample-project
    else
        export SAMPLE_ROOT=$HOME/git/sierra-sample-project
    fi

    export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT/projects

    localsite=$(python3 -m site --user-site)
    localbase=$(python3 -m site --user-base)

    # I should NOT have to do this, but (apparentwly) PATH is reset
    # between jobs in a workflow  on OSX, and doing this the way
    # github says to do doesn't work.
    export PATH=$pythonLocation/bin:$PATH

    # Required to get coverage.py to work with the installed version
    # of SIERRA. Omitting this results in either nothing getting
    # measured because the local site-packages is omitted, or if that
    # is included ALL locally installed packages get measured.
    export PYTHONPATH=$PYTHONPATH:$PWD

    which sierra-cli
    which python3

    echo ":" >> /tmp/nodefile
    export SIERRA_NODEFILE=/tmp/nodefile

    export COVERAGE_CMD="coverage \
    run \
     --debug=debug \
     $(which sierra-cli)"

    export SIERRA_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.ros1robot \
       --project=ros1robot_project \
       --exp-setup=exp_setup.T10.K5.N50\
       --n-runs=4 \
       --template-input-file=$SAMPLE_ROOT/exp/ros1robot/turtlebot3.launch \
       --scenario=OutdoorWorld.10x10x2 \
       --controller=turtlebot3.wander \
       --robot turtlebot3
       --skip-online-check\
       --skip-sync\
       --log-level=TRACE"

    export PARALLEL="--env LD_LIBRARY_PATH"
}

################################################################################
# Check that the batch criteria that come with SIERRA for ROS1+robot work.
################################################################################
bc_univar_sanity_test() {
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3"

    $SIERRA_CMD --pipeline 1
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Log8"

    $SIERRA_CMD --pipeline 1
    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 1 outputs what it is supposed to
################################################################################
stage1_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"ros1robot_project\",[\"population_size.Linear3.C3\"],\"OutdoorWorld.10x10x2\",\"turtlebot3.wander\", \"turtlebot3\"))")

    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 "

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$input_root/exp$i" ] || false
    done

    # Check stage1 generated stuff
    for exp in {0..2}; do
        for run in {0..3}; do
            [ -f "$input_root/exp${exp}/commands_run${run}_master.txt" ] || false
            [ -f "$input_root/exp${exp}/commands_run${run}_slave.txt" ] || false
            [ -f "$input_root/exp${exp}/exp_def.pkl" ] || false
            [ -f "$input_root/exp${exp}/seeds.pkl" ] || false
            [ -f "$input_root/exp${exp}/turtlebot3_run${run}_master.launch" ] ||false
            [ -f "$input_root/exp${exp}/turtlebot3_run${run}_robot${exp}.launch" ] || false
        done
    done

    rm -rf $SIERRA_ROOT
}


################################################################################
# Run Tests
################################################################################
setup_env

# Exit anytime SIERRA crashes or a command fails
set -e

# Echo cmds to stdout
set -x

func=NONE
exec_env=''

while getopts f:e: arg; do
    case "$arg" in
        f) func="$OPTARG";;
        e) exec_env="$OPTARG";;
        *) exit 2;;
    esac
done

$func $exec_env

#!/bin/bash -l
#
################################################################################
# Setup Environment
################################################################################
setup_env() {
    export SIERRA_ROOT=$HOME/test

    if [ "$GITHUB_ACTIONS" = true ]; then
        export SAMPLE_ROOT=$GITHUB_WORKSPACE/sierra-sample-project
    else
        export SAMPLE_ROOT=$HOME/git/thesis/sierra-sample-project
    fi
    # Since this is CI, we want to avoid being surprised by deprecated
    # features, so treat them all as errors.
    # export PYTHONWARNINGS=error

    export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT/projects

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
       --engine=engine.ros1robot \
       --project=projects.sample_ros1robot \
       --exp-setup=exp_setup.T10.K5.N50\
       --n-runs=4 \
       --expdef-template=$SAMPLE_ROOT/exp/ros1robot/turtlebot3.launch \
       --scenario=OutdoorWorld.10x10x2 \
       --controller=turtlebot3.wander \
       --robot turtlebot3
       -sonline-check\
       -ssync\
       --log-level=TRACE"

    export PARALLEL="--env LD_LIBRARY_PATH"
}

################################################################################
# Check that the batch criteria that come with SIERRA for ROS1+robot work.
################################################################################
sanity_univar_test() {
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
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"turtlebot3\";
scenario=\"OutdoorWorld.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_ros1robot\",controller=\"turtlebot3.wander\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 "

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$input_root/c1-exp${i}" ] || false
    done

    # Check stage1 generated stuff
    for i in {0..2}; do
        for run in {0..3}; do
            [ -f "$input_root/c1-exp${i}/commands_run${run}_master.txt" ] || false
            [ -f "$input_root/c1-exp${i}/commands_run${run}_slave.txt" ] || false
            [ -f "$input_root/c1-exp${i}/exp_def.pkl" ] || false
            [ -f "$input_root/c1-exp${i}/seeds.pkl" ] || false
            [ -f "$input_root/c1-exp${i}/turtlebot3_run${run}_master.launch" ] ||false
            [ -f "$input_root/c1-exp${i}/turtlebot3_run${run}_robot${i}.launch" ] || false
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

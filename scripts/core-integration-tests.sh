#!/bin/bash -l
#
################################################################################
# Setup Environment
################################################################################
setup_env() {
    export SIERRA_ROOT=$HOME/test

    if [ "$GITHUB_ACTIONS" = true ]; then
        export SAMPLE_ROOT=$HOME/work/sierra-sample-project
        export ARGOS_INSTALL_PREFIX=/usr/local

    else
        export SAMPLE_ROOT=$HOME/git/sierra-sample-project
        export ARGOS_INSTALL_PREFIX=/$HOME/.local

    fi

    # Set ARGoS library search path. Must contain both the ARGoS core libraries path
    # AND the sample project library path.
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARGOS_INSTALL_PREFIX/lib/argos3
    export ARGOS_PLUGIN_PATH=$ARGOS_INSTALL_PREFIX/lib/argos3:$SAMPLE_ROOT/argos/build
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

    export SIERRA_BASE_CMD_ARGOS="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --controller=foraging.footbot_foraging \
       --platform=platform.argos \
       --project=argos_project \
       --exp-setup=exp_setup.T5000.K5 \
       --n-runs=4 \
       --exec-strict \
       --template-input-file=$SAMPLE_ROOT/exp/argos/template.argos \
       --scenario=LowBlockCount.10x10x2 \
       --exec-no-devnull \
       --with-robot-leds \
       --with-robot-rab\
       --log-level=TRACE"

    export PARALLEL="--env LD_LIBRARY_PATH"

    export SIERRA_BASE_CMD_ROS1GAZEBO="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.ros1gazebo \
       --project=ros1gazebo_project \
       --exp-setup=exp_setup.T10.K5.N50\
       --n-runs=4 \
       --exec-strict\
       --template-input-file=$SAMPLE_ROOT/exp/ros1gazebo/turtlebot3_house.launch \
       --scenario=HouseWorld.10x10x2 \
       --controller=turtlebot3.wander \
       --robot turtlebot3\
       --exec-no-devnull \
       --log-level=TRACE"

}

################################################################################
# Check usage of environment variables
################################################################################
env_vars_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"ros1robot_project\",[\"population_size.Linear3.C3\"],\"OutdoorWorld.10x10x2\",\"turtlebot3.wander\", \"turtlebot3\"))")

    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    # Test SIERRA_ARCH
    export SIERRA_ARCH=fizzbuzz

    which argos3
    ln -s /usr/local/bin/argos3 /usr/local/bin/argos3-fizzbuzz
    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2"

    $SIERRA_CMD

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check cmdline options
################################################################################
cmdline_opts_test() {
    criteria=(population_size.Linear3.C3
              population_variable_density.1p0.4p0.C4)

    # Check plotting opts
    for bc in "${criteria[@]}"; do
        SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
        --physics-n-engines=1 \
        --batch-criteria ${bc}"

        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --pipeline 1 2 3

        $SIERRA_CMD --pipeline 4 --plot-log-xscale
        $SIERRA_CMD --pipeline 4 --plot-enumerated-xscale
        $SIERRA_CMD --pipeline 4 --plot-log-yscale
        $SIERRA_CMD --pipeline 4 --plot-large-text
    done
    rm -rf $SIERRA_ROOT

    # Check serial processing
    $SIERRA_CMD --pipeline 1 2 3 4 --processing-serial

    # Check version
    $SIERRA_CMD --version
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

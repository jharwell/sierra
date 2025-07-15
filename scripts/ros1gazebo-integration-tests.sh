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
    export SIERRA_ROSBRIDGE_INSTALL_PREFIX=$HOME/.local

    . $SIERRA_ROSBRIDGE_INSTALL_PREFIX/setup.bash

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
    which gazebo
    gazebo -v
    
    export COVERAGE_CMD="coverage \
    run \
     --debug=debug \
     $(which sierra-cli)"

    export SIERRA_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --engine=engine.ros1gazebo \
       --project=projects.sample_ros1gazebo \
       --exp-setup=exp_setup.T5.K5\
       --n-runs=4 \
       -xstrict \
       --expdef-template=$SAMPLE_ROOT/exp/ros1gazebo/turtlebot3_house.launch \
       --scenario=HouseWorld.10x10x2 \
       --controller=turtlebot3.wander \
       --robot turtlebot3 \
       -xno-devnull \
       --log-level=TRACE"

    export PARALLEL="--env LD_LIBRARY_PATH"
}

################################################################################
# Check that stage 1 outputs what it is supposed to
################################################################################
stage1_univar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"turtlebot3_house\";
scenario=\"HouseWorld.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_ros1gazebo\",controller=\"turtlebot3.wander\",leaf=leaf).to_path();
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
        [ -d "$input_root/c1-exp$[i]" ] || false
    done

    # Check stage1 generated stuff
    for i in {0..2}; do
        [ -f "$input_root/c1-exp${i}/commands.txt" ] || false
        [ -f "$input_root/c1-exp${i}/exp_def.pkl" ] || false
        [ -f "$input_root/c1-exp${i}/seeds.pkl" ] || false

        for run in {0..3}; do
            [ -f "$input_root/c1-exp${i}/turtlebot3_house_run${run}_master.launch" ] ||false
            [ -f "$input_root/c1-exp${i}/turtlebot3_house_run${run}_robots.launch" ] || false
        done
    done

    rm -rf $SIERRA_ROOT
}


################################################################################
# Check that stage 2 works for all exec envs
################################################################################
stage2_univar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"turtlebot3_house\";
scenario=\"HouseWorld.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_ros1gazebo\",controller=\"turtlebot3.wander\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    scratch_root=$batch_root/scratch/

    export SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 "

    env=$1

    rm -rf $SIERRA_ROOT

    if [ "$env" = "hpc.local" ]; then
        $SIERRA_CMD --exec-env=hpc.local

        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --exec-env=hpc.local --exec-devnull

        # Check no output produced
        for i in {0..2}; do
            [ ! -s "$scratch_root/c1-exp${i}/1/*/stdout" ]
            [ ! -s "$scratch_root/c1-exp${i}/1/*/stderr" ]
        done

        rm -rf $SIERRA_ROOT

    elif [ "$env" = "hpc.adhoc" ]; then
        # : -> "run on localhost" in GNU parallel
        echo ":" > /tmp/nodefile
        export SIERRA_NODEFILE=/tmp/nodefile

        $SIERRA_CMD --exec-env=hpc.adhoc

        rm -rf $SIERRA_ROOT
    elif [ "$env" = "hpc.slurm" ]; then
        sbatch --wait -v --export=ALL ./scripts/slurm-test.sh
        # cat R-*
        # sudo cat /var/log/slurm-llnl/slurmd.log
        # sudo cat /var/log/slurm-llnl/slurmctld.log
        # sinfo

        rm -rf $SIERRA_ROOT
    elif [ "$env" = "hpc.pbs" ]; then
        false
    else
        false
    fi
}

################################################################################
# Run Tests
################################################################################
setup_env

# Exit anytime SIERRA crashes or a command fails
set -e

# Echo cmds to stdout
set -x

rospack find sierra_rosbridge

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

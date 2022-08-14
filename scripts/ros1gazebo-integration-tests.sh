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
    export SIERRA_ROSBRIDGE_INSTALL_PREFIX=$HOME/.local

    . $SIERRA_ROSBRIDGE_INSTALL_PREFIX/setup.bash

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

    export COVERAGE_CMD="coverage \
    run \
     --debug=debug \
     $(which sierra-cli)"

    export SIERRA_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.ros1gazebo \
       --project=ros1gazebo_project \
       --exp-setup=exp_setup.T5.K5\
       --n-runs=4 \
       --exec-strict\
       --template-input-file=$SAMPLE_ROOT/exp/ros1gazebo/turtlebot3_house.launch \
       --scenario=HouseWorld.10x10x2 \
       --controller=turtlebot3.wander \
       --robot turtlebot3\
       --exec-no-devnull \
       --log-level=TRACE"

    export PARALLEL="--env LD_LIBRARY_PATH"
}

################################################################################
# Check that the batch criteria that come with SIERRA for ROS1+Gazebo work.
################################################################################
bc_univar_sanity_test() {

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3"

    $SIERRA_CMD --pipeline 1 2
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Log8"

    $SIERRA_CMD --pipeline 1 2
    rm -rf $SIERRA_ROOT

}

bc_bivar_sanity_test() {
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3 max_speed.1.9.C5"

    $SIERRA_CMD --pipeline 1 2
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria max_speed.1.9.C5 population_size.Linear3.C3"

    $SIERRA_CMD --pipeline 1 2
    rm -rf $SIERRA_ROOT

}
################################################################################
# Check that stage 1 outputs what it is supposed to
################################################################################
stage1_univar_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"ros1gazebo_project\",[\"population_size.Linear3.C3\"],\"HouseWorld.10x10x2\",\"turtlebot3.wander\", \"turtlebot3_house\"))")

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
        [ -f "$input_root/exp${exp}/commands.txt" ] || false
        [ -f "$input_root/exp${exp}/exp_def.pkl" ] || false
        [ -f "$input_root/exp${exp}/seeds.pkl" ] || false

        for run in {0..3}; do
            [ -f "$input_root/exp${exp}/turtlebot3_house_run${run}_master.launch" ] ||false
            [ -f "$input_root/exp${exp}/turtlebot3_house_run${run}_robots.launch" ] || false
        done
    done

    rm -rf $SIERRA_ROOT
}

stage1_bivar_test() {
    batch_root1=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"ros1gazebo_project\",[\"population_size.Linear3.C3\",\"max_speed.1.9.C5\"],\"HouseWorld.10x10x2\",\"turtlebot3.wander\", \"turtlebot3_house\"))")

    input_root1=$batch_root1/exp-inputs/

    batch_root2=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"ros1gazebo_project\",[\"max_speed.1.9.C5\",\"population_size.Linear3.C3\"],\"HouseWorld.10x10x2\",\"turtlebot3.wander\", \"turtlebot3_house\"))")

    input_root2=$batch_root2/exp-inputs/

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3 max_speed.1.9.C5\
    --pipeline 1"

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..2}; do
        for j in {0..4}; do
            [ -d "$input_root1/c1-exp${i}+c2-exp${j}" ] || false
        done
    done

    # Check stage1 generated stuff
    for i in {0..2}; do
        [ $(grep -r "max=\"1.0\"" $input_root1/c1-exp${i}+* | wc -l) -eq "5" ]
        for j in {0..4}; do
            [ -f "$input_root1/c1-exp${i}+c2-exp${j}/commands.txt" ] || false
            [ -f "$input_root1/c1-exp${i}+c2-exp${j}/exp_def.pkl" ] || false
            [ -f "$input_root1/c1-exp${i}+c2-exp${j}/seeds.pkl" ] || false

            for run in {0..3}; do
                [ -f "$input_root1/c1-exp${i}+c2-exp${j}/turtlebot3_house_run${run}_master.launch" ] ||false
                [ -f "$input_root1/c1-exp${i}+c2-exp${j}/turtlebot3_house_run${run}_robots.launch" ] ||false
            done
        done
    done

    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria max_speed.1.9.C5 population_size.Linear3.C3\
    --pipeline 1"

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..4}; do
        for j in {0..2}; do
            [ -d "$input_root2/c1-exp${i}+c2-exp${j}" ] || false
        done
    done

    # Check stage1 generated stuff
    for i in {0..4}; do
        for j in {0..2}; do
            [ $(grep -r "max=\"1.0\"" $input_root2/*+c2-exp${j} | wc -l) -eq "5" ]

            [ -f "$input_root2/c1-exp${i}+c2-exp${j}/commands.txt" ] || false
            [ -f "$input_root2/c1-exp${i}+c2-exp${j}/exp_def.pkl" ] || false
            [ -f "$input_root2/c1-exp${i}+c2-exp${j}/seeds.pkl" ] || false
        done
    done

    rm -rf $SIERRA_ROOT
}


################################################################################
# Check that stage 2 works for all exec envs
################################################################################
stage2_univar_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"ros1gazebo_project\",[\"population_size.Linear3.C3\"],\"HouseWorld.10x10x2\",\"turtlebot3.wander\", \"turtlebot3_house\"))")

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
        for exp in {0..2}; do
            [ ! -s "$scratch_root/exp${exp}/1/*/stdout" ]
            [ ! -s "$scratch_root/exp${exp}/1/*/stderr" ]
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

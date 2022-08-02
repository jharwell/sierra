#!/bin/bash -l

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
    export PYTHONPATH=.
    export COVERAGE_CMD="coverage \
    run \
     --append \
     $localbase/bin/sierra-cli"

    export SIERRA_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.argos \
       --project=argos_project \
       --exp-setup=exp_setup.T5000.K5 \
       --n-runs=4 \
       --exec-strict \
       --template-input-file=$SAMPLE_ROOT/exp/argos/template.argos \
       --scenario=LowBlockCount.10x10x1 \
       --controller=foraging.footbot_foraging \
       --with-robot-leds \
       --with-robot-rab\
       --exec-no-devnull \
       --log-level=DEBUG"

    export PARALLEL="--env ARGOS_PLUGIN_PATH --env LD_LIBRARY_PATH"
}

################################################################################
# Utility funcs
################################################################################
sanity_check_pipeline() {
    SIERRA_CMD="$*"

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --pipeline 1

    $SIERRA_CMD --pipeline 2

    $SIERRA_CMD --pipeline 3

    $SIERRA_CMD --pipeline 4

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --pipeline 1 2 3 4
}

################################################################################
# Check that you can use multiple physics engines and things don't
# crash.
################################################################################
physics_engines_test() {
    ENGINES=(1 2 4 6 8 12 16 24)

    for n in "${ENGINES[@]}"
    do
        SIERRA_CMD="$SIERRA_BASE_CMD \
        --batch-criteria population_size.Linear3.C3\
        --physics-n-engines=$n"

        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --pipeline 1 2

        rm -rf $SIERRA_ROOT
    done
}

################################################################################
# Check that the batch criteria that come with SIERRA for ARGoS work.
################################################################################
batch_criteria_test() {
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3"

    sanity_check_pipeline $SIERRA_CMD

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_size.Log8"

    sanity_check_pipeline $SIERRA_CMD

    # Can't check constant/variable density beyond stage 1--requires
    # changing arena size and also the positions of lights in the
    # sample project :-(.
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_constant_density.CD1p0.I4.C4 \
    --pipeline 1"

    rm -rf $SIERRA_ROOT
    $SIERRA_CMD

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_variable_density.1p0.4p0.C4 \
    --pipeline 1"

    rm -rf $SIERRA_ROOT
    $SIERRA_CMD
}

################################################################################
# Check that stage 1 outputs what it is supposed to
################################################################################
stage1_outputs_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x1\",\"foraging.footbot_foraging\", \"template\"))")

    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 "

    $SIERRA_CMD

    # Check SIERRA directory structure
    [ -d "$input_root/exp0" ] || false
    [ -d "$input_root/exp1" ] || false
    [ -d "$input_root/exp2" ] || false

    # Check stage1 generated stuff
    [ -f "$input_root/exp0/template_run0.argos" ] || false
    [ -f "$input_root/exp0/template_run1.argos" ] || false
    [ -f "$input_root/exp0/template_run2.argos" ] || false
    [ -f "$input_root/exp0/template_run3.argos" ] || false
    [ -f "$input_root/exp0/commands.txt" ] || false

    [ -f "$input_root/exp1/template_run0.argos" ] || false
    [ -f "$input_root/exp1/template_run1.argos" ] || false
    [ -f "$input_root/exp1/template_run2.argos" ] || false
    [ -f "$input_root/exp1/template_run3.argos" ] || false
    [ -f "$input_root/exp1/commands.txt" ] || false

    [ -f "$input_root/exp2/template_run0.argos" ] || false
    [ -f "$input_root/exp2/template_run1.argos" ] || false
    [ -f "$input_root/exp2/template_run2.argos" ] || false
    [ -f "$input_root/exp2/template_run3.argos" ] || false
    [ -f "$input_root/exp2/commands.txt" ] || false

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 2 outputs what it is supposed to
################################################################################
stage2_outputs_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x1\",\"foraging.footbot_foraging\", \"template\"))")

    output_root=$batch_root/exp-outputs/

    export SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 "

    env=$1

    rm -rf $SIERRA_ROOT

    if [ "$env" = "hpc.local" ]; then
        $SIERRA_CMD --exec-env=hpc.local
    elif [ "$env" = "hpc.adhoc" ]; then
        # : -> "run on localhost" in GNU parallel
        echo ":" > /tmp/nodefile
        export SIERRA_NODEFILE=/tmp/nodefile
        $SIERRA_CMD --exec-env=hpc.adhoc
    elif [ "$env" = "hpc.slurm" ]; then
        sbatch --wait -v --export=ALL ./scripts/slurm-test.sh
        # cat R-*
        # sudo cat /var/log/slurm-llnl/slurmd.log
        # sudo cat /var/log/slurm-llnl/slurmctld.log
        # sinfo
    elif [ "$env" = "hpc.pbs" ]; then
        false
    fi

    stage2_check_outputs $batch_root
    rm -rf $SIERRA_ROOT
}

stage2_check_outputs() {
    output_root=$1/exp-outputs

    # Check SIERRA directory structure
    [ -d "$output_root/exp0/template_0_output" ] || false
    [ -d "$output_root/exp0/template_1_output" ] || false
    [ -d "$output_root/exp0/template_2_output" ] || false

    [ -d "$output_root/exp1/template_0_output" ] || false
    [ -d "$output_root/exp1/template_1_output" ] || false
    [ -d "$output_root/exp1/template_2_output" ] || false

    [ -d "$output_root/exp2/template_0_output" ] || false
    [ -d "$output_root/exp2/template_1_output" ] || false
    [ -d "$output_root/exp2/template_2_output" ] || false

    # Check stage2 generated data
    [ -f "$output_root/exp0/template_0_output/output/collected-data.csv" ] || false
    [ -f "$output_root/exp0/template_1_output/output/collected-data.csv" ] || false
    [ -f "$output_root/exp0/template_2_output/output/collected-data.csv" ] || false

    [ -f "$output_root/exp1/template_0_output/output/collected-data.csv" ] || false
    [ -f "$output_root/exp1/template_1_output/output/collected-data.csv" ] || false
    [ -f "$output_root/exp1/template_2_output/output/collected-data.csv" ] || false

    [ -f "$output_root/exp2/template_0_output/output/collected-data.csv" ] || false
    [ -f "$output_root/exp2/template_1_output/output/collected-data.csv" ] || false
    [ -f "$output_root/exp2/template_2_output/output/collected-data.csv" ] || false

}

################################################################################
# Check that stage 3 outputs what it is supposed to
################################################################################
stage3_outputs_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x1\",\"foraging.footbot_foraging\", \"template\"))")

    stat_root=$batch_root/statistics
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 3"

    $SIERRA_CMD

    # Check SIERRA directory structure
    [ -d "$stat_root/exp0" ] || false
    [ -d "$stat_root/exp1" ] || false
    [ -d "$stat_root/exp2" ] || false
    [ -d "$stat_root/collated" ] || false

    # Check stage3 generated statistics
    [ -f "$stat_root/exp0/collected-data.mean" ] || false
    [ -f "$stat_root/exp1/collected-data.mean" ] || false
    [ -f "$stat_root/exp2/collected-data.mean" ] || false

    ls -alh "$stat_root/collated/"
    [ -f "$stat_root/collated/exp0-collected-data-collected_food.csv" ] || false
    [ -f "$stat_root/collated/exp1-collected-data-collected_food.csv" ] || false
    [ -f "$stat_root/collated/exp2-collected-data-collected_food.csv" ] || false

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 4 outputs what it is supposed to
################################################################################
stage4_outputs_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x1\",\"foraging.footbot_foraging\", \"template\"))")

    graph_root=$batch_root/graphs
    stat_root=$batch_root/statistics
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 3 4"

    $SIERRA_CMD

    # Check SIERRA directory structure
    [ -d "$graph_root/exp0" ] || false
    [ -d "$graph_root/exp1" ] || false
    [ -d "$graph_root/exp2" ] || false
    [ -d "$graph_root/collated" ] || false

    # Check stage4 generated .csvs
    [ -f "$stat_root/collated/food-counts.mean" ] || false
    [ -f "$stat_root/collated/robot-counts-resting.mean" ] || false
    [ -f "$stat_root/collated/robot-counts-walking.mean" ] || false
    [ -f "$stat_root/collated/swarm-energy.mean" ] || false

    # Check stage4 generated graphs
    [ -f "$graph_root/exp0/SLN-food-counts.png" ] || false
    [ -f "$graph_root/exp0/SLN-robot-counts.png" ] || false
    [ -f "$graph_root/exp0/SLN-swarm-energy.png" ] || false

    [ -f "$graph_root/exp1/SLN-food-counts.png" ] || false
    [ -f "$graph_root/exp1/SLN-robot-counts.png" ] || false
    [ -f "$graph_root/exp1/SLN-swarm-energy.png" ] || false

    [ -f "$graph_root/exp2/SLN-food-counts.png" ] || false
    [ -f "$graph_root/exp2/SLN-robot-counts.png" ] || false
    [ -f "$graph_root/exp2/SLN-swarm-energy.png" ] || false

    [ -f "$graph_root/collated/SLN-food-counts.png" ] || false
    [ -f "$graph_root/collated/SLN-robot-counts-walking.png" ] || false
    [ -f "$graph_root/collated/SLN-robot-counts-resting.png" ] || false
    [ -f "$graph_root/collated/SLN-swarm-energy.png" ] || false

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

options=$(getopt -o f:,e: --long func:,env:  -n "ARGoS integration tests" -- "$@")

eval set -- "$options"
func=NONE
exec_env=''

while true; do

    case "$1" in
        -f|--func) func=$2; shift;;
        -e|--env) exec_env=$2; shift;;
        --) break;;
        *) break;;
    esac
    shift;
done

$func $exec_env

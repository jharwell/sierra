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
     --debug=debug\
     $(which sierra-cli)"

    export SIERRA_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.argos \
       --project=argos_project \
       --exp-setup=exp_setup.T5000.K5 \
       --n-runs=4 \
       --exec-strict \
       --template-input-file=$SAMPLE_ROOT/exp/argos/template.argos \
       --scenario=LowBlockCount.10x10x2 \
       --with-robot-leds \
       --with-robot-rab\
       --exec-no-devnull \
       --log-level=TRACE"

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
        --controller=foraging.footbot_foraging \
        --batch-criteria population_size.Linear3.C3\
        --physics-n-engines=$n"

        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --pipeline 1 2

        rm -rf $SIERRA_ROOT
    done

    SIERRA_CMD="$SIERRA_BASE_CMD \
        --controller=foraging.footbot_foraging \
        --batch-criteria population_size.Linear3.C3\
        --physics-n-engines=1 \
        --physics-spatial-hash2D"

    $SIERRA_CMD --pipeline 1 2

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that the batch criteria that come with SIERRA for ARGoS work.
################################################################################
batch_criteria_test() {
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3"

    sanity_check_pipeline $SIERRA_CMD

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --batch-criteria population_size.Log8"

    sanity_check_pipeline $SIERRA_CMD

    # Can't check constant/variable density beyond stage 1--requires
    # changing arena size and also the positions of lights in the
    # sample project :-(.
    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --batch-criteria population_constant_density.CD1p0.I4.C4 \
    --pipeline 1"

    rm -rf $SIERRA_ROOT
    $SIERRA_CMD

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
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
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x2\",\"foraging.footbot_foraging\", \"template\"))")

    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
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
            [ -f "$input_root/exp${exp}/template_run${run}.argos" ] || false
        done
    done

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 2 outputs what it is supposed to
################################################################################
stage2_outputs_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x2\",\"foraging.footbot_foraging\", \"template\"))")

    output_root=$batch_root/exp-outputs/

    export SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
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
    for exp in {0..2}; do
        for run in {0..3}; do
            [ -d "$output_root/exp${exp}/template_${run}_output" ] || false
        done
    done

    # Check stage2 generated data
    for exp in {0..2}; do
        for run in {0..3}; do
            [ -f "$output_root/exp${exp}/template_${run}_output/output/collected-data.csv" ] || false
        done
    done
}

################################################################################
# Check that stage 3 outputs what it is supposed to
################################################################################
stage3_outputs_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x2\",\"foraging.footbot_foraging\", \"template\"))")

    stat_root=$batch_root/statistics
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 3"

    NONE=(mean)
    CONF95=(mean stddev)
    BW=(mean median whishi whislo q1 q3 cilo cihi)

    $SIERRA_CMD --dist-stats=none
    stage3_check_outputs $batch_root "${NONE[@]}"
    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=conf95
    stage3_check_outputs $batch_root "${CONF95[@]}"
    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=bw
    stage3_check_outputs $batch_root "${BW[@]}"
    rm -rf $SIERRA_ROOT
}

stage3_check_outputs() {
    batch_root="$1"
    stat_root=$batch_root/statistics
    shift
    to_check=("$@")

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$stat_root/exp${i}" ] || false
    done
    [ -d "$stat_root/collated" ] || false

    # Check stage3 generated statistics
    for stat in "${to_check[@]}"; do
        [ -f "$stat_root/collated/exp${i}-collected-data-collected_food.csv" ] || false
        for i in {0..2}; do
            [ -f "$stat_root/exp${i}/collected-data.${stat}" ] || false
        done
    done
}

################################################################################
# Check that stage 4 outputs what it is supposed to
################################################################################
stage4_outputs_test() {
    rm -rf $SIERRA_ROOT

    criteria=(population_size.Linear3.C3
              population_variable_density.1p0.4p0.C4)
    NONE=(mean)
    CONF95=(mean stddev)
    BW=(mean median whishi whislo q1 q3 cilo cihi)

    for bc in "${criteria[@]}"; do
        SIERRA_CMD="$SIERRA_BASE_CMD \
        --controller=foraging.footbot_foraging \
        --physics-n-engines=1 \
        --batch-criteria ${bc}\
        --pipeline 1 2 3 4"

        batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"${bc}\"],\"LowBlockCount.10x10x2\",\"foraging.footbot_foraging\", \"template\"))")

        graph_root=$batch_root/graphs

        $SIERRA_CMD --dist-stats=none
        stage4_check_outputs $batch_root "${NONE[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=conf95
        stage4_check_outputs $batch_root "${CONF95[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=bw
        stage4_check_outputs $batch_root "${BW[@]}"
        rm -rf $SIERRA_ROOT
    done
}

stage4_check_outputs() {
    batch_root="$1"
    graph_root=$batch_root/graphs
    stat_root=$batch_root/statistics
    shift
    to_check=("$@")

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$graph_root/exp${i}" ] || false
    done
    [ -d "$graph_root/collated" ] || false

    for stat in "${to_check[@]}"; do
        # Check stage4 generated .csvs
        [ -f "$stat_root/collated/food-counts.${stat}" ] || false
        [ -f "$stat_root/collated/robot-counts-resting.${stat}" ] || false
        [ -f "$stat_root/collated/robot-counts-walking.${stat}" ] || false
        [ -f "$stat_root/collated/swarm-energy.${stat}" ] || false
    done

    # Check stage4 generated graphs
    for i in {0..2}; do
        [ -f "$graph_root/exp${i}/SLN-food-counts.png" ] || false
        [ -f "$graph_root/exp${i}/SLN-robot-counts.png" ] || false
        [ -f "$graph_root/exp${i}/SLN-swarm-energy.png" ] || false
    done

    [ -f "$graph_root/collated/SLN-food-counts.png" ] || false
    [ -f "$graph_root/collated/SLN-robot-counts-walking.png" ] || false
    [ -f "$graph_root/collated/SLN-robot-counts-resting.png" ] || false
    [ -f "$graph_root/collated/SLN-swarm-energy.png" ] || false
}

################################################################################
# Check that stage 5 outputs what it is supposed to
################################################################################
stage5_outputs_test() {
    rm -rf $SIERRA_ROOT

    criteria=(population_size.Linear3.C3)

    controllers=(foraging.footbot_foraging
                 foraging.footbot_foraging_slow)

    # Run experiments with both controllers
    for bc in "${criteria[@]}"; do
        for c in "${controllers[@]}"; do
            SIERRA_CMD="$SIERRA_BASE_CMD \
            --controller ${c}
            --physics-n-engines=1 \
            --batch-criteria ${bc}\
            --pipeline 1 2 3 4"

            $SIERRA_CMD
        done
    done

    # Compare the controllers
    export SIERRA_STAGE5_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --project=argos_project \
       --pipeline 5 \
       --n-runs=4 \
       --bc-univar \
       --log-level=TRACE"

    SIERRA_STAGE5_CMD="$SIERRA_STAGE5_BASE_CMD \
       --batch-criteria population_size.Linear3.C3 \
       --controller-comparison \
       --controllers-list=foraging.footbot_foraging,foraging.footbot_foraging_slow"

    $SIERRA_STAGE5_CMD

    stage5_check_cc_outputs ${criteria[0]}
}

stage5_check_cc_outputs() {
    batch_criteria=$1

    cc_csv_root=$SIERRA_ROOT/argos_project/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-csvs
    cc_graph_root=$SIERRA_ROOT/argos_project/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-graphs

    # The sample project should generate 2 csvs and 2 graphs
    [[ "$(ls $cc_csv_root | wc -l)" -eq "2" ]] || false
    [[ "$(ls $cc_graph_root | wc -l)" -eq "2" ]] || false
}

################################################################################
# Visual capture test
################################################################################
vc_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x2\",\"foraging.footbot_foraging\", \"template\"))")

    output_root=$batch_root/exp-outputs
    video_root=$batch_root/videos
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --controller=foraging.footbot_foraging \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 3 4 \
    --platform-vc \
    --exp-setup=exp_setup.T500"

    cameras=(overhead
             sw
             sw+interp)

    for c in "${cameras[@]}"; do
        $SIERRA_CMD --camera-config=${c}

        # Check SIERRA directory structure
        for i in {0..2}; do
            [ -d "$output_root/exp${i}/template_${i}_output/frames" ] || false
        done

        # Check generated frames exist
        for i in {0..2}; do
            [[ $(ls -A $output_root/exp${i}/template_${i}_output/frames) > /dev/null ]]  || false
        done

        # Check generated videos
        for i in {0..2}; do
            [ -f "$video_root/exp${i}/template_${i}_output.mp4" ] || false
        done
        rm -rf $SIERRA_ROOT
    done
}

################################################################################
# Cmdline test
################################################################################
cmdline_test() {
    batch_root=$(python3 -c"import sierra.core.root_dirpath_generator as rdg;print(rdg.gen_batch_root(\"$SIERRA_ROOT\",\"argos_project\",[\"population_size.Linear3.C3\"],\"LowBlockCount.10x10x2\",\"foraging.footbot_foraging\", \"template\"))")

    input_root=$batch_root/exp-inputs
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --controller=foraging.footbot_foraging \
    --batch-criteria population_size.Linear3.C3 \
    --exp-setup=exp_setup.T500"


    $SIERRA_CMD --n-robots=10 --pipeline 1

    for exp in {0..2}; do
        for run in {0..3}; do
            grep "quantity=\"10\"" $input_root/exp${exp}/template_run${run}.argos
        done
    done

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

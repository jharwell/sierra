#!/bin/bash -l

################################################################################
# Setup Environment
################################################################################
setup_env() {
    export SIERRA_ROOT=$HOME/test

    if [ "$GITHUB_ACTIONS" = true ]; then
        export SAMPLE_ROOT=$GITHUB_WORKSPACE/sierra-sample-project
        export ARGOS_INSTALL_PREFIX=/usr/local
    else
        export SAMPLE_ROOT=$HOME/git/thesis/sierra-sample-project
        export ARGOS_INSTALL_PREFIX=/$HOME/.local/
    fi

    # Since this is CI, we want to avoid being surprised by deprecated
    # features, so treat them all as errors.
    # export PYTHONWARNINGS=error

    # Set ARGoS library search path. Must contain both the ARGoS core libraries path
    # AND the sample project library path.
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARGOS_INSTALL_PREFIX/lib/argos3
    export ARGOS_PLUGIN_PATH=$ARGOS_INSTALL_PREFIX/lib/argos3:$SAMPLE_ROOT/argos/build
    export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT:./sierra/plugins/engine

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
       --engine=engine.argos \
       --project=projects.sample_argos \
       --exp-setup=exp_setup.T100.K5 \
       --n-runs=4 \
       -xstrict \
       --expdef-template=$SAMPLE_ROOT/exp/argos/template.argos \
       --scenario=LowBlockCount.10x10x2 \
       -xno-devnull \
       --with-robot-leds \
       --with-robot-rab \
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

    # Semi-hack to avoid running stage 4 on OSX in github actions in
    # order to avoid having to install mactex.
    if [[ ! (("$GITHUB_ACTIONS" = true) && ("$RUNNER_OS" = "macOS")) ]]; then
        $SIERRA_CMD --pipeline 4
    fi

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that you can use multiple physics engines and things don't
# crash.
################################################################################
physics_engines_test() {

    # Don't test with ALL engine sizes, just the smallest, largest,
    # and one in between.
    #
    # All: 1 2 4 6 8 12 16 24
    ENGINES=(1 16 24)

    for n in "${ENGINES[@]}"
    do
        SIERRA_CMD="$SIERRA_BASE_CMD \
        --controller=foraging.footbot_foraging \
        --batch-criteria population_size.Linear3.C3\
        --physics-n-engines=${n}"

        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --pipeline 1 2

        rm -rf $SIERRA_ROOT
    done
}

################################################################################
# Check that stage 1 outputs what it is supposed to
################################################################################
stage1_univar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"
    batch_root=$(python3 -c "${batch_root_cmd}")

    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria population_size.Linear3.C3 \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --pipeline 1 "

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$input_root/c1-exp${i}" ] || false
    done

    # Check stage1 generated stuff
    for i in {0..2}; do
        [ -f "$input_root/c1-exp${i}/commands.txt" ] || false
        [ -f "$input_root/c1-exp${i}/exp_def.pkl" ] || false
        [ -f "$input_root/c1-exp${i}/seeds.pkl" ] || false

        for run in {0..3}; do
            [ -f "$input_root/c1-exp${i}/template_run${run}.argos" ] ||false
        done
    done

    rm -rf $SIERRA_ROOT
}



################################################################################
# Check that stage 2 outputs what it is supposed to
################################################################################
stage2_univar_test() {
        batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    output_root=$batch_root/exp-outputs/
    scratch_root=$batch_root/scratch/

    export SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2 "

    env=$1

    rm -rf $SIERRA_ROOT

    if [ "$env" = "hpc.local" ]; then
        $SIERRA_CMD --exec-env=hpc.local
        stage2_univar_check_outputs $batch_root

        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --exec-env=hpc.local --exec-devnull
        stage2_univar_check_outputs $batch_root

        # Check ARGoS produced no output
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
        stage2_univar_check_outputs $batch_root

        rm -rf $SIERRA_ROOT

    elif [ "$env" = "hpc.slurm" ]; then
        sbatch --wait -v --export=ALL ./scripts/slurm-test.sh
        stage2_univar_check_outputs $batch_root
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

stage2_univar_check_outputs() {
    output_root=$1/exp-outputs

    # Check SIERRA directory structure
    for i in {0..2}; do
        for run in {0..3}; do
            [ -d "$output_root/c1-exp${i}/template_run${run}_output" ] || false
        done
    done

    # Check stage2 generated data
    for i in {0..2}; do
        for run in {0..3}; do
            [ -f "$output_root/c1-exp${i}/template_run${run}_output/output/collected-data.csv" ] || false
        done
    done
}


################################################################################
# Check that stage 3 outputs what it is supposed to
################################################################################
stage3_univar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"
    batch_root=$(python3 -c"${batch_root_cmd}")

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
    stage3_univar_check_outputs $batch_root "${NONE[@]}"
    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=conf95
    stage3_univar_check_outputs $batch_root "${CONF95[@]}"
    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=bw
    stage3_univar_check_outputs $batch_root "${BW[@]}"
    rm -rf $SIERRA_ROOT
}

stage3_univar_check_outputs() {
    batch_root="$1"
    stat_root=$batch_root/statistics
    shift
    to_check=("$@")

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$stat_root/c1-exp${i}" ] || false
    done
    [ -d "$stat_root/collated" ] || false

    # Check stage3 generated statistics
    for stat in "${to_check[@]}"; do
        [ -f "$stat_root/collated/c1-exp${i}/collected-data-collected_food.csv" ] || false
        for i in {0..2}; do
            [ -f "$stat_root/c1-exp${i}/collected-data.${stat}" ] || false
        done
    done
}


################################################################################
# Check that stage 4 outputs what it is supposed to
################################################################################
stage4_univar_test() {
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
        batch_root_cmd="from sierra.core import batchroot;
bc=[\"${bc}\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"
        batch_root=$(python3 -c"${batch_root_cmd}")

        graph_root=$batch_root/graphs

        $SIERRA_CMD --dist-stats=none
        stage4_univar_check_outputs $batch_root "${NONE[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=conf95
        stage4_univar_check_outputs $batch_root "${CONF95[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=bw
        stage4_univar_check_outputs $batch_root "${BW[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=all
        stage4_univar_check_outputs $batch_root "${BW[@]}" "${CONF95[@]}"
        rm -rf $SIERRA_ROOT
    done
}

stage4_univar_check_outputs() {
    batch_root="$1"
    graph_root=$batch_root/graphs
    stat_root=$batch_root/statistics
    shift
    to_check=("$@")

    # Check SIERRA directory structure
    for i in {0..2}; do
        [ -d "$graph_root/c1-exp${i}" ] || false
    done
    [ -d "$graph_root/collated" ] || false

    # Check stage4 generated .csvs
    for stat in "${to_check[@]}"; do
        [ -f "$stat_root/collated/food-counts.${stat}" ] || false
        [ -f "$stat_root/collated/robot-counts-resting.${stat}" ] || false
        [ -f "$stat_root/collated/robot-counts-walking.${stat}" ] || false
        [ -f "$stat_root/collated/swarm-energy.${stat}" ] || false
    done

    # Check stage4 generated graphs
    for i in {0..2}; do
        [ -f "$graph_root/c1-exp${i}/SLN-food-counts.png" ] || false
        [ -f "$graph_root/c1-exp${i}/SLN-robot-counts.png" ] || false
        [ -f "$graph_root/c1-exp${i}/SLN-swarm-energy.png" ] || false
    done

    [ -f "$graph_root/collated/SLN-food-counts.png" ] || false
    [ -f "$graph_root/collated/SLN-robot-counts-walking.png" ] || false
    [ -f "$graph_root/collated/SLN-robot-counts-resting.png" ] || false
    [ -f "$graph_root/collated/SLN-swarm-energy.png" ] || false
}


################################################################################
# Visual capture test
################################################################################
vc_test() {
        batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear1.C1\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    output_root=$batch_root/exp-outputs
    video_root=$batch_root/videos
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --controller=foraging.footbot_foraging \
    --batch-criteria population_size.Linear1.C1 \
    --pipeline 1 2 3 4 \
    --prod prod.render \
    --engine-vc"

    cameras=(overhead
             sw
             sw+interp)

    for c in "${cameras[@]}"; do
        $SIERRA_CMD --camera-config=${c}

        # Check SIERRA directory structure
        for i in {0..3}; do
            [ -d "$output_root/c1-exp0/template_run${i}_output/frames" ] || false
        done

        # Check generated frames exist
        for i in {0..3}; do
            [[ $(ls -A $output_root/c1-exp0/template_run${i}_output/frames 2> /dev/null) ]]  || false
        done

        # Check generated videos
        for i in {0..3}; do
            [ -f "$video_root/c1-exp0/template_run${i}_output.mp4" ] || false
        done
        rm -rf $SIERRA_ROOT
    done
}
################################################################################
# Imagize test
################################################################################
imagize_test() {
        batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear1.C1\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    output_root=$batch_root/exp-outputs
    video_root=$batch_root/videos
    imagize_root=$batch_root/imagize
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --controller=foraging.footbot_foraging \
    --batch-criteria population_size.Linear1.C1 \
    --pipeline 1 2 3 4 \
    --proc proc.statistics proc.imagize \
    --prod prod.render \
    --project-rendering \
    --exp-setup=exp_setup.T100.K10"

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..3}; do
        [ -d "$output_root/c1-exp0/template_run${i}_output/output/floor-state" ] || false
    done

    # Check generated images exist
    [[ $(ls -A $imagize_root/c1-exp0/floor-state/*.png) > /dev/null ]]  || false

    # Check generated videos
    [ -f "$video_root/c1-exp0/floor-state/floor-state.mp4" ] || false
    rm -rf $SIERRA_ROOT
}

################################################################################
# Cmdline test
################################################################################
cmdline_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    input_root=$batch_root/exp-inputs
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --physics-n-engines=1 \
    --controller=foraging.footbot_foraging \
    --batch-criteria population_size.Linear3.C3"


    $SIERRA_CMD --n-agents=10 --pipeline 1

    for i in {0..2}; do
        for run in {0..3}; do
            grep "quantity=\"10\"" $input_root/c1-exp${i}/template_run${run}.argos
        done
    done
    rm -rf $SIERRA_ROOT
}

################################################################################
# Run Tests
################################################################################

# Exit anytime SIERRA crashes or a command fails
set -e

# Echo cmds to stdout
set -x

setup_env

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

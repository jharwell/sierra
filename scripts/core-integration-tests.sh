#!/bin/bash -l
#
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
        export ARGOS_INSTALL_PREFIX=/$HOME/.local

    fi

    # Since this is CI, we want to avoid being surprised by deprecated
    # features, so treat them all as errors.
    # export PYTHONWARNINGS=error

    # Set ARGoS library search path. Must contain both the ARGoS core libraries path
    # AND the sample project library path.
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARGOS_INSTALL_PREFIX/lib/argos3
    export ARGOS_PLUGIN_PATH=$ARGOS_INSTALL_PREFIX/lib/argos3:$SAMPLE_ROOT/argos/build
    export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT

    # Required to get coverage.py to work with the installed version
    # of SIERRA. Omitting this results in either nothing getting
    # measured because the local site-packages is omitted, or if that
    # is included ALL locally installed packages get measured.
    export PYTHONPATH=$PYTHONPATH:$PWD

    which sierra-cli
    which python3

    echo ":" >> /tmp/nodefile
    export SIERRA_NODEFILE=/tmp/nodefile

    rm -rf ~/.sierrarc

    export COVERAGE_CMD="coverage \
    run \
     --debug=debug \
     $(which sierra-cli)"

    export SIERRA_BASE_CMD_ARGOS="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --controller=foraging.footbot_foraging \
       --engine=engine.argos \
       --project=projects.sample_argos \
       --exp-setup=exp_setup.T50.K5 \
       --n-runs=4 \
       -xstrict \
       --expdef-template=$SAMPLE_ROOT/exp/argos/template.argos \
       --scenario=LowBlockCount.10x10x2 \
       -xno-devnull \
       --with-robot-leds \
       --with-robot-rab\
       --log-level=TRACE"

    export SIERRA_BASE_CMD_JSONSIM="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --controller=default.default \
       --engine=plugins.jsonsim \
       --project=projects.sample_jsonsim \
       --jsonsim-path=$SAMPLE_ROOT/plugins/jsonsim/jsonsim.py \
       --exp-setup=exp_setup.T50.K5 \
       --n-runs=4 \
       --expdef=expdef.json \
       --expdef-template=$SAMPLE_ROOT/exp/jsonsim/template.json \
       --scenario=scenario1.10x10x10 \
       --log-level=TRACE"

    export PARALLEL="--env LD_LIBRARY_PATH"
}

################################################################################
# Check usage of environment variables
################################################################################
env_vars_test() {
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

    # Test SIERRA_ARCH
    export SIERRA_ARCH=fizzbuzz

    which argos3

    ln -sfn /usr/local/bin/argos3 /usr/local/bin/argos3-fizzbuzz

    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
    --physics-n-engines=1 \
    --batch-criteria population_size.Linear3.C3 \
    --pipeline 1 2"

    $SIERRA_CMD

    rm -rf $SIERRA_ROOT
}
################################################################################
# Check usage of builtin batch criteria
################################################################################
builtin_bc_test() {
        batch_root_cmd="from sierra.core import batchroot;
bc=[\"builtin.MonteCarlo.C5\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_jsonsim\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")
    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD_JSONSIM \
                    --batch-criteria builtin.MonteCarlo.C5"
    $SIERRA_CMD --pipeline 1

    # Check SIERRA directory structure
    for i in {0..4}; do
        [ -d "$input_root/c1-exp${i}" ] || false
    done

    $SIERRA_CMD --pipeline 2 3 4
    rm -rf $SIERRA_ROOT
}

################################################################################
# Check cmdline options
################################################################################
cmdline_opts_test() {
    # Check plotting opts
    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
                    --physics-n-engines=1 \
                    --batch-criteria population_size.Linear3.C3"

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --pipeline 1 2 3 --processing-parallelism=1

    $SIERRA_CMD --pipeline 4 --plot-log-xscale
    $SIERRA_CMD --pipeline 4 --plot-enumerated-xscale
    $SIERRA_CMD --pipeline 4 --plot-log-yscale --processing-parallelism=1
    $SIERRA_CMD --pipeline 4 --plot-large-text

    rm -rf $SIERRA_ROOT

    # Check version
    $SIERRA_CMD --version

    # Check rcfile
    rm -rf $HOME/test2
    rm -rf $HOME/test3

    echo "--sierra-root=~/test2" > /tmp/tmpfile
    $SIERRA_CMD --rcfile=/tmp/tmpfile
    [ -d "$HOME/test2/" ] || false

    rm -rf $HOME/test2

    echo "--sierra-root $HOME/test3" > /tmp/tmpfile2
    $SIERRA_CMD --rcfile=/tmp/tmpfile2
    [ -d "$HOME/test3/" ] || false

    rm -rf $HOME/test3

    export SIERRA_RCFILE=/tmp/tmpfile2
    $SIERRA_CMD
    [ -d "$HOME/test3/" ] || false

    rm -rf $HOME/test3

    export -n SIERRA_RCFILE
    mv /tmp/tmpfile2 ~/.sierrarc
    $SIERRA_CMD
    [ -d "$HOME/test3/" ] || false

    rm -rf $HOME/test3

}

stage5_univar_test() {
    rm -rf $SIERRA_ROOT

    criteria=(population_size.Linear3.C3)

    controllers=(foraging.footbot_foraging
                 foraging.footbot_foraging_slow)

    STATS=(none conf95 bw)


    # Add some extra plotting options to test--these should be pulled
    # out of here and into a python class once everything is converted
    # from bash -> python
    export SIERRA_STAGE5_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --project=projects.sample_argos \
       --pipeline 5 \
       --n-runs=4 \
       --bc-univar \
       -plog-yscale \
       -plarge-text \
       -pprimary-axis=1 \
       --log-level=TRACE"

    # Run experiments with both controllers
    for bc in "${criteria[@]}"; do
        for c in "${controllers[@]}"; do
            SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
            --controller ${c}
            --physics-n-engines=1 \
            --batch-criteria ${bc}\
            --pipeline 1 2 3 4 --dist-stats=all"

            $SIERRA_CMD --scenario=HighBlockCount.10x10x2
        done
    done

    # Compare the controllers within the same scenario
    for stat in "${STATS[@]}"; do

        SIERRA_STAGE5_CMD="$SIERRA_STAGE5_BASE_CMD \
        --batch-criteria population_size.Linear3.C3 \
        --controller-comparison \
        --dist-stats=${stat} \
        --controllers-list=foraging.footbot_foraging,foraging.footbot_foraging_slow"

        $SIERRA_STAGE5_CMD

        stage5_univar_check_cc_outputs ${criteria[0]}
    done

    # Run more experiments with both controllers for scenario
    # comparison. This CANNOT be part of the block above, because for
    # controller comparison, having the selected controllers be run on
    # multiple scenarios results in ambiguity and errors.
    for bc in "${criteria[@]}"; do
        for c in "${controllers[@]}"; do
            SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
            --controller ${c}
            --physics-n-engines=1 \
            --batch-criteria ${bc}\
            --pipeline 1 2 3 4 --dist-stats=all"

            $SIERRA_CMD --scenario=LowBlockCount.10x10x2
        done
    done

    # Compare the controller across scenarios
    for stat in "${STATS[@]}"; do

        SIERRA_STAGE5_CMD="$SIERRA_STAGE5_BASE_CMD \
       --batch-criteria population_size.Linear3.C3 \
       --scenario-comparison \
       --controller=foraging.footbot_foraging\
       --dist-stats=${stat} \
       --scenarios-list=LowBlockCount.10x10x2,HighBlockCount.10x10x2"

        $SIERRA_STAGE5_CMD

        stage5_univar_check_sc_outputs ${criteria[0]}
    done

    # rm -rf $SIERRA_ROOT
}

stage5_univar_check_cc_outputs() {
    batch_criteria=$1

    cc_csv_root=$SIERRA_ROOT/projects.sample_argos/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-csvs
    cc_graph_root=$SIERRA_ROOT/projects.sample_argos/foraging.footbot_foraging+foraging.footbot_foraging_slow-cc-graphs

    # The sample project should generate 18 csvs (1 mean + 1 stddev +
    # 7 bw stats per controller ) and 2 graphs
    [[ "$(ls $cc_csv_root | wc -l)" -eq "18" ]] || false
    [[ "$(ls $cc_graph_root | wc -l)" -eq "2" ]] || false
}

stage5_univar_check_sc_outputs() {
    batch_criteria=$1

    sc_csv_root=$SIERRA_ROOT/projects.sample_argos/LowBlockCount.10x10x2+HighBlockCount.10x10x2-sc-csvs
    sc_graph_root=$SIERRA_ROOT/projects.sample_argos/LowBlockCount.10x10x2+HighBlockCount.10x10x2-sc-graphs
    # The sample project should generate 18 csvs (1 mean + 1 stddev +
    # 7 bw stats per controller ) and 2 graphs
    [[ "$(ls $sc_csv_root | wc -l)" -eq "18" ]] || false
    [[ "$(ls $sc_graph_root | wc -l)" -eq "2" ]] || false
}

################################################################################
# Bivariate Tests
################################################################################
stage1_bivar_test() {
    batch_root_cmd1="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\",\"max_speed.1.9.C5\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"
    batch_root_cmd2="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\",\"population_size.Linear3.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"

    batch_root1=$(python3 -c "${batch_root_cmd1}")

    input_root1=$batch_root1/exp-inputs/

    batch_root2=$(python3 -c"${batch_root_cmd2}")

    input_root2=$batch_root2/exp-inputs/

    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
    --batch-criteria population_size.Linear3.C3 max_speed.1.9.C5\
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
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
        [ $(grep -r "max_speed=\"1.0\"" $input_root1/c1-exp${i}+* | wc -l) -eq "5" ]
        for j in {0..4}; do
            [ -f "$input_root1/c1-exp${i}+c2-exp${j}/commands.txt" ] || false
            [ -f "$input_root1/c1-exp${i}+c2-exp${j}/exp_def.pkl" ] || false
            [ -f "$input_root1/c1-exp${i}+c2-exp${j}/seeds.pkl" ] || false
            for run in {0..3}; do
                [ -f "$input_root1/c1-exp${i}+c2-exp${j}/template_run${run}.argos" ] ||false
            done
        done
    done

    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
    --batch-criteria max_speed.1.9.C5 population_size.Linear3.C3\
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
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
            [ $(grep -r "max_speed=\"1.0\"" $input_root2/*+c2-exp${j} | wc -l) -eq "5" ]

            [ -f "$input_root2/c1-exp${i}+c2-exp${j}/commands.txt" ] || false
            [ -f "$input_root2/c1-exp${i}+c2-exp${j}/exp_def.pkl" ] || false
            [ -f "$input_root2/c1-exp${i}+c2-exp${j}/seeds.pkl" ] || false

            for run in {0..3}; do
                [ -f "$input_root2/c1-exp${i}+c2-exp${j}/template_run${run}.argos" ] ||false
            done
        done
    done

    rm -rf $SIERRA_ROOT
}

stage2_bivar_test() {
    batch_root_cmd1="from sierra.core import batchroot;
bc=[\"population_size.Linear2.C2\", \"max_speed.1.9.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"
    batch_root1=$(python3 -c"${batch_root_cmd1}")

    output_root1=$batch_root1/exp-outputs/

    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
    --controller=foraging.footbot_foraging \
    --batch-criteria population_size.Linear2.C2 max_speed.1.9.C3\
    --physics-n-engines=1 \
    --pipeline 1 2"

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..1}; do
        for j in {0..2}; do
            [ -d "$output_root1/c1-exp${i}+c2-exp${j}" ] || false
        done
    done

    # Check stage2 generated stuff
    for i in {0..1}; do
        for j in {0..2}; do
            for run in {0..3}; do
                [ -f "$output_root1/c1-exp${i}+c2-exp${j}/template_run${run}_output/output/collected-data.csv" ] ||false
            done
        done
    done
}

stage3_bivar_test() {
    batch_root_cmd1="from sierra.core import batchroot;
bc=[\"population_size.Linear2.C2\", \"max_speed.1.9.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd1}")

    output_root=$batch_root1/exp-outputs/

    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
    --batch-criteria population_size.Linear2.C2 max_speed.1.9.C3\
    --controller=foraging.footbot_foraging \
    --physics-n-engines=1 \
    --pipeline 1 2 3"

    NONE=(mean)
    CONF95=(mean stddev)
    BW=(mean median whishi whislo q1 q3 cilo cihi)

    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=none
    stage3_bivar_check_outputs $batch_root "${NONE[@]}"
    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=conf95
    stage3_bivar_check_outputs $batch_root "${CONF95[@]}"
    rm -rf $SIERRA_ROOT

    $SIERRA_CMD --dist-stats=bw
    stage3_bivar_check_outputs $batch_root "${BW[@]}"
    rm -rf $SIERRA_ROOT
}

stage3_bivar_check_outputs() {
    batch_root="$1"
    stat_root=$batch_root/statistics
    shift
    to_check=("$@")

    # Check SIERRA directory structure
    for i in {0..1}; do
        for j in {0..2}; do
            [ -d "$stat_root/c1-exp${i}+c2-exp${j}" ] || false
        done
    done
    [ -d "$stat_root/collated" ] || false

    # Check stage3 generated statistics
    for stat in "${to_check[@]}"; do
        for i in {0..1}; do
            for j in {0..2}; do
                [ -f "$stat_root/c1-exp${i}+c2-exp${j}/collected-data.${stat}" ] || false
                [ -f "$stat_root/collated/c1-exp${i}+c2-exp${j}/collected-data-collected_food.csv" ] || false

            done
        done
    done
}

stage4_bivar_test() {
    rm -rf $SIERRA_ROOT

    criteria=()
    NONE=(mean)
    CONF95=(mean stddev)
    BW=(mean median whishi whislo q1 q3 cilo cihi)

    SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
        --controller=foraging.footbot_foraging2 \
        --physics-n-engines=1 \
        --batch-criteria population_size.Linear3.C3 max_speed.1.9.C3 \
        --pipeline 1 2 3 4"
        batch_root_cmd="from sierra.core import batchroot;
bc=[\"population_size.Linear3.C3\", \"max_speed.1.9.C3\"];
template_stem=\"template\";
scenario=\"LowBlockCount.10x10x2\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_argos\",controller=\"foraging.footbot_foraging2\",leaf=leaf).to_path();
print(path)
"
        batch_root=$(python3 -c"${batch_root_cmd}")

        graph_root=$batch_root/graphs

        $SIERRA_CMD --dist-stats=none
        stage4_bivar_check_outputs $batch_root "${NONE[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=conf95
        stage4_bivar_check_outputs $batch_root "${CONF95[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=bw
        stage4_bivar_check_outputs $batch_root "${BW[@]}"
        rm -rf $SIERRA_ROOT

        $SIERRA_CMD --dist-stats=all
        stage4_bivar_check_outputs $batch_root "${BW[@]}" "${CONF95[@]}"
        rm -rf $SIERRA_ROOT
}

stage4_bivar_check_outputs() {
    batch_root="$1"
    graph_root=$batch_root/graphs
    stat_root=$batch_root/statistics
    shift
    to_check=("$@")

    # Check SIERRA directory structure
    for i in {0..2}; do
        for j in {0..2}; do
            [ -d "$graph_root/c1-exp${i}+c2-exp${j}" ] || false
        done
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
        for j in {0..2}; do
        [ -f "$graph_root/c1-exp${i}+c2-exp${j}/SLN-food-counts.png" ] || false
        [ -f "$graph_root/c1-exp${i}+c2-exp${j}/SLN-robot-counts.png" ] || false
        [ -f "$graph_root/c1-exp${i}+c2-exp${j}/SLN-swarm-energy.png" ] || false
        done
    done

    [ -f "$graph_root/collated/HM-food-counts2.png" ] || false
    [ -f "$graph_root/collated/HM-robot-counts-walking2.png" ] || false
    [ -f "$graph_root/collated/HM-robot-counts-resting2.png" ] || false
    [ -f "$graph_root/collated/HM-swarm-energy2.png" ] || false
}

stage5_bivar_test() {
    rm -rf $SIERRA_ROOT

    controllers=(foraging.footbot_foraging2
                 foraging.footbot_foraging_slow2)

    # Run experiments with both controllers
    for c in "${controllers[@]}"; do
        SIERRA_CMD="$SIERRA_BASE_CMD_ARGOS \
        --controller ${c} \
        --bc-rendering \
        --physics-n-engines=1 \
        --batch-criteria population_size.Linear3.C3 max_speed.1.9.C5\
        --pipeline  1 2 3 4"

        $SIERRA_CMD
    done

    # Compare the controllers
    export SIERRA_STAGE5_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --project=projects.sample_argos \
       --pipeline 5 \
       --n-runs=4 \
       --bc-bivar \
       --log-level=TRACE"

    # 2 -> 1 graph per controller, 2 performance variables
    N_FILES=(2)
    COMPS=(LNraw)

    for i in {0..0}; do
        SIERRA_STAGE5_CMD="$SIERRA_STAGE5_BASE_CMD \
        --batch-criteria population_size.Linear3.C3 max_speed.1.9.C5\
        --controller-comparison \
        --dist-stats=conf95 \
        --comparison-type=${COMPS[${i}]} \
        --plot-log-yscale \
        --plot-large-text \
        --plot-transpose-graphs \
        --controllers-list=foraging.footbot_foraging2,foraging.footbot_foraging_slow2"

        cc_csv_root=$SIERRA_ROOT/projects.sample_argos/foraging.footbot_foraging2+foraging.footbot_foraging_slow2-cc-csvs
        cc_graph_root=$SIERRA_ROOT/projects.sample_argos/foraging.footbot_foraging2+foraging.footbot_foraging_slow2-cc-graphs

        rm -rf $cc_csv_root
        rm -rf $cc_graph_root

        $SIERRA_STAGE5_CMD --plot-primary-axis=0
        stage5_bivar_check_cc_outputs $cc_graph_root ${N_FILES[${i}]}

        rm -rf $cc_csv_root
        rm -rf $cc_graph_root

        $SIERRA_STAGE5_CMD --plot-primary-axis=1
        stage5_bivar_check_cc_outputs $cc_graph_root ${N_FILES[${i}]}
    done
}

stage5_bivar_check_cc_outputs() {
    cc_graph_root=$1
    n_files=$2

    [[ "$(ls $cc_graph_root | wc -l)" -eq "$n_files" ]] || false
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

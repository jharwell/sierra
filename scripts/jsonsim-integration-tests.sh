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

    export COVERAGE_CMD="coverage \
    run \
     --debug=debug \
     $(which sierra-cli)"

    export SIERRA_BASE_CMD="$COVERAGE_CMD \
       --sierra-root=$SIERRA_ROOT \
       --engine=plugins.jsonsim \
       --project=projects.sample_jsonsim \
       --n-runs=4 \
       --expdef=expdef.json \
       --exp-setup=exp_setup.T10 \
       --expdef-template=$SAMPLE_ROOT/exp/jsonsim/template.json \
       --scenario=scenario1.10x10x10 \
       --jsonsim-path=$SAMPLE_ROOT/plugins/jsonsim/jsonsim.py \
       --log-level=TRACE"

}

################################################################################
# Check that stage 1 outputs what it is supposed to
################################################################################
stage1_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_jsonsim\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")
    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=default.default \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 "

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..4}; do
        [ -d "$input_root/c1-exp${i}" ] || false
    done

    # Check stage1 generated stuff
    for i in {0..4}; do
        for run in {0..3}; do
            [ -f "$input_root/c1-exp${i}/commands.txt" ] || false
            [ -f "$input_root/c1-exp${i}/exp_def.pkl" ] || false
            [ -f "$input_root/c1-exp${i}/seeds.pkl" ] || false
            [ -f "$input_root/c1-exp${i}/template_run${run}.json" ] ||false
            grep -v "\-1" "$input_root/c1-exp${i}/template_run${run}.json"
            grep -v "foobar" "$input_root/c1-exp${i}/template_run${run}.json"
        done
    done

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 2 outputs what it is supposed to
################################################################################
stage2_univar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_jsonsim\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")
    output_root=$batch_root/exp-outputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=default.default \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 2"

    $SIERRA_CMD

    # Check stage2 generated stuff
    for i in {0..4}; do
        [ -d "$output_root/c1-exp${i}" ] || false
        for run in {0..3}; do
            [ -d "$output_root/c1-exp${i}/template_run${run}_output/output" ] || false
            [ -f "$output_root/c1-exp${i}/template_run${run}_output/output/output1D.csv" ] || false
            n_cols=$(awk -F\, '{print NF; exit}' "$output_root/c1-exp${run}/template_run${run}_output/output/output1D.csv")
            n_rows=$(wc -l < "$output_root/c1-exp${run}/template_run${run}_output/output/output1D.csv")
            [[ $n_cols == 5 ]] && true || false
            [[ $n_rows == 51 ]] && true || false

            [ -f "$output_root/c1-exp${i}/template_run${run}_output/output/output2D.csv" ] || false
            n_cols=$(awk -F\, '{print NF; exit}' "$output_root/c1-exp${run}/template_run${run}_output/output/output2D.csv")
            n_rows=$(wc -l < "$output_root/c1-exp${i}/template_run${run}_output/output/output2D.csv")
            [[ $n_cols == 3 ]] && true || false
            [[ $n_rows == 49 ]] && true || false

        done
    done

    rm -rf $SIERRA_ROOT
}


################################################################################
# Check that stage 3 outputs what it is supposed to
################################################################################
stage3_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_jsonsim\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    stat_root=$batch_root/statistics/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=default.default \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 2 3"

    $SIERRA_CMD

    # Check stage3 generated stuff
    [ -d "$stat_root/collated" ] || false
    for i in {0..4}; do
        [ -d "$stat_root/c1-exp${i}" ] || false
        [ -f "$stat_root/c1-exp${i}/output1D.mean" ] || false
        [ -f "$stat_root/c1-exp${i}/output2D.mean" ] || false
        [ -f "$stat_root/c1-exp${i}/subdir1/subdir2/output1D.mean" ] || false
        [ -f "$stat_root/c1-exp${i}/subdir1/subdir2/output2D.mean" ] || false
        [ -f "$stat_root/c1-exp${i}/subdir3/output1D.mean" ] || false
        [ -f "$stat_root/c1-exp${i}/subdir3/output2D.mean" ] || false
        n_rows=$(wc -l < "$stat_root/c1-exp${i}/output1D.mean")
        [[ $n_rows == 51 ]] && true || false
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/c1-exp${i}/output1D.mean")
        [[ $n_cols == 5 ]] && true || false

        n_rows=$(wc -l < "$stat_root/c1-exp${i}/output2D.mean")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/c1-exp${i}/output2D.mean")
        [[ $n_rows == 49 ]] && true || false
        [[ $n_cols == 3 ]] && true || false

        n_rows=$(wc -l < "$stat_root/c1-exp${i}/subdir1/subdir2/output1D.mean")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/c1-exp${i}/subdir1/subdir2/output1D.mean")
        [[ $n_rows == 51 ]] && true || false
        [[ $n_cols == 5 ]] && true || false

        n_rows=$(wc -l < "$stat_root/c1-exp${i}/subdir1/subdir2/output2D.mean")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/c1-exp${i}/subdir1/subdir2/output2D.mean")
        [[ $n_rows == 49 ]] && true || false
        [[ $n_cols == 3 ]] && true || false

        n_rows=$(wc -l < "$stat_root/c1-exp${i}/subdir3/output1D.mean")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/c1-exp${i}/subdir3/output1D.mean")
        [[ $n_rows == 51 ]] && true || false
        [[ $n_cols == 5 ]] && true || false

        n_rows=$(wc -l < "$stat_root/c1-exp${i}/subdir3/output2D.mean")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/c1-exp${i}/subdir3/output2D.mean")
        [[ $n_rows == 49 ]] && true || false
        [[ $n_cols == 3 ]] && true || false

        [ -f "$stat_root/collated/c1-exp${i}/subdir1/subdir2/output1D-col1.csv" ] || false
        n_rows=$(wc -l < "$stat_root/collated/c1-exp${i}/subdir1/subdir2/output1D-col1.csv")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/collated/c1-exp${i}/subdir1/subdir2/output1D-col1.csv")
        [[ $n_rows == 51 ]] && true || false
        [[ $n_cols == 4 ]] && true || false

        [ -f "$stat_root/collated/c1-exp${i}/subdir3/output1D-col2.csv" ] || false
        n_rows=$(wc -l < "$stat_root/collated/c1-exp${i}/subdir3/output1D-col2.csv")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/collated/c1-exp${i}/subdir3/output1D-col2.csv")
        [[ $n_rows == 51 ]] && true || false
        [[ $n_cols == 4 ]] && true || false
    done

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 4 outputs what it is supposed to
################################################################################
stage4_univar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_jsonsim\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    graph_root=$batch_root/graphs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=default.default \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 2 3 4"

    $SIERRA_CMD

    # Check stage4 generated stuff
    [ -d "$graph_root/collated" ] || false
    [ -f "$graph_root/collated/SLN-random-noise-col1.png" ] || false
    [ -f "$graph_root/collated/SLN-random-noise2-col2.png" ] || false
    [ -f "$graph_root/collated/SM-random-noise3-col2.png" ] || false
    for i in {0..4}; do
        [ -f "$graph_root/c1-exp${i}/SLN-random-noise.png" ] || false
        [ -f "$graph_root/c1-exp${i}/SLN-random-noise2.png" ] || false
        [ -f "$graph_root/c1-exp${i}/SLN-random-noise3.png" ] || false
        [ -f "$graph_root/c1-exp${i}/HM-output2D-1.png" ] || false
        [ -f "$graph_root/c1-exp${i}/HM-output2D-2.png" ] || false
    done

    rm -rf $SIERRA_ROOT
}

stage4_bivar_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\", \"fuel.10.100.C4\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"projects.sample_jsonsim\",controller=\"default.default2\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    graph_root=$batch_root/graphs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --controller=default.default2 \
    --batch-criteria max_speed.1.9.C5 fuel.10.100.C4 \
    --pipeline 1 2 3 4"

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..4}; do
        for j in {0..3}; do
            [ -d "$graph_root/c1-exp${i}+c2-exp${j}" ] || false
        done
    done
    [ -d "$graph_root/collated" ] || false

    # Check stage4 collated .csvs
    for stat in "${to_check[@]}"; do
        [ -f "$stat_root/collated/random-noise-col1.${stat}" ] || false
        [ -f "$stat_root/collated/random-noise2-col2.${stat}" ] || false
        [ -f "$stat_root/collated/random-noise3-col2.${stat}" ] || false
    done

    # Check stage4 intra graphs
    for i in {0..4}; do
        for j in {0..3}; do
            [ -f "$graph_root/c1-exp${i}+c2-exp${j}/SLN-random-noise.png" ] || false
            [ -f "$graph_root/c1-exp${i}+c2-exp${j}/SLN-random-noise2.png" ] || false
            [ -f "$graph_root/c1-exp${i}+c2-exp${j}/SLN-random-noise3.png" ] || false
            [ -f "$graph_root/c1-exp${i}+c2-exp${j}/HM-output2D-1.png" ] || false
            [ -f "$graph_root/c1-exp${i}+c2-exp${j}/HM-output2D-2.png" ] || false
        done
    done

    # Check stage4 generated stuff
    [ -d "$graph_root/collated" ] || false
    for i in {0..4}; do
        [ -f "$graph_root/collated/HM-bivar-random-noise-col1.png" ] || false
        [ -f "$graph_root/collated/HM-bivar-random-noise2-col2.png" ] || false
        [ -f "$graph_root/collated/HM-bivar-random-noise3-col2.png" ] || false
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

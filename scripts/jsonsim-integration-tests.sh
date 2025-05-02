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

    export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT/plugins/platform:$SAMPLE_ROOT/projects

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
       --platform=platform.jsonsim \
       --project=jsonsim_project \
       --n-runs=4 \
       --expdef=expdef.json \
       --exp-setup=exp_setup.T10 \
       --expdef-template=$SAMPLE_ROOT/exp/jsonsim/template.json \
       --scenario=scenario1.10x10x10 \
       --controller=default.default \
       --jsonsim-path=$SAMPLE_ROOT/plugins/platform/jsonsim/jsonsim.py \
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
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"jsonsim_project\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")
    input_root=$batch_root/exp-inputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 "

    $SIERRA_CMD

    # Check SIERRA directory structure
    for i in {0..4}; do
        [ -d "$input_root/exp$i" ] || false
    done

    # Check stage1 generated stuff
    for exp in {0..4}; do
        for run in {0..3}; do
            [ -f "$input_root/exp${exp}/commands.txt" ] || false
            [ -f "$input_root/exp${exp}/exp_def.pkl" ] || false
            [ -f "$input_root/exp${exp}/seeds.pkl" ] || false
            [ -f "$input_root/exp${exp}/template_run${run}.json" ] ||false
            grep -v "\-1" "$input_root/exp${exp}/template_run${run}.json"
            grep -v "foobar" "$input_root/exp${exp}/template_run${run}.json"
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
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"jsonsim_project\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")
    output_root=$batch_root/exp-outputs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 2"

    $SIERRA_CMD

    # Check stage2 generated stuff
    for exp in {0..4}; do
        [ -d "$output_root/exp${exp}" ] || false
        for run in {0..3}; do
            [ -d "$output_root/exp${run}/template_run${run}_output/output" ] || false
            [ -f "$output_root/exp${run}/template_run${run}_output/output/output.csv" ] || false
            n_cols=$(awk -F\, '{print NF; exit}' "$output_root/exp${run}/template_run${run}_output/output/output.csv")
            n_rows=$(wc -l < "$output_root/exp${run}/template_run${run}_output/output/output.csv")
            [[ $n_cols == 5 ]] && true || false
            [[ $n_rows == 51 ]] && true || false
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
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"jsonsim_project\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    stat_root=$batch_root/statistics/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 2 3"

    $SIERRA_CMD

    # Check stage3 generated stuff
    [ -d "$stat_root/collated" ] || false
    for exp in {0..4}; do
        [ -d "$stat_root/exp${exp}" ] || false
        [ -f "$stat_root/exp${exp}/output.mean" ] || false
        [ -f "$stat_root/exp${exp}/subdir1/subdir2/output.mean" ] || false
        [ -f "$stat_root/exp${exp}/subdir3/output.mean" ] || false
        n_rows=$(wc -l < "$stat_root/exp${exp}/output.mean")
        [[ $n_rows == 51 ]] && true || false

        n_rows=$(wc -l < "$stat_root/exp${exp}/subdir1/subdir2/output.mean")
        [[ $n_rows == 51 ]] && true || false

        n_rows=$(wc -l < "$stat_root/exp${exp}/subdir3/output.mean")
        [[ $n_rows == 51 ]] && true || false

        [ -f "$stat_root/collated/exp${exp}-output-col1.csv" ] || false
        n_rows=$(wc -l < "$stat_root/collated/exp${exp}-output-col1.csv")
        n_cols=$(awk -F\, '{print NF; exit}' "$stat_root/collated/exp${exp}-output-col1.csv")
        [[ $n_rows == 51 ]] && true || false
        [[ $n_cols == 4 ]] && true || false
    done

    rm -rf $SIERRA_ROOT
}

################################################################################
# Check that stage 4 outputs what it is supposed to
################################################################################
stage4_test() {
    batch_root_cmd="from sierra.core import batchroot;
bc=[\"max_speed.1.9.C5\"];
template_stem=\"template\";
scenario=\"scenario1.10x10x10\";
leaf=batchroot.ExpRootLeaf(bc=bc,template_stem=template_stem,scenario=scenario);
path=batchroot.ExpRoot(sierra_root=\"$SIERRA_ROOT\",project=\"jsonsim_project\",controller=\"default.default\",leaf=leaf).to_path();
print(path)
"

    batch_root=$(python3 -c"${batch_root_cmd}")

    graph_root=$batch_root/graphs/
    rm -rf $SIERRA_ROOT

    SIERRA_CMD="$SIERRA_BASE_CMD \
    --batch-criteria max_speed.1.9.C5 \
    --pipeline 1 2 3 4"

    $SIERRA_CMD

    # Check stage4 generated stuff
    [ -d "$graph_root/collated" ] || false
    for exp in {0..4}; do
        [ -f "$graph_root/collated/SLN-random-noise-col1.png" ] || false
        [ -f "$graph_root/collated/SLN-random-noise2-col2.png" ] || false
        [ -f "$graph_root/collated/SLN-random-noise3-col2.png" ] || false
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

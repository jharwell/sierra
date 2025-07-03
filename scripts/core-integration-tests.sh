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
        [ -d "$input_root/exp$i" ] || false
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

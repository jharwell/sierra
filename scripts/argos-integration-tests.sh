#!/bin/bash -l

################################################################################
# Setup Environment
################################################################################
export SIERRA_ROOT=$HOME/test
export SAMPLE_ROOT=$HOME/work/sierra-sample-project
export ARGOS_INSTALL_PREFIX=/usr/local

# Set ARGoS library search path. Must contain both the ARGoS core libraries path
# AND the sample project library path.
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$ARGOS_INSTALL_PREFIX/lib/argos3
export ARGOS_PLUGIN_PATH=$ARGOS_INSTALL_PREFIX/lib/argos3:$SAMPLE_ROOT/argos/build

export SIERRA_PLUGIN_PATH=$SAMPLE_ROOT/projects

export SIERRA_BASE_CMD="sierra-cli \
       --sierra-root=$SIERRA_ROOT \
       --platform=platform.argos \
       --project=argos_project \
       --exp-setup=exp_setup.T1000.K5 \
       --n-runs=4 \
       --exec-strict \
       --template-input-file=$SAMPLE_ROOT/exp/argos/template.argos \
       --scenario=LowBlockCount.10x10x1 \
       --controller=foraging.footbot_foraging \
       --with-robot-leds \
       --with-robot-rab\
       --exec-no-devnull \
       --log-level=DEBUG"

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

        sanity_check_pipeline $SIERRA_CMD
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
# Run Tests
################################################################################
# Exit anytime SIERRA crashes or a command fails
set -e

# Echo cmds to stdout
set -x

batch_criteria_test
physics_engines_test

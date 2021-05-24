#!/bin/bash -l

################################################################################
# Setup Simulation Environment                                                 #
################################################################################
# Set paths
FORDYCA=$HOME/git/fordyca
SIERRA=$HOME/git/sierra

OUTPUT_ROOT=$HOME/exp/2021-ijcai-demo

cd $SIERRA
TASK="$1"

BASE_CMD="python3 main.py \
        --sierra-root=$OUTPUT_ROOT\
        --template-input-file=$SIERRA/templates/2021-ijcai-demo.argos \
        --project=fordyca\
        --physics-n-engines=1\
        --batch-criteria population_size.Log8\
        --exp-overwrite\
        --models-disable\
        --no-verify-results\
        --log-level=DEBUG\
        --with-robot-leds"

################################################################################
# Basic Experiment                                                             #
################################################################################
if [ "$TASK" == "demo1" ]; then
    $BASE_CMD --controller=d0.CRW\
              --scenario=SS.12x6x2\
              --n-sims=24
fi

################################################################################
# Controller Comparison: CRW and DPO                                           #
################################################################################
if [ "$TASK" == "demo2" ]; then
    $BASE_CMD --controller=d0.DPO\
              --scenario=SS.12x6x2\
              --n-sims=24

    $BASE_CMD --pipeline 5\
              --controller-comparison\
              --controller-list=d0.CRW,d0.DPO\
              --controllers-legend=CRW,DPO\
              --bc-univar
fi

################################################################################
# ARGoS Video Rendering                                                        #
################################################################################
if [ "$TASK" == "demo3" ]; then
    $BASE_CMD --controller=d0.CRW\
              --scenario=SS.12x6x2\
              --n-sims=4\
              --argos-rendering\
              --exp-graphs=none
fi

################################################################################
# .csv Video Rendering                                                         #
################################################################################
if [ "$TASK" == "demo4" ]; then
    $BASE_CMD --controller=d0.CRW\
              --scenario=RN.12x12x2\
              --n-sims=4\
              --project-imagizing\
              --project-rendering\
              --exp-graphs=none
fi

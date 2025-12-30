#!/bin/bash -l

################################################################################
# Setup Simulation Environment                                                 #
################################################################################
set -x

export AWS_BATCH_JOB_ID=1234
export AWS_BATCH_JOB_NUM_NODES=1
echo ":" > /tmp/awsbatch-nodefile
$SIERRA_CMD \
    --execenv=hpc.awsbatch \
    --nodefile=/tmp/awsbatch-nodefile \
    --exec-parallelism-paradigm=per-batch \
    --exec-jobs-per-node=2

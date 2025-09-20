#!/bin/bash -l
#PBS -S /bin/bash
#PBS -q batch
#PBS -l nodes=1:ppn=2
#PBS -l mem=32gb
#PBS -l walltime=48:00:00
#PBS -N pbs-test
#PBS -m abe

################################################################################
# Setup Simulation Environment                                                 #
################################################################################
set -x

export PBS_NODEFILE=/tmp/pbs-nodefile
export PBS_NUM_PPN=1
export PBS_JOBID=12345678
echo ":" > /tmp/pbs-nodefile
$SIERRA_CMD \
    --execenv=hpc.pbs \
    --exec-parallelism-paradigm=per-exp \
    --exec-jobs-per-node=2

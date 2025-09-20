#!/bin/bash -l
#SBATCH --time=00:10:00
#SBATCH --nodes 1
#SBATCH --tasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --output=R-%x.%j.out
#SBATCH --error=R-%x.%j.err
#SBATCH -J slurm-test

################################################################################
# Setup Simulation Environment                                                 #
################################################################################
set -x

# HACK HACK HACK!
# GNU parallel isn't smart enough to figure out that 'localhost' means
# "don't use ssh". passwordless ssh to localhost isn't set up by
# default on github action runners, so we fudge the SLURM environment
# a bit to make things work
export SLURM_JOB_NODELIST=":"
$SIERRA_CMD --execenv=hpc.slurm  --exec-parallelism-paradigm=per-exp

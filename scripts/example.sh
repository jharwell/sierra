#!/bin/bash -l
#SBATCH --time=4:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --ncputs-per-task=24
#SBATCH --mem=2gb
#SBATCH --mail-type=ALL
#SBATCH --mail-user=harwe006@umn.edu
#SBATCH --output=R-%x.%j.out
#SBATCH --error=R-%x.%j.err
#SBATCH -J SIERRA-example

################################################################################
# Setup Simulation Environment                                                 #
################################################################################
# Set paths
FORDYCA=$HOME/git/fordyca
SIERRA=$HOME/git/sierra

################################################################################
# Begin Experiments                                                            #
################################################################################
OUTPUT_ROOT=$HOME/exp

cd $SIERRA
python3 sierra.py \
        --sierra-root=$OUTPUT_ROOT\
        --template-input-file=$SIERRA/templates/ideal.argos \
        --n-sims=24\
        --project=fordyca\
        --hpc-env=local\
        --physics-n-engines=1\
        --controller=d0.CRW\
        --scenario=SS.12x6\
        --batch-criteria population_size.Log64\
        --n-blocks=20\
        --time-setup=time_setup.T10000\
        --exp-overwrite\
        --models-disable

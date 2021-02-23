#!/bin/bash -l
#SBATCH --time=12:00:00
#SBATCH --nodes 32
#SBATCH --cpus-per-task=24
#SBATCH --mem-per-cpu=2G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=harwe006@umn.edu
#SBATCH --output=R-%x.%j.out
#SBATCH --error=R-%x.%j.err
#SBATCH -J 2021-tro-sc2

################################################################################
# Setup Simulation Environment                                                 #
################################################################################
# set -x

# Initialize modules
source /home/gini/shared/swarm/bin/msi-env-setup.sh

if [ -n "$MSIARCH" ]; then # Running on MSI
    export SIERRA_ROOT=$HOME/research/$MSIARCH/sierra
    export FORDYCA_ROOT=$HOME/research/$MSIARCH/fordyca
else
    export SIERRA_ROOT=$HOME/git/sierra
    export FORDYCA_ROOT=$HOME/git/fordyca
fi

# Set ARGoS library search path. Must contain both the ARGoS core libraries path
# AND the fordyca library path.
export ARGOS_PLUGIN_PATH=$ARGOS_PLUGIN_PATH:$FORDYCA_ROOT

# Setup logging (maybe compiled out and unneeded, but maybe not)
export LOG4CXX_CONFIGURATION=$FORDYCA_ROOT/log4cxx.xml

# Set SIERRA ARCH
export SIERRA_ARCH=$MSIARCH

# From MSI docs: transfers all of the loaded modules to the compute nodes (not
# inherited from the master/launch node when using GNU parallel)
export PARALLEL="--workdir . --env PATH --env LD_LIBRARY_PATH --env
LOADEDMODULES --env _LMFILES_ --env MODULE_VERSION --env MODULEPATH --env
MODULEVERSION_STACK --env MODULESHOME --env OMP_DYNAMICS --env
OMP_MAX_ACTIVE_LEVELS --env OMP_NESTED --env OMP_NUM_THREADS --env
OMP_SCHEDULE --env OMP_STACKSIZE --env OMP_THREAD_LIMIT --env OMP_WAIT_POLICY
--env ARGOS_PLUGIN_PATH --env LOG4CXX_CONFIGURATION"

################################################################################
# Begin Experiments                                                            #
################################################################################
CONTROLLERS=(d0.CRW d0.DPO d1.BITD_DPO d2.BIRTD_DPO)
OUTPUT_ROOT=$HOME/exp/2021-tro-sc2
DENSITY=5p0 # 1036 robots with cardinality = 5
N_BLOCKS=4000
BLOCK_DIST=PL
XCARDINALITY=3
YCARDINALITY=8
TIME=time_setup.T20000N100
TASKS=("scalability" "flexibility" "robustness_pd" "robustness_saa")
NSIMS=4

SIERRA_BASE_CMD="python3 sierra.py \
                  --sierra-root=$OUTPUT_ROOT\
                  --template-input-file=$SIERRA_ROOT/templates/2021-tro-sc2.argos \
                  --n-sims=$NSIMS\
                  --pipeline 1\
                  --exp-graphs=inter\
                  --project=fordyca\
                  --dist-stats=conf95\
                  --with-robot-leds \
                  --exp-overwrite\
                  --exp-graphs=inter --project-no-yaml-LN\
                  --models-disable\
                  --log-level=DEBUG\
                  "

if [ -n "$MSIARCH" ] # Running on MSI
then
    # 4 controllers, 4 tasks
    TASK_NUM=$(($SLURM_ARRAY_TASK_ID % 4)) # This is the experiment
    CONTROLLER_NUM=$(($SLURM_ARRAY_TASK_ID / 4)) # This is the scenario
    CONTROLLERS=(${CONTROLLERS_LIST[$X]})
    TASK=${TASKS[$Y]}

    SIERRA_CMD="$SIERRA_BASE_CMD --hpc-env=slurm"
else
    CONTROLLERS=(d0.CRW d0.DPO d1.BITD_DPO d2.BIRTD_DPO)
    TASK="$1"

    SIERRA_CMD="$SIERRA_BASE_CMD\
                  --hpc-env=local\
                  --physics-n-engines=4\
                  --no-verify-results\
                  --plot-large-text\
                  --plot-log-xscale"
fi

cd $SIERRA_ROOT

# # Scalability/emergence analysis
if [ "$TASK" == "scalability" ] || [ "$TASK" == "emergence" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        $SIERRA_CMD --scenario=${BLOCK_DIST}.16x16 \
                  --batch-criteria population_density.CD${DENSITY}.I32.C${XCARDINALITY} block_motion_dynamics.C${YCARDINALITY}.F25p0.RW0p001\
                  --controller=${c} \
                  --n-blocks=${N_BLOCKS}\
                  --time-setup=${TIME}

    done
fi

# Flexibility analysis.
if [ "$TASK" == "flexibility" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        $SIERRA_CMD --scenario=${BLOCK_DIST}.16x16 \
                  --batch-criteria  population_density.CD${DENSITY}.I32.C${XCARDINALITY} temporal_variance.MSine\
                  --controller=${c}\
                  --n-blocks=${N_BLOCKS}\
                  --time-setup=${TIME}

    done
fi

# Robustness analysis.
if [ "$TASK" == "robustness_pd" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        # Depending on what Maria/reviewers say, I might have to add birth
        # dynamics to this to have a stable queueing system and get graph axis
        # ticks that are well defined.
        $SIERRA_CMD --scenario=${BLOCK_DIST}.16x16 \
                  --batch-criteria  population_density.CD${DENSITY}.I32.C${XCARDINALITY} population_dynamics.C${YCARDINALITY}.F2p0.D0p0001 \
                  --controller=${c} \
                  --n-blocks=${N_BLOCKS}\
                  --time-setup=${TIME}
    done
fi

if [ "$TASK" == "robustness_saa" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        $SIERRA_CMD --scenario=${BLOCK_DIST}.16x16 \
                  --batch-criteria  population_density.CD${DENSITY}.I32.C${XCARDINALITY} saa_noise.all.C${YCARDINALITY}\
                  --controller=${c} \
                  --n-blocks=${N_BLOCKS}\
                  --time-setup=${TIME}
    done
fi

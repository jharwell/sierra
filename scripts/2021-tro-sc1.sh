#!/bin/bash -l
#SBATCH --time=12:00:00
#SBATCH --nodes 32
#SBATCH --cpus-per-task=24
#SBATCH --mem-per-cpu=2G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=harwe006@umn.edu
#SBATCH --output=R-%x.%j.out
#SBATCH --error=R-%x.%j.err
#SBATCH -J 2021-tro-sc1

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
OUTPUT_ROOT=$HOME/exp/sc1
TIME_SHORT=time_setup.T10000
# TIME_SHORT=time_setup.T1000
TIME_LONG=time_setup.T200000N1000

CONTROLLERS_LIST=(d1.BITD_DPO)
TASKS=("scalability" "flexibility" "robustness_saa" "robustness_pd")
CARDINALITY=C8
NSIMS=12

SIERRA_BASE_CMD="python3 sierra.py \
                  --sierra-root=$OUTPUT_ROOT\
                  --template-input-file=$SIERRA_ROOT/templates/2021-tro-sc1.argos \
                  --n-sims=$NSIMS\
                  --pipeline 1 2 3 4 \
                  --exp-graphs=inter\
                  --project=fordyca\
                  --dist-stats=none\
                  --with-robot-leds \
                  --exp-overwrite\
                  --project-rendering --project-imagizing --serial-processing\
                  --exp-graphs=none\
                  --models-disable\
                  --log-level=DEBUG\
                  --exp-range=7:7
                  "

if [ -n "$MSIARCH" ] # Running on MSI
then
    # 4 controllers, 4 tasks
    TASK_NUM=$(($SLURM_ARRAY_TASK_ID % 4)) # This is the experiment
    CONTROLLER_NUM=$(($SLURM_ARRAY_TASK_ID / 4)) # This is the scenario
    CONTROLLERS=(${CONTROLLERS_LIST[$X]})
    TASK=${TASKS[$Y]}


    SIERRA_CMD="$SIERRA_BASE_CMD --hpc-env=slurm"

    echo "********************************************************************************\n"
    echo  squeue -j $SLURM_ARRAY_TASK_ID -o "%.9i %.9P %.8j %.8u %.2t %.10M %.6D %S %e"
    echo "********************************************************************************\n"
else
    TASK="$1"
    CONTROLLERS=("${CONTROLLERS_LIST[@]}")

    SIERRA_CMD="$SIERRA_BASE_CMD\
                  --hpc-env=local\
                  --physics-n-engines=1\
                  --no-verify-results\
                  --plot-large-text\
                  --plot-log-xscale"
fi

cd $SIERRA_ROOT

# Scalability/emergence analysis
if [ "$TASK" == "scalability" ] || [ "$TASK" == "emergence" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        # $SIERRA_CMD --scenario=SS.32x16 \
        #           --batch-criteria population_size.Log128 \
        #           --controller=${c} \
        #           --n-blocks=128\
        #           --time-setup=${TIME_SHORT}


        $SIERRA_CMD --scenario=RN.48x48 \
                  --batch-criteria population_size.Log512 \
                  --controller=${c} \
                  --n-blocks=512\
                  --time-setup=${TIME_SHORT}

        # $SIERRA_CMD --scenario=RN.96x96 \
        #           --batch-criteria population_size.Log2048 \
        #           --controller=${c} \
        #           --n-blocks=2048\
        #           --time-setup=${TIME_SHORT}

    done
fi

# Flexibility analysis
if [ "$TASK" == "flexibility" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        $SIERRA_CMD --scenario=SS.32x16 \
                  --batch-criteria temporal_variance.BCSquare.Z50 \
                  --controller=${c}\
                  --n-blocks=50\
                  --time-setup=${TIME_SHORT}


        $SIERRA_CMD --scenario=RN.48x48 \
                  --batch-criteria temporal_variance.BCSquare.Z200\
                  --controller=${c} \
                  --n-blocks=200\
                  --time-setup=${TIME_SHORT}

    done
fi

# Robustness analysis
if [ "$TASK" == "robustness_saa" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        # Steady state population of 5 when total swarm size is 50 (repair queue
        # steady state of 45)
        # rho = 45/46

        $SIERRA_CMD --scenario=SS.32x16 \
                  --batch-criteria population_dynamics.${CARDINALITY}.F2p0.M0p001.R0p001022222\
                  --controller=${c} \
                  --n-blocks=50\
                  --n-robots=50\
                  --time-setup=${TIME_LONG}

        $SIERRA_CMD --scenario=SS.32x16 \
                  --batch-criteria saa_noise.all.${CARDINALITY}.Z50\
                  --controller=${c} \
                  --n-blocks=50\
                  --n-robots=50\
                  --time-setup=${TIME_SHORT}
    done
fi

if [ "$TASK" == "robustness_pd" ] || [ "$TASK" == "all" ]
then
    for c in "${CONTROLLERS[@]}"
    do
        # Steady state population of 20 when total swarm size is 200 (repair queue
        # steady state of 180)
        # rho = 180 / 181
        $SIERRA_CMD --scenario=RN.48x48 \
                  --batch-criteria population_dynamics.${CARDINALITY}.F2p0.M0p001.R0p001005556 \
                  --controller=${c} \
                  --n-blocks=200\
                  --n-robots=200\
                  --time-setup=${TIME_LONG}

        $SIERRA_CMD --scenario=RN.48x48 \
                  --batch-criteria saa_noise.all.${CARDINALITY}.Z200\
                  --controller=${c} \
                  --n-blocks=200\
                  --n-robots=200\
                  --time-setup=${TIME_SHORT}
    done
fi

if [ "$TASK" == "comp" ] || [ "$TASK" == "all" ]
then
    STAGE5_CMD="python3 sierra.py \
                  --project=fordyca\
                  --pipeline 5\
                  --sierra-root=$OUTPUT_ROOT"

    # Generate scalability/emergence comparison graphs
    $STAGE5_CMD --batch-criteria population_size.Log128 \
                --bc-univar\
                --plot-log-xaxis\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria population_size.Log128 \
                --bc-univar\
                --plot-log-xaxis\
                --controllers-list d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria population_size.Log512 \
                --bc-univar\
                --plot-log-xaxis\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria population_size.Log512 \
                --bc-univar\
                --plot-log-xaxis\
                --controllers-list d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend DPO,STOCHM,STOCHX

    $STAGE5_CMD --scenario=RN.96x96 \
                --batch-criteria population_size.Log2048 \
                --bc-univar\
                --plot-log-xaxis\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    # Generate flexibility comparison graphs
    $STAGE5_CMD --batch-criteria temporal_variance.BCSquare.Z200\
                --bc-univar\
                --bc-undefined-exp0\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria temporal_variance.BCSquare.Z50\
                --bc-univar\
                --bc-undefined-exp0\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    # Generate robustness comparison graphs
    $STAGE5_CMD --batch-criteria population_dynamics.${CARDINALITY}.F2p0.M0p001.R0p001022222\
                --bc-univar\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria population_dynamics.${CARDINALITY}.F2p0.M0p001.R0p001022222\
                --bc-univar\
                --controllers-list d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria saa_noise.all.${CARDINALITY}.Z50\
                --bc-univar\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria population_dynamics.${CARDINALITY}.F2p0.M0p001.R0p001005556 \
                --bc-univar\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria population_dynamics.${CARDINALITY}.F2p0.M0p001.R0p001005556 \
                --bc-univar\
                --controllers-list d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend DPO,STOCHM,STOCHX

    $STAGE5_CMD --batch-criteria saa_noise.all.${CARDINALITY}.Z200\
                --bc-univar\
                --controllers-list d0.CRW,d0.DPO,d1.BITD_DPO,d2.BIRTD_DPO\
                --controllers-legend CRW,DPO,STOCHM,STOCHX


fi

#!/bin/bash -l
################################################################################
# Setup Simulation Environment                                                 #
################################################################################
# Set paths
FORDYCA=$HOME/git/fordyca
SIERRA=$HOME/git/sierra

################################################################################
# Begin Experiments                                                            #
################################################################################
CONTROLLERS=(depth1.BITD_DPO)
SCENARIOS=(SS.128x64 DS.128x64 QS.96x96)

OUTPUT_ROOT=$HOME/exp/msi/2020-aamas-ideal
BASE_CMD="python3 sierra.py \
                  --template-input-file=$SIERRA/templates/2020-aamas-depth1-ideal.argos\
                  --time-setup=time_setup.T10000 \
                  --batch-criteria swarm_size.Log1024 ta_policy_set.All \
                  --sierra-root=$OUTPUT_ROOT --exp-graphs=inter --no-verify-results\
                  --pipeline 4 --physics-n-engines=8 --n-sims=50 --n-threads=8"

cd $SIERRA

echo "Running with controller=${CONTROLLERS[$PBS_ARRAYID]},scenario=${SCENARIOS[$PBS_ARRAYID]},block count=${BLOCK_COUNTS[$PBS_ARRAYID]}"


# for c in "${CONTROLLERS[@]}"
# do
#     for s in "${SCENARIOS[@]}"
#     do
#         $BASE_CMD\
#             --controller=${c}\
#             --scenario=${s}
#     done
# done

python3 sierra.py \
        --pipeline 5\
        --sierra-root=$OUTPUT_ROOT\
        --batch-criteria swarm_size.Log1024 ta_policy_set.All\
        --controller-comp-list=depth1.BITD_DPO,depth2.BIRTD_DPO\
        --normalize-comparisons

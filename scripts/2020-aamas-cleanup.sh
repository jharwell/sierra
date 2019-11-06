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
CONTROLLERS=(depth2.BIRTD_DPO)
SCENARIOS=(SS.128x64 DS.128x64 QS.96x96)

OUTPUT_ROOT=$HOME/exp/msi/2020-aamas-ideal
BASE_CMD="python3 sierra.py \
                  --template-input-file=$SIERRA/templates/2020-aamas-depth2-ideal.argos\
                  --time-setup=time_setup.T10000 \
                  --batch-criteria swarm_size.Log1024 ta_policy_set.All \
                  --sierra-root=$OUTPUT_ROOT --exp-graphs=inter --no-verify-results\
                  --pipeline 4 --physics-n-engines=8 --n-sims=20 --n-threads=8"

cd $SIERRA

# for c in "${CONTROLLERS[@]}"
# do
#     for s in "${SCENARIOS[@]}"
#     do
#         $BASE_CMD\
#             --controller=${c}\
#             --scenario=${s}
#     done
# done

# python3 sierra.py \
#         --pipeline 5\
#         --sierra-root=$OUTPUT_ROOT\
#         --batch-criteria swarm_size.Log1024 ta_policy_set.All\
#         --controllers-list=depth1.BITD_DPO,depth2.BIRTD_DPO\
#         --controllers-legend="Compound Task Decomposition Graph","Complex Task Decomposition Graph"\
#         --bc-bivar

CONTROLLERS=(depth2.BIRTD_ODPO)
SCENARIOS=(SS.128x64 DS.128x64 QS.96x96)

OUTPUT_ROOT=$HOME/exp/msi/2020-aamas-oracle-tasks
BASE_CMD="python3 sierra.py \
                  --template-input-file=$SIERRA/templates/2020-aamas-depth2-oracle-tasks.argos\
                  --time-setup=time_setup.T10000 \
                  --batch-criteria swarm_size.Log1024 ta_policy_set.All \
                  --sierra-root=$OUTPUT_ROOT --exp-graphs=inter --no-verify-results\
                  --pipeline 3 4 --physics-n-engines=8 --n-sims=20 --n-threads=8"

cd $SIERRA

# for c in "${CONTROLLERS[@]}"
# do
#     for s in "${SCENARIOS[@]}"
#     do
#         $BASE_CMD\
#                 --controller=${c}\
#                 --scenario=${s}
#     done
# done

python3 sierra.py \
        --pipeline 5\
        --sierra-root=$OUTPUT_ROOT\
        --batch-criteria swarm_size.Log1024 ta_policy_set.All\
        --controllers-list=depth1.BITD_ODPO,depth2.BIRTD_ODPO\
        --controllers-legend="Compound Task Decomposition Graph","Complex Task Decomposition Graph"\
        --bc-bivar

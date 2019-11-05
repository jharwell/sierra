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
CONTROLLERS=(depth1.BITD_ODPO)
SCENARIOS=(SS.36x18 DS.36x18)

OUTPUT_ROOT=$HOME/exp/msi/2020-aamas-constant-density10
BASE_CMD="python3 sierra.py \
                  --template-input-file=$SIERRA/templates/2020-aamas-depth1-oracle-tasks.argos\
                  --time-setup=time_setup.T10000 \
                  --batch-criteria swarm_density.CD10p0.I12 ta_policy_set.All \
                  --sierra-root=$OUTPUT_ROOT --exp-graphs=inter --no-verify-results\
                  --pipeline 3 4 --physics-n-engines=8 --n-sims=20 --n-threads=8"

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

CONTROLLERS=(depth2.BIRTD_ODPO)
SCENARIOS=(SS.36x18 DS.36x18)

BASE_CMD="python3 sierra.py \
                  --template-input-file=$SIERRA/templates/2020-aamas-depth2-oracle-tasks.argos\
                  --time-setup=time_setup.T10000 \
                  --batch-criteria swarm_density.CD10p0.I12 ta_policy_set.All \
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
        --batch-criteria swarm_density.CD10p0.I12 ta_policy_set.All\
        --controllers-list=depth1.BITD_ODPO,depth1.BITD_DPO\
        --controllers-legend="Compound Decomposition Graph","Complex Decomposition Graph"\
        --comparison-type='diff2D' \
        --bc-bivar

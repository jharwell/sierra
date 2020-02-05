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
CONTROLLERS=(depth0.CRW depth0.DPO depth1.BITD_DPO depth2.BIRTD_DPO)
# CONTROLLERS=(depth2.BIRTD_DPO)
SCENARIOS=(SS.96x48 DS.96x48)
BLOCK_COUNT=128
OUTPUT_ROOT=$HOME/exp
BASE_CMD="python3 sierra.py \
                  --time-setup=time_setup.T10000 \
                  --plugin=fordyca\
                  --physics-n-engines=4\
                  --n-sims=4\
                  --n-threads=4\
                  --n-blocks=$BLOCK_COUNT"

cd $SIERRA

# SAA robustness
for c in "${CONTROLLERS[@]}"
do
    for s in "${SCENARIOS[@]}"
    do
        $BASE_CMD\
            --template-input-file=$SIERRA/templates/2020-arms-saa-noise.argos\
            --controller=${c}\
            --sierra-root=$OUTPUT_ROOT/2020-arms-saa\
            --batch-criteria saa_noise.sensors.C10 \
            --scenario=${s}
    done
done

python3 sierra.py \
        --pipeline 5\
        --plugin=fordyca\
        --sierra-root=$OUTPUT_ROOT/2020-arms-saa\
        --batch-criteria saa_noise.sensors.C10\
        --controllers-list=depth0.CRW,depth0.DPO,depth1.BITD_DPO,depth2.BIRTD_DPO\
        --controllers-legend="CRW","DPO","BITD-DPO","BIRTD-DPO"\
        --comparison-type='raw1D'\
        --bc-univar

# Size robustness for steady state 75 robots with max 128 robots
# for c in "${CONTROLLERS[@]}"
# do
#     for s in "${SCENARIOS[@]}"
#     do
#         $BASE_CMD\
#             --template-input-file=$SIERRA/templates/2020-arms-pd.argos\
#             --controller=${c} --pipeline 4 --exp-graphs=inter\
#             --sierra-root=$OUTPUT_ROOT/2020-arms-pd\
#             --batch-criteria population_dynamics.C5.F1p0.B0p0019736.D0p002\
#             --scenario=${s}
#     done
# done

# python3 sierra.py \
#         --pipeline 5\
#         --plugin=fordyca\
#         --sierra-root=$OUTPUT_ROOT/2020-arms-pd\
#         --batch-criteria population_dynamics.C5.F1p0.B0p0019736.D0p002\
#         --controllers-list=depth0.CRW,depth0.DPO,depth1.BITD_DPO,depth2.BIRTD_DPO\
#         --controllers-legend="CRW","DPO","BITD-DPO","BIRTD-DPO"\
#         --comparison-type='raw1D'\
#         --bc-univar

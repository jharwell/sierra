#!/bin/bash
#
# PBS job script for the hpc.pbs smoke test. Submitted with:
#     qsub -W block=true ./tests/smoke_tests/pbs-test.sh
#
# Mirrors slurm-test.sh: it runs the SIERRA command passed in via the
# environment. The PBS-specific wrinkle vs. the old direct-run mock is that a
# PBS job does NOT start in the submit directory -- it starts in the
# submitter's $HOME. PBS exports the submit dir as $PBS_O_WORKDIR, so we cd
# there first. Without this, relative paths in SIERRA_CMD resolve against
# /home/pbstest and the run fails in ways that look unrelated.
#
#PBS -N sierra_smoke
#PBS -l select=1:ncpus=1
#PBS -l walltime=00:30:00
#PBS -j oe

set -euo pipefail

# Land back in the directory the job was submitted from.
if [ -n "${PBS_O_WORKDIR:-}" ]; then
    cd "${PBS_O_WORKDIR}"
fi

# qsub with `-V` (or `-E` on the sudo wrapper) exports the submitter's env,
# so SIERRA_CMD set by the nox session is visible here, same as the SLURM path.
if [ -z "${SIERRA_CMD:-}" ]; then
    echo "pbs-test.sh: SIERRA_CMD is not set in the job environment" >&2
    exit 1
fi

echo "pbs-test.sh: PBS_O_WORKDIR=${PBS_O_WORKDIR:-<unset>}"
echo "pbs-test.sh: running: ${SIERRA_CMD}"

# Word-splitting is intentional here: SIERRA_CMD is a full command line, the
# same way slurm-test.sh consumes it.
# shellcheck disable=SC2086
set -x

env

${SIERRA_CMD} \
    --execenv=hpc.pbs \
    --exec-parallelism-paradigm=per-exp \
    --exec-jobs-per-node=2

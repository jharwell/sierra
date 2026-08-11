#!/bin/bash
set -e
source /etc/pbs.conf

# 1. Postgres backs the PBS data service. sysvinit wrapper works w/o systemd.
service postgresql start
sleep 3

# 2. Start all PBS daemons (reads PBS_START_* from /etc/pbs.conf)
${PBS_EXEC}/libexec/pbs_init.d start
sleep 5

# 3. Register this host as a compute node (idempotent)
${PBS_EXEC}/bin/qmgr -c "create node localhost" 2>/dev/null || true

# 4. Make sure scheduling is on and the queue accepts/runs jobs
${PBS_EXEC}/bin/qmgr -c "set server scheduling = true"
${PBS_EXEC}/bin/qmgr -c "set server default_queue = workq" 2>/dev/null || true
${PBS_EXEC}/bin/qmgr -c "set queue workq enabled = true" 2>/dev/null || true
${PBS_EXEC}/bin/qmgr -c "set queue workq started = true" 2>/dev/null || true

# 5. Wait for the node to actually reach state 'free' before returning.
#    qsub will hold jobs forever if the mom hasn't checked in yet.
for i in $(seq 1 30); do
    if ${PBS_EXEC}/bin/pbsnodes -a 2>/dev/null | grep -q 'state = free'; then
        echo "PBS node is free and ready"
        break
    fi
    echo "waiting for mom to report free ($i/30)"
    sleep 2
done

${PBS_EXEC}/bin/pbsnodes -a

#!/bin/bash
#
# Bring OpenPBS fully up inside the container and block until it can actually
# accept and run jobs. Safe to run more than once (idempotent).
#
# Ordering matters: postgres (data service) -> pbs daemons -> node registered
# -> scheduling on -> wait for the mom to report the node 'free'. qsub will
# hold a job in 'Q' forever if the node hasn't checked in, so the final wait
# loop is what makes this usable as a synchronous smoke test.
#
set -euo pipefail

# shellcheck disable=SC1091
source /etc/pbs.conf

# CRITICAL: pbs_server sizes its epoll event buffer from RLIMIT_NOFILE and
# passes (nofile - 1) straight to epoll_pwait() as maxevents. Some container
# runtimes (notably Podman/containerd on recent Fedora) default nofile to
# ~2^30, which exceeds the kernel's EP_MAX_EVENTS ceiling -- so epoll_pwait
# returns EINVAL on EVERY call and pbs_server spins at 100% CPU, never
# servicing clients. That in turn makes pbs_habitat hang forever (it waits on
# a temp server that can't finish) and the mom never registers.
#
# In CI this is the PRIMARY fix, not a fallback: the GitHub Actions
# `container:` directive starts the container for us, so there is no
# `docker run` we control on which to pass `--ulimit`. Lowering the soft
# limit is unprivileged and always permitted, so capping here works
# everywhere. (The workflow's `options:` line ALSO sets
# `--ulimit nofile=8192:8192` as declared intent, but do NOT rely on that
# alone -- this line is what guarantees it.) Do NOT remove it thinking it's
# redundant: it is the difference between a working PBS and a 100% CPU spin
# that hangs pbs_habitat forever.
ulimit -n 8192 2>/dev/null || true

# PBS_SERVER must match the container's actual hostname. Locally we run with
# --hostname localhost, but CI's container: directive assigns a random hostname
# (e.g. 15d56b361a75), and a mismatch makes qmgr/mom unable to reach the server
# ("cannot connect to server", "Connection refused"). Rewrite pbs.conf to the
# real hostname before starting anything.
HN="$(hostname)"
sed -i "s/^PBS_SERVER=.*/PBS_SERVER=${HN}/" /etc/pbs.conf

# Ensure the hostname resolves (PBS needs it to). Docker usually adds this,
# but make it explicit.
grep -q "$(hostname)" /etc/hosts || echo "127.0.0.1 $(hostname)" >> /etc/hosts

echo "[pbs-start] starting postgres (backs the PBS data service)"
service postgresql start
sleep 3

# Initialize the PBS datastore on first boot if it isn't already valid. In a
# container the build-time datastore state is unreliable, and pbs_init.d's
# auto-habitat falls into an "upgrade" path that fails ("Datastore upgrade
# cannot continue") when there's no prior install to upgrade. PG_VERSION is
# postgres's own marker of a fully-initialized cluster, so its absence is a
# reliable "needs fresh init" signal.
if [ ! -f "${PBS_HOME}/datastore/PG_VERSION" ]; then
    echo "[pbs-start] no valid datastore, initializing fresh via pbs_habitat"
    rm -rf "${PBS_HOME}/datastore"
    "${PBS_EXEC}/libexec/pbs_habitat"
fi

echo "[pbs-start] starting PBS daemons"
# Reads PBS_START_* from /etc/pbs.conf and launches server/sched/comm/mom.
"${PBS_EXEC}/libexec/pbs_init.d" start
sleep 5

echo "[pbs-start] registering ${HN} as a compute node"
"${PBS_EXEC}/bin/qmgr" -c "create node ${HN}" 2>/dev/null || true

echo "[pbs-start] enabling scheduling and the default queue"
"${PBS_EXEC}/bin/qmgr" -c "set server scheduling = true"
"${PBS_EXEC}/bin/qmgr" -c "set server default_queue = workq"       2>/dev/null || true
"${PBS_EXEC}/bin/qmgr" -c "set queue workq enabled = true"          2>/dev/null || true
"${PBS_EXEC}/bin/qmgr" -c "set queue workq started = true"          2>/dev/null || true

# Allow root to submit jobs. PBS refuses root submissions by default, which is
# correct on a real cluster but wrong for a throwaway CI container: everything
# here runs as root inside a nox-managed virtualenv, and a separate submitter
# user (pbstest) can't reach that venv, so the job fails with exit 127
# (sierra: command not found). Letting root submit means the job runs in the
# same environment nox set up -- which is exactly the environment the other
# execenv branches test. Security is irrelevant in a disposable container.
"${PBS_EXEC}/bin/qmgr" -c "set server acl_roots = root@*"

echo "[pbs-start] waiting for the node to reach state 'free'"
ready=0
for i in $(seq 1 30); do
    if "${PBS_EXEC}/bin/pbsnodes" -a 2>/dev/null | grep -q 'state = free'; then
        echo "[pbs-start] node is free and ready"
        ready=1
        break
    fi
    echo "[pbs-start] waiting for mom to report free ($i/30)"
    sleep 2
done

"${PBS_EXEC}/bin/pbsnodes" -a || true

if [ "$ready" -ne 1 ]; then
    echo "[pbs-start] ERROR: node never reached 'free'. Recent server log:" >&2
    tail -n 40 "${PBS_HOME}"/server_logs/* 2>/dev/null >&2 || true
    exit 1
fi

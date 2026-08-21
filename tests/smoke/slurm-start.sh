#!/bin/bash
#
# Bring SLURM fully up inside the container and block until the node can
# actually accept and run jobs. Safe to run more than once (idempotent).
#
# Ordering matters: munge (auth) -> slurmctld (controller) -> slurmd (compute
# daemon) -> node forced IDLE -> wait until sinfo reports the node idle. sbatch
# fails immediately with "Unable to contact slurm controller (connect failure)"
# if slurmctld isn't up, and a job holds in the queue forever if slurmd hasn't
# registered the node, so the final wait loop is what makes this usable as a
# synchronous smoke test.
#
# Background: the Debian slurm packages ship systemd units and rely on
# `systemctl` to start the daemons at boot. CI containers do NOT run under
# systemd (the job process is effectively PID 1), so nothing ever fires those
# units -- the package being "installed" does not mean the daemons are running.
set -euo pipefail

log() { echo "[slurm-start] $*"; }

# --- munge (authentication) ------------------------------------------------
# slurmctld/slurmd authenticate clients via munge; munged must be up first,
# with a valid key. Missing munge surfaces as the SAME "unable to contact
# controller" error, so start it explicitly rather than assuming auto-start.
if ! pgrep -x munged >/dev/null 2>&1; then
    if [ ! -f /etc/munge/munge.key ]; then
        log "no munge key, creating one"
        # create-munge-key on Debian; fall back to a raw key if absent.
        if command -v create-munge-key >/dev/null 2>&1; then
            create-munge-key -f
        else
            dd if=/dev/urandom bs=1 count=1024 >/etc/munge/munge.key 2>/dev/null
        fi
        chown munge:munge /etc/munge/munge.key 2>/dev/null || true
        chmod 400 /etc/munge/munge.key 2>/dev/null || true
    fi
    log "starting munged"
    # --force clears a stale socket/pid left by a previous (crashed) run so a
    # retry doesn't fail on "already running".
    runuser -u munge -- /usr/sbin/munged --force 2>/dev/null \
        || munged --force 2>/dev/null \
        || true
    sleep 1
else
    log "munged already running"
fi

# --- cgroup plugin: bypass systemd for containerized slurmd -----------------
# SLURM 23.11's slurmd initializes a cgroup context at startup regardless of
# ProctrackType/TaskPlugin. Its cgroup/v2 plugin normally creates the stepd
# scope via dbus + systemd; in a container with no systemd as PID 1 that fails
# ("_init_new_scope_dbus ... could not be set" / "cannot create cgroup context
# for cgroup/v2" / "slurmd initialization failed"), the node never registers,
# and sbatch --wait hangs. The fix is cgroup.conf with IgnoreSystemd=yes, which
# makes the v2 plugin manage cgroups directly via cgroupfs (no systemd).
#
# NOTE: `CgroupPlugin=disabled` does NOT work on this build -- there is no
# cgroup/disabled plugin ("cannot find cgroup plugin for disabled"). Use
# autodetect + IgnoreSystemd instead.
#
# Normally baked into the image at /etc/slurm/cgroup.conf; ensure it here so the
# script is self-contained (like pbs-start.sh). We (re)write when the file is
# missing OR still carries the broken `disabled` value, so a stale image conf
# can't keep slurmd wedged.
SLURM_CONF_DIR="${SLURM_CONF_DIR:-/etc/slurm}"
cgroup_conf="${SLURM_CONF_DIR}/cgroup.conf"
if [ ! -f "${cgroup_conf}" ] || grep -qiE '^\s*CgroupPlugin\s*=\s*disabled' "${cgroup_conf}" 2>/dev/null; then
    log "writing ${cgroup_conf} (autodetect + IgnoreSystemd=yes)"
    {
        echo "CgroupPlugin=autodetect"
        echo "IgnoreSystemd=yes"
    } > "${cgroup_conf}" 2>/dev/null \
        || log "WARNING: could not write ${cgroup_conf}"
fi

# --- pre-create the stepd scope directory ----------------------------------
# With --cgroupns=host, this container's own cgroup is already UNDER
# system.slice (/proc/self/cgroup -> 0::/system.slice/docker-<id>.scope). The
# cgroup/v2 plugin (IgnoreSystemd) then hard-appends "system.slice/<name>.scope"
# and tries to mkdir the LEAF only, so the effective path DOUBLES:
#   /sys/fs/cgroup/system.slice/system.slice/localhost_slurmstepd.scope
# slurmd won't create the missing intermediate parent, so it dies with
# "Could not create scope directory ... No such file or directory". Pre-create
# the parent so the leaf mkdir succeeds. This is exactly what the pre-migration
# CI did inline; it is REQUIRED for this SLURM version under cgroupns=host, not
# an optional workaround. (The doubled system.slice is intentional -- match it.)
_stepd_scope="/sys/fs/cgroup/system.slice/system.slice/localhost_slurmstepd.scope"
if [ ! -d "${_stepd_scope}" ]; then
    log "pre-creating stepd scope dir ${_stepd_scope}"
    mkdir -p "${_stepd_scope}" 2>/dev/null \
        || log "WARNING: could not create ${_stepd_scope} (slurmd may fail)"
fi

# --- controller + compute daemons -----------------------------------------
# -D runs in the foreground; we background each and poll for readiness rather
# than sleeping a fixed interval (a fixed `sleep 5` races on a slow runner).
if ! pgrep -x slurmctld >/dev/null 2>&1; then
    log "starting slurmctld (controller)"
    slurmctld -D &
else
    log "slurmctld already running"
fi

# Wait for the controller to answer before starting slurmd / touching state.
ctld_up=0
for i in $(seq 1 30); do
    if scontrol ping >/dev/null 2>&1; then
        log "slurmctld is up"
        ctld_up=1
        break
    fi
    log "waiting for slurmctld to answer ($i/30)"
    sleep 1
done
if [ "$ctld_up" -ne 1 ]; then
    log "ERROR: slurmctld never answered. Running 'slurmctld -Dvvv' once for diagnostics:" >&2
    slurmctld -Dvvv >&2 2>&1 &
    sleep 3
    exit 1
fi

if ! pgrep -x slurmd >/dev/null 2>&1; then
    log "starting slurmd (compute daemon)"
    slurmd -D &
else
    log "slurmd already running"
fi

# slurmd can exit almost immediately (e.g. cgroup/dbus init failure) yet leave
# the controller reporting the node as IDLE because we forced it. If we don't
# catch that here, sbatch --wait hangs forever on "Nodes not responding". So
# verify the process is actually alive after a moment.
sleep 2
if ! pgrep -x slurmd >/dev/null 2>&1; then
    log "ERROR: slurmd exited immediately after start. Re-running 'slurmd -Dvvv' for the reason:" >&2
    slurmd -Dvvv >&2 2>&1 || true
    log "If this is a cgroup init error: ${cgroup_conf} should contain" >&2
    log "  CgroupPlugin=autodetect / IgnoreSystemd=yes  (NOT CgroupPlugin=disabled" >&2
    log "  -- no such plugin on this build). IgnoreSystemd lets cgroup/v2 run" >&2
    log "  without systemd, which a container lacks." >&2
    log "If the scope path is DOUBLED (system.slice/system.slice/...), that is" >&2
    log "  EXPECTED under --cgroupns=host (this container's cgroup is already" >&2
    log "  under system.slice; slurmd appends another). The fix is to pre-create" >&2
    log "  /sys/fs/cgroup/system.slice/system.slice/localhost_slurmstepd.scope" >&2
    log "  (this script does that above) -- NOT to remove --cgroupns=host." >&2
    log "Valid cgroup plugins: ls /usr/lib/*/slurm-wlm/ | grep cgroup" >&2
    exit 1
fi

# --- force the node schedulable -------------------------------------------
# The DOWN(reason)->IDLE bounce forces the node into a schedulable state
# immediately instead of waiting out the health-check/registration timeout.
# Node name is read from slurm.conf; default to localhost (what the packaged
# single-node conf uses). Override via $SLURM_NODENAME if the conf differs.
NODE="${SLURM_NODENAME:-localhost}"
scontrol update nodename="${NODE}" state=DOWN reason=initial 2>/dev/null || true
scontrol update nodename="${NODE}" state=IDLE 2>/dev/null || true

# --- wait until the node is actually idle ----------------------------------
log "waiting for node ${NODE} to reach state 'idle'"
ready=0
for i in $(seq 1 30); do
    # sinfo state codes: idle / mix are schedulable; drain/down/unk are not.
    if sinfo -h -n "${NODE}" -o '%t' 2>/dev/null | grep -qE '^(idle|mix)'; then
        log "node is idle and ready"
        ready=1
        break
    fi
    log "waiting for node to report idle ($i/30)"
    sleep 2
done

sinfo -N -l 2>/dev/null || true

if [ "$ready" -ne 1 ]; then
    log "ERROR: node never reached 'idle'." >&2
    scontrol show node "${NODE}" >&2 2>&1 || true
    exit 1
fi

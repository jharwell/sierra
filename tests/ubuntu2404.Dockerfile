FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

################################################################################
# SIERRA core
################################################################################
RUN set -ex

RUN apt-get update && apt-get install -y \
    gnupg ca-certificates

RUN apt-get update && apt-get install -y \
    lsb-release \
    git \
    parallel \
    cmake \
    parallel \
    cm-super \
    dvipng \
    pssh \
    ffmpeg \
    xvfb \
    libblas-dev \
    texlive-fonts-recommended \
    texlive-latex-extra \
    curl \
    python3-dev \
    clang \
    build-essential \
    psmisc \
    libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

# Don't keep downloaded .deb archives in image layers (avoids /var/cache/apt
# filling up during large multi-stage installs like TeXLive + source builds).
RUN echo 'Binary::apt::APT::Keep-Downloaded-Packages "false";' \
    > /etc/apt/apt.conf.d/no-cache

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

################################################################################
# ARGoS engine
################################################################################
# ARGoS dependencies
RUN apt-get update && apt-get install -y \
    qtbase5-dev \
    libfreeimageplus-dev \
    freeglut3-dev \
    libeigen3-dev \
    libudev-dev \
    liblua5.3-dev \
    libfreeimage-dev \
    libxi-dev \
    libxmu-dev \
    libgraphviz-dev \
    asciidoc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/jharwell/argos3.git && \
    cd argos3 && \
    git checkout devel && \
    mkdir build && cd build && \
    cmake -DARGOS_DOCUMENTATION=OFF -DARGOS_WITH_LUA=OFF ../src && \
    make -j $(grep -c ^processor /proc/cpuinfo) install && \
    rm -rf argos3

################################################################################
# SLURM execution environment
################################################################################
RUN apt-get update && apt-get install -y \
    slurmd \
    slurmctld \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/slurm-llnl/ && \
    chmod 777 /etc/slurm-llnl && \
    mkdir -p /var/lib/slurm-llnl/slurmd && \
    mkdir -p /var/lib/slurm-llnl/slurmctld/ && \
    chown slurm:slurm /var/lib/slurm-llnl && \
    mkdir -p /var/log/slurm-llnl/ && \
    chown -R slurm:slurm /etc/slurm-llnl/ && \
    chown -R slurm:slurm /var/lib/slurm-llnl/ && \
    chown -R slurm:slurm /var/log/slurm-llnl/

COPY ./tests/smoke_tests/slurm.conf /etc/slurm-llnl/slurm.conf
COPY ./tests/smoke_tests/slurm.conf /etc/slurm/slurm.conf

################################################################################
# PBS execution environment
################################################################################
# Build + runtime deps. Note vs. the OpenPBS INSTALL doc for 24.04:
#   - libpq-fe.h comes from postgresql-server-dev-all (DB headers; the
#     "Database headers not found" configure error otherwise)
#   - libcjson-dev is required by master
#   - sendmail-bin is listed in the 24.04 INSTALL deps
RUN apt-get update && apt-get install -y \
    gcc make libtool libhwloc-dev libx11-dev libxt-dev libedit-dev \
    libical-dev ncurses-dev perl postgresql postgresql-contrib \
    postgresql-server-dev-all libcjson-dev \
    python3-dev tcl-dev tk-dev swig libexpat-dev libssl-dev \
    libxext-dev libxft-dev autoconf automake g++ \
    git wget hostname sudo sendmail-bin \
    && rm -rf /var/lib/apt/lists/*

# Build from master, NOT v23.06.06: the last release predates Python 3.12 and
# fails on Ubuntu 24.04 with "fatal error: eval.h: No such file or directory".
# The Python 3.12 fixes only exist past the last tag. Pinned to a specific
# commit which is known to work as of 2026/08/12.
ARG OPENPBS_COMMIT=cd7ab5ed
RUN git clone https://github.com/openpbs/openpbs.git /opt/openpbs-src && \
    cd /opt/openpbs-src && git checkout ${OPENPBS_COMMIT}
WORKDIR /opt/openpbs-src

RUN ./autogen.sh && \
    ./configure --prefix=/opt/pbs && \
    make -j"$(nproc)" && \
    make install

# --- Ubuntu 24.04 fixes required BEFORE pbs_postinstall ---
# 1. The habitat/DB init scripts hardcode a RHEL-style PostgreSQL path
#    (/usr/pgsql-<ver>/...). Symlink Ubuntu's PG layout to where they look.
#    Derive the major version instead of hardcoding 16.x so a PG point-release
#    bump doesn't silently break the build.
RUN PG_MAJOR="$(ls /usr/lib/postgresql/)" && \
    PG_FULL="$(/usr/lib/postgresql/${PG_MAJOR}/bin/postgres --version | awk '{print $3}')" && \
    mkdir -p "/usr/pgsql-${PG_FULL}" && \
    ln -s /usr/lib/postgresql/${PG_MAJOR}/lib   "/usr/pgsql-${PG_FULL}/lib" && \
    ln -s /usr/share/postgresql/${PG_MAJOR}     "/usr/pgsql-${PG_FULL}/share" && \
    ln -s /usr/lib/postgresql/${PG_MAJOR}/bin/pg_resetwal \
          /usr/lib/postgresql/${PG_MAJOR}/bin/pg_resetxlog

# 2. pbs_db_utility uses a bash-ism ([[ ... ]]) but ships with a /bin/sh
#    shebang. On 24.04 /bin/sh is dash, not bash, so the DB init throws a
#    syntax error and the data service fails to come up. Force bash.
RUN sed -i '1s|^#!/bin/sh|#!/bin/bash|' /opt/pbs/libexec/pbs_db_utility

# Now the postinstall / datastore init will succeed.
RUN /opt/pbs/libexec/pbs_postinstall

# Setuid bits PBS needs
RUN chmod 4755 /opt/pbs/sbin/pbs_iff /opt/pbs/sbin/pbs_rcp

# Make PBS binaries available on PATH for all later steps / the entrypoint.
ENV PATH="/opt/pbs/bin:/opt/pbs/sbin:${PATH}"

# Mom config: trust localhost and allow our unprivileged submitter to run jobs.
RUN mkdir -p /var/spool/pbs/mom_priv && \
    printf '$clienthost localhost\n$restrict_user_maxsysid 999\n$logevent 0xffffffff\n' \
    > /var/spool/pbs/mom_priv/config

COPY ./tests/smoke_tests/pbs.conf /etc/pbs.conf

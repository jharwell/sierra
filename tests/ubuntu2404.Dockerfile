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
    libgraphviz-dev

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
    g++

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
    slurmctld

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
# Build + runtime deps (from OpenPBS INSTALL doc, adjusted for 24.04)
RUN apt-get update && apt-get install -y \
    gcc make libtool libhwloc-dev libx11-dev libxt-dev libedit-dev \
    libical-dev ncurses-dev perl postgresql postgresql-contrib \
    python3-dev tcl-dev tk-dev swig libexpat-dev libssl-dev \
    libxext-dev libxft-dev autoconf automake g++ \
    git wget hostname sudo \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch v23.06.06 https://github.com/openpbs/openpbs.git /opt/openpbs-src
WORKDIR /opt/openpbs-src

RUN ./autogen.sh && \
    ./configure --prefix=/opt/pbs && \
    make -j"$(nproc)" && \
    make install && \
    /opt/pbs/libexec/pbs_postinstall

# Setuid bits PBS needs
RUN chmod 4755 /opt/pbs/sbin/pbs_iff /opt/pbs/sbin/pbs_rcp

COPY ./tests/smoke_tests/pbs.conf /etc/pbs.conf

# Make PBS binaries available and set PBS_HOME for postinstall's DB init
ENV PATH="/opt/pbs/bin:/opt/pbs/sbin:${PATH}"

# Mom config: trust localhost, allow our test user to submit/run
RUN mkdir -p /var/spool/pbs/mom_priv && \
    printf '$clienthost localhost\n$restrict_user_maxsysid 999\n$logevent 0xffffffff\n' \
    > /var/spool/pbs/mom_priv/config

# PBS refuses jobs from root — create an unprivileged submitter
RUN useradd -m -s /bin/bash pbstest

# postgres user for the PBS data service must own PBS_HOME data dir
RUN /opt/pbs/libexec/pbs_habitat 2>/dev/null || true
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

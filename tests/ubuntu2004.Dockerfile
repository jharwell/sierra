FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

################################################################################
# SIERRA core
################################################################################
RUN set -ex

RUN apt-get update && apt-get install -y \
    lsb-release \
    git \
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
    gpg \
    clang \
    build-essential \
    wget \
    psmisc \
    libgraphviz-dev

# The version of parallel which comes with 20.04 is too old/doesn't support the
# PARALLEL envvar, so we have to install a newer one.
RUN wget https://ftpmirror.gnu.org/parallel/parallel-latest.tar.bz2 && \
    tar -xjf parallel-latest.tar.bz2 && \
    cd parallel-* && \
    ./configure && make && make install && \
    rm -rf parallel*


RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

################################################################################
# ROS1+Gazebo engine
################################################################################
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F42ED6FBAB17C654

RUN apt update && apt install -y \
    python3.9 \
    python3.9-dev \
    python3.9-venv \
    python3-apt \
    python3-cairo \
    intltool \
    python3-wheel \
    python3-pip \
    libxv1

RUN apt update && apt install -y \
    ros-noetic-ros-base \
    ros-noetic-turtlebot3-description \
    ros-noetic-turtlebot3-msgs \
    ros-noetic-turtlebot3-gazebo \
    ros-noetic-turtlebot3-bringup

FROM macos13:latest

ARG DEBIAN_FRONTEND=noninteractive

################################################################################
# SIERRA core
################################################################################
RUN set -ex

ENV HOMEBREW_NO_AUTO_UPDATE=1
ENV HOMEBREW_NO_INSTALL_UPGRADE=1

RUN brew update && brew install parallel pssh

# The version of parallel which comes with 20.04 is too old/doesn't support the
# PARALLEL envvar, so we have to install a newer one.
RUN wget https://ftpmirror.gnu.org/parallel/parallel-latest.tar.bz2 && \
    tar -xjf parallel-latest.tar.bz2 && \
    cd parallel-* && \
    ./configure && make && make install

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

############################################################################
# ARGoS engine
############################################################################
# 2023/01/16: Caching doesn't work reliably, for reasons unknown :-(.
#
# The {xquartz, mactex, qt} deps are not required as long as the ARGoS
# integration tests for OSX don't run stage 4+ or try to do video
# capture. Installing them takes ~30 min in github actions, so cutting
# this particular corner saves a TON of time.
#
# Note that by omitting Xquartz you MUST also omit Qt, otherwise CI
# fails (I think ARGoS segfaults).
RUN brew install pkg-config cmake libpng freeimage lua

RUN git clone https://github.com/jharwell/argos3.git && \
    cd argos3 && \
    git checkout devel && \
    mkdir build && cd build && \
    cmake -DARGOS_DOCUMENTATION=OFF -DARGOS_WITH_LUA=OFF ../src && \
    make -j $(grep -c ^processor /proc/cpuinfo) install && \
    rm -rf argos3

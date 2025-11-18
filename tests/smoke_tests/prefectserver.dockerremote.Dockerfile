FROM ubuntu:22.04

ARG USERNAME

RUN apt update && apt-get install python3-pip -y

RUN pip3 install \
    prefect \
    hvplot \
    hatchling \
    coloredlogs \
    distro \
    haggis \
    implements \
    jsonpath-ng \
    numpy \
    pandas \
    pyarrow \
    prefect[docker] \
    psutil \
    pyyaml \
    retry

# In CI, this makes prefect fail, even when it works locally, for unknown
# reasons. Locally, you need this so  files don't come out as owned by root
#
# For now, the easiest solution is to comment out for CI and re-enable locally
# as needed.

# RUN useradd -m -s /bin/bash ${USERNAME}
# USER ${USERNAME}

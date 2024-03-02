
# Copyright 2023 Two Six Technologies
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 

# inspiration from https://github.com/tiangolo/docker-with-compose
FROM ubuntu:18.04
LABEL maintainer="Two Six Labs <race@twosixlabs.com>"

# Configure Base Environment
ENV CODE_ROOT=/code/
ENV ENVIRONMENT=production
ENV RACE_ROOT=/race_in_the_box/
ENV SSH_ROOT=/root/.ssh/
ENV TMP_ROOT=/tmp/
ENV PATH="${PATH}:/race_in_the_box/scripts/voa"

# Install Python 3.8 & Configure Python Environment
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends \
        python3.8=3.8.0-3ubuntu1~18.04.2 \
        python3.8-dev=3.8.0-3ubuntu1~18.04.2 \
        python3-pip=9.0.1-2.3~ubuntu1.18.04.* && \
    python3.8 -m pip install --no-cache-dir --upgrade --force-reinstall pip==22.3.0 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1 && \
    update-alternatives --set python /usr/bin/python3.8 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 && \
    update-alternatives --set python3 /usr/bin/python3.8 && \
    update-alternatives --install /usr/bin/python3-config python3-config /usr/bin/python3.8-config 1 && \
    update-alternatives --set python3-config /usr/bin/python3.8-config
RUN ln -fs /usr/bin/python3.8 /usr/bin/python

# Run Make Directories
RUN mkdir -p ${RACE_ROOT} ${CODE_ROOT} ${SSH_ROOT} ${TMP_ROOT} 

# Install Linux Dependencies
# If any of these version pins fails you can use `apt-cache madison` to find the available versions
#     docker run -it --rm ubuntu:18.04 bash -c 'apt-get update && apt-cache madison <package name>'
RUN apt-get update && apt-get install -y \
        build-essential=12.4ubuntu1 \
        cargo=0.6* \
        curl=7.58.0-2ubuntu3.2* \
        dosfstools=4.1-1 \
        emacs=47.0 \
        git=1:2.17.1-1ubuntu0.1* \
        groff=1.22.3-10 \
        jq=1.5+dfsg-2 \
        less=487-0.1 \
        libc6-dev=2.27-3ubuntu1.6 \
        libffi-dev=3.2.1-8 \
        libfreetype6-dev=2.8.1-2ubuntu2.* \
        libopenblas-dev=0.2.20+ds-4 \
        libpng-dev=1.6.34-1ubuntu0.18.04.2 \
        libssl-dev=1.1.1-1ubuntu2.1~18.04.* \
        make=4.1-9.1ubuntu1 \
        net-tools=1.60+git20161116.90da8a0-1ubuntu1 \
        openssh-client=1:7.6p1-4ubuntu0.5 \
        redis-tools=5:4.0.9-1ubuntu0.2 \
        rsync=3.1.2-2.1ubuntu1.* \
        tree=1.7.0-5 \
        unzip=6.0* \
        vim=2:8.0.1453-1ubuntu1.* \
        zlib1g-dev=1:1.2.11.dfsg-0ubuntu2.2

# Install SRI Network Manager Graph Dependencies
# Need to lock the version of pyparsing because packaging (required by ansible)
# requires <3 but pydot asks for >=2 and installs a 3.x version
RUN apt-get update && \
    apt-get install -y graphviz=2.40.* && \
    python3.8 -m pip install pyparsing==2.4.7 pydot~=1.4.2

# Download adb
ARG ADB_VERSION=32.0.0
RUN curl -L \
        https://dl.google.com/android/repository/platform-tools_r${ADB_VERSION}-linux.zip \
        -o /tmp/platform-tools.zip && \
    cd /tmp && \
    unzip platform-tools.zip && \
    mv platform-tools/adb /usr/bin/adb && \
    rm -r /tmp/platform-tools*

COPY ./rib/requirements.txt $TMP_ROOT/temp_rib/
WORKDIR $TMP_ROOT/temp_rib/
RUN python3.8 -m pip install --upgrade \
        setuptools==60.2.0 \
        setuptools_rust==1.1.2 \
        wheel==0.37.1 && \
    CRYPTOGRAPHY_DONT_BUILD_RUST=1 python3.8 -m pip install -r $TMP_ROOT/temp_rib/requirements.txt

RUN python3.8 -m pip uninstall -y cryptography && \
    python3.8 -m pip install cryptography==36.0.02

# Install docker compose from website
RUN curl -L "https://github.com/docker/compose/releases/download/v2.14.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/bin/docker-compose
RUN chmod +x /usr/bin/docker-compose

# Install Docker per the instructions here:
# https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
RUN apt-get update && apt-get install -y \
        ca-certificates \
        gnupg=2.2.4-1ubuntu* \
        lsb-release=9.20170808ubuntu1

ARG TARGETARCH
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=$TARGETARCH signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y \
        containerd.io=1.4.12-1 \
        docker-ce=5:20.10.12~3-0~ubuntu-bionic \
        docker-ce-cli=5:20.10.12~3-0~ubuntu-bionic

# Setup Bash Environment
WORKDIR ${RACE_ROOT}
COPY ./docker-image/docker_environment/.bashrc /root/
COPY ./docker-image/docker_environment/.bash_profile /root/

# Add Symbolic Link for Bash History
RUN ln -s /root/.race/rib/user-state/.bash_history /root/.bash_history

# Add Symbolic Link for docker login
RUN ln -s /root/.race/rib/user-state/.docker /root/.docker

# Set up AWS Environment
RUN mkdir /root/.aws/ && \
    ln -s /root/.race/rib/aws/config /root/.aws/config && \
    ln -s /root/.race/rib/aws/credentials /root/.aws/credentials

# Set up Ansible Environment
ENV ANSIBLE_HOST_KEY_CHECKING=false

# Install RiB Code
WORKDIR ${RACE_ROOT}
# TODO: this copies the entire project (excluding files listed in the .dockerignore file) into the
# image. This adds a lot of files we don't need and increases the image size. Would be nice to
# address this at some point, either by restructring the project dir layout, or whitelisting the
# specific files/dirs we want (not supported by Docker yet), or some other option.
ADD . ${RACE_ROOT}

# Install the RiB tool (editable for now, need to figure out more)
WORKDIR ${RACE_ROOT}

RUN make install

# Move the User to the Code Directory (Where things should be mounted)
WORKDIR ${CODE_ROOT}

ARG RIB_VERSION=development
ENV RIB_VERSION=${RIB_VERSION}
ENV MTOOLS_SKIP_CHECK=1

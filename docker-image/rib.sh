#!/usr/bin/env bash

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

# -----------------------------------------------------------------------------
# Run an instance of the RACE in a Box system
#
# Note: Will spin up running a shell and the user can
# either exec into the container or run commands 1 at a time through
# docker exec (we recommend execing in)
# -----------------------------------------------------------------------------


set -e


###
# Helper Functions and Setup
###


Usage() {
cat << EOF  
Usage: sh rib.sh --code <code_dir>  [--version <value>] [--ssh <value>]

Common Arguments:
-c <value>, --code <value>, --code=<value>
    Absolute path to mount into /code in the container. This will include any
    code for building, range-configs for deployments, and more
-v <value>, --version <value>, --version=<value>
    Override version value for RiB. Note, rib.sh is coupled with rib due to mounts
    and other similar dependencies, so it is recommended to use the correct
    rib_x.y.z.sh entrypoint instead of overriding
-s <value>, --ssh <value>, --ssh=<value>
    Absolute path of private .ssh key to mount into RiB Container. Needed for AWS
    RiB functionality
-h, --help
    Print help and exit

TA3 Arguments (Unsupported but usabled by performers if needed)
-r <value>, --repo <value>, --repo=<value>
    Absolute path to mount into /config in the container. This will include any
    configuration files needed for running RACE
-C <value>, --command <value>, --command=<value>
    Run command in RiB container and exit instead of attaching to bash
--local
    Use a locally built RiB image instead of pulling from container registry
--detached
    Run RiB Detached
--dev
    Override production RiB code for development (e.g. race-ta3 vs race-common)
--verbose
    Verbose script, set -x
--rib_state_path <value>, --rib_state_path=<value>
    Override RiB's state path. Used for CI and similar environments
--custom_rib_path <value>, --custom_rib_path=<value>
    Set a custom path for your RiB source code. By setting this your RiB container
    will use the source code pointed to by this path. This will allow you to modify
    code on the fly and see the effects in your container immediately: very useful
    for local development.
    Sample usage:
        cd docker-image/
        ./build_race_in_the_box.sh
        ./rib.sh --code=/tmp --local --custom_rib_path=\$(pwd)/..
-i <value>, --ip-address <value>, --ip-address=<value>
    Local network IP address of the RiB host if auto-detection is not acceptable
--ui
    Enable running of UI container
--ui-port
    Use the given port for the UI container
--rib-tag
    Add given tag to the running race-in-the-box docker instance
EOF
}

formatlog() {
    LOG_LEVELS=("DEBUG" "INFO" "WARNING" "ERROR")
    if [ "$1" = "ERROR" ]; then
        RED='\033[0;31m'
        NO_COLOR='\033[0m'
        printf "${RED}%s (%s): %s${NO_COLOR}\n" "$(date +%c)" "${1}" "${2}"
    elif [ "$1" = "WARNING" ]; then
        YELLOW='\033[0;33m'
        NO_COLOR='\033[0m'
        printf "${YELLOW}%s (%s): %s${NO_COLOR}\n" "$(date +%c)" "${1}" "${2}"
    elif [ ! "$(echo "${LOG_LEVELS[@]}" | grep -co "${1}")" = "1" ]; then
        echo "$(date +%c): ${1}"
    else
        echo "$(date +%c) (${1}): ${2}"
    fi
}


###
# Arguments
###


# GitHub
CONTAINER_REGISTRY="ghcr.io"
CONTAINER_REPO="tst-race/race-in-the-box"

# Settings
ENVIRONMENT="production"
RIB_VERSION="2.6.0"
LAN_IP_ADDRESS=""
RIB_INSTANCE_TAG=""
RIB_UI_PORT="8501"

# Mounts
CODE_PATH=""
RIB_STATE_PATH="$HOME/.race/rib"

# Flags / Args
# Port 8000 is the REST API (FastAPI) and is used by the web app. It is exposed
# in order to be accessed when running the web app dev server rather than the
# web app container.
NETWORK_ARG="--network rib-overlay-network -p 8000:8000"
INTERACTIVE_FLAG="-it"
DETACHED_FLAG=""
LOCAL_RIB=false
RUN_UI=false

# Mounts
SSH_VOLUME_MOUNT=""
CUSTOM_RIB_PATH=""

# COMMANDS
INIT_COMMAND="python3.8 /race_in_the_box/scripts/internal/initialize_rib_state.py "
RIB_COMMAND="/bin/bash"
# CD into the rib directory so uvicorn only watches for changes in that folder
# rather than all of /code
RESTAPI_COMMAND="cd /race_in_the_box/rib && uvicorn rib.restapi.main:app --host 0.0.0.0 --reload > /var/log/rib-restapi.log 2>&1 "

# Parse CLI Arguments
while [ $# -gt 0 ]
do
    key="$1"

    case $key in
        -c|--code)
        CODE_PATH="$2"
        shift
        shift
        ;;
        --code=*)
        CODE_PATH="${1#*=}"
        shift
        ;;
        -r|--repo)
        CONTAINER_REPO="$2"
        shift
        shift
        ;;
        --repo=*)
        CONTAINER_REPO="${1#*=}"
        shift
        ;;
        -v|--version)
        RIB_VERSION="$2"
        shift
        shift
        ;;
        --version=*)
        RIB_VERSION="${1#*=}"
        shift
        ;;
        -C|--command)
        RIB_COMMAND="$2"
        INTERACTIVE_FLAG=""
        shift
        shift
        ;;
        --command=*)
        RIB_COMMAND="${1#*=}"
        INTERACTIVE_FLAG=""
        shift
        ;;
        --rib_state_path)
        RIB_STATE_PATH="$2"
        shift
        shift
        ;;
        --rib_state_path=*)
        RIB_STATE_PATH="${1#*=}"
        shift
        ;;
        -i|--ip-address)
        LAN_IP_ADDRESS="$2"
        shift
        shift
        ;;
        --ip-address=*)
        LAN_IP_ADDRESS="${1#*=}"
        shift
        ;;
        --ui)
        RUN_UI=true
        shift
        ;;
        -s|--ssh)
        if [ -z "$2" ] || [ ! -f "$2" ]; then
            formatlog "ERROR" "invalid ssh key: $2"
            exit 1
        fi
        SSH_VOLUME_MOUNT="-v $2:/root/.ssh/rib_private_key"
        shift
        shift
        ;;
        --ssh=*)
        SSH_PRIVATE_KEY="${1#*=}"
        # Handle tilde expansion
        SSH_PRIVATE_KEY="${SSH_PRIVATE_KEY/#\~/$HOME}"
        if [ -z "${SSH_PRIVATE_KEY}" ] || [ ! -f "${SSH_PRIVATE_KEY}" ]; then
            formatlog "ERROR" "invalid ssh key: ${SSH_PRIVATE_KEY}"
            exit 1
        fi
        SSH_VOLUME_MOUNT="-v ${SSH_PRIVATE_KEY}:/root/.ssh/rib_private_key"
        shift
        ;;
        --local)
        LOCAL_RIB=true
        shift
        ;;
        --detached)
        INTERACTIVE_FLAG=""
        DETACHED_FLAG="-d"
        shift
        ;;
        --dev)
        ENVIRONMENT="development"
        shift
        ;;
        --verbose)
        set -x
        shift
        ;;
        --custom_rib_path)
        CUSTOM_RIB_PATH="-v $2:/race_in_the_box"
        shift
        shift
        ;;
        --custom_rib_path=*)
        CUSTOM_RIB_PATH="-v ${1#*=}:/race_in_the_box"
        shift
        ;;
        --rib-tag)
        RIB_INSTANCE_TAG="-$2"
        shift
        shift
        ;;
        --rib-tag=*)
        RIB_INSTANCE_TAG="${1#*=}"
        shift
        ;;
        --ui-port)
        RIB_UI_PORT="$2"
        shift
        shift
        ;;
        --ui-port=*)
        RIB_UI_PORT="${1#*=}"
        shift
        ;;
        -h|--help)
        Usage
        exit 1;
        ;;
        *)
        Usage
        formatlog "ERROR" "unknown argument \"$1\""
        exit 1
        ;;
    esac
done

# If detached, entrypoint must not be bin/bash. So override with tail to hold open RiB container
if [ "$RIB_COMMAND" = "/bin/bash" ] && [ "$DETACHED_FLAG" = "-d" ]; then
    RIB_COMMAND="tail -f /dev/null"
fi

# Custom RIB Path is occasionally used for CI and testing. Be careful with this functionality
if [ -n "${CUSTOM_RIB_PATH}" ]; then
  formatlog "WARNING" "You are setting a custom path to your RiB source code \
(--custom_rib_path=RIB_PATH). Do not proceed if you do not know what you're doing. Using this \
parameter voids all warranties express and implied. Proceed with extreme caution."
  INIT_COMMAND="${INIT_COMMAND} && make build_package -C /race_in_the_box/"
fi

# Code Path is not required, but typically should be set. Print a big, scary warning if it's not provided.
if [ -z "${CODE_PATH}" ]
then
  formatlog "WARNING" "No CODE_PATH Specified (--code=CODE_PATH). RACE code will not be \
volume mounted."
else
  CODE_MOUNT="-v $CODE_PATH:/code --env HOST_CODE_PATH=$CODE_PATH"
fi


# Handling Relative Code Path
case $CODE_PATH in
  /*) ;;
  *) CODE_PATH=$(pwd)/$CODE_PATH ;;
esac

# Automatically determine LAN IP address if not explicitly set...
if [ -z "${LAN_IP_ADDRESS}" ]; then
    # If Linux, use `ip route get` to get the IP address
    if [ "$(uname)" == "Linux" ]; then
        set +e
        LAN_IP_ADDRESS=$(ip route get 1.2.3.4 | awk '{print $7}' | awk NF)
        set -e
    # Else if MacOS, use `ipconfig getifaddr` for en0 then en1
    elif [ "$(uname)" == "Darwin" ]; then
        set +e
        LAN_IP_ADDRESS=$(ipconfig getifaddr en0)
        set -e
        if [ -z "${LAN_IP_ADDRESS}" ]; then
            set +e
            LAN_IP_ADDRESS=$(ipconfig getifaddr en1)
            set -e
        fi
    fi
fi

# If unable to determine IP address, bail out
if [ -z "${LAN_IP_ADDRESS}" ]; then
    formatlog "ERROR" "Could not automatically determine the local IP address. Please set it using --ip-address."
    exit 1
else
    formatlog "INFO" "Using local IP address ${LAN_IP_ADDRESS}"
fi

###
# Main Execution
###


RIB_IMAGE=""
UI_IMAGE=""
if [ "$LOCAL_RIB" = false ] ; then
    RIB_IMAGE="${CONTAINER_REGISTRY}/${CONTAINER_REPO}/race-in-the-box:${RIB_VERSION}"
    UI_IMAGE="${CONTAINER_REGISTRY}/${CONTAINER_REPO}/race-in-the-box-ui:${RIB_VERSION}"
    formatlog "INFO" "Pulling Updated RiB: $RIB_IMAGE"
    docker pull "${RIB_IMAGE}"
    if [ "$RUN_UI" = true ] ; then
        formatlog "INFO" "Pulling Updated RiB UI: $UI_IMAGE"
        docker pull "${UI_IMAGE}"
    fi
else
    RIB_IMAGE="race-in-the-box:${RIB_VERSION}"
    UI_IMAGE="race-in-the-box-ui:${RIB_VERSION}"
    formatlog "INFO" "Pulling Updated RiB"
fi

formatlog "INFO" "RiB Details: "
echo "Image: ${RIB_IMAGE}"
docker inspect -f '{{ .Created }}' "${RIB_IMAGE}"
docker inspect --format '{{ index .Config.Labels "git_branch"}}' "${RIB_IMAGE}"
docker inspect --format '{{ index .Config.Labels "git_commit_sha"}}' "${RIB_IMAGE}"

if [ "$RUN_UI" = true ] ; then
    formatlog "INFO" "RiB UI Details: "
    echo "Image: ${UI_IMAGE}"
    docker inspect -f '{{ .Created }}' "${UI_IMAGE}"
    docker inspect --format '{{ index .Config.Labels "git_branch"}}' "${UI_IMAGE}"
    docker inspect --format '{{ index .Config.Labels "git_commit_sha"}}' "${UI_IMAGE}"
fi

# Need to detect if KVM is available for Android Hardware Excelleration
UNAME=$(uname)
if ls /dev/kvm &> /dev/null; then
    HAS_DEV_KVM=true
else
    HAS_DEV_KVM=false
fi

# If Host OS is linux, detect systemd version and warn if incompatible with RiB/RACE
HOST_SYSTEMCTL=
if [[ "$UNAME" = "Linux" ]]; then

    set +e
    if ! command -v systemctl &> /dev/null; then
        formatlog "WARNING" "systemctl not installed"
    else
        IFS=' ' read -r -a SYSTEMCTL_VERSION_RAW <<< "$(systemctl --version | head -n 1)"
        HOST_SYSTEMCTL="${SYSTEMCTL_VERSION_RAW[1]}"
        
        if [ "${HOST_SYSTEMCTL#* }" -ge "248" ]; then
            formatlog "WARNING" "RACE requires systemctl version <= 247"
        fi
    fi
    set -e
    
fi

HOST_ARCHITECTURE=$(uname -m)

# Checking ADB for Android Bridge Mode support
if command -v adb &> /dev/null; then
    HAS_ADB_SUPPORT=true
    if adb --version | grep -q '1.0.41' &> /dev/null; then
      # if adb exists, start the server so that adb communications can be established 
      # from inside of rib to the host machine
      adb kill-server
      adb -a nodaemon server start &> /dev/null &
      HOST_HAS_COMPATIBLE_ADB=true
    else
      HOST_HAS_COMPATIBLE_ADB=false
    fi
else
    HAS_ADB_SUPPORT=false
    HOST_HAS_COMPATIBLE_ADB=false
fi


# Checking for rib-overlay-network, creating if it does not exist
set +e
if ! docker network inspect "rib-overlay-network" &> /dev/null; then
    formatlog "INFO" "Running: docker network create 'rib-overlay-network' --subnet=10.11.0.0/16"
    docker network create "rib-overlay-network" --subnet=10.11.0.0/16  &> /dev/null;
fi
set -e

# Save RiB start time
RIB_START_TIME=$(date +%Y-%m-%d-%H-%m-%S)

if [ "$RUN_UI" = true ] ; then
    formatlog "INFO" "Run the RiB UI container detached"
    docker kill race-in-the-box-ui &> /dev/null || true
    docker run --rm -d --network rib-overlay-network -p "${RIB_UI_PORT}:80" --name="race-in-the-box-ui${RIB_INSTANCE_TAG}" "${UI_IMAGE}"
fi

formatlog "INFO" "Run the RiB container attached to shell"
RUN_COMMAND="docker run --rm ${INTERACTIVE_FLAG} ${DETACHED_FLAG} \
    ${NETWORK_ARG} \
    --add-host host.docker.internal:host-gateway \
    --env HOST_USER=$(whoami) \
    --env HOST_RIB_STATE_PATH=${RIB_STATE_PATH} \
    --env HOST_UNAME=${UNAME} \
    --env HOST_ARCHITECTURE=${HOST_ARCHITECTURE} \
    --env HOST_HAS_DEV_KVM=${HAS_DEV_KVM} \
    --env HOST_HAS_ADB_SUPPORT=${HAS_ADB_SUPPORT} \
    --env HOST_HAS_COMPATIBLE_ADB=${HOST_HAS_COMPATIBLE_ADB} \
    --env HOST_SYSTEMCTL=${HOST_SYSTEMCTL} \
    --env HOST_LAN_IP_ADDRESS=${LAN_IP_ADDRESS} \
    --env ENVIRONMENT=${ENVIRONMENT} \
    --env RIB_START_TIME=${RIB_START_TIME} \
    --env SSH_AUTH_SOCK=/root/.ssh/keyring \
    --env ANDROID_ADB_SERVER_ADDRESS=host.docker.internal \
    --env RIB_INSTANCE_TAG=${RIB_INSTANCE_TAG} \
    -v /var/run/docker.sock:/var/run/docker.sock \
    ${CODE_MOUNT} \
    -v ${RIB_STATE_PATH}:/root/.race/rib/ \
    ${CUSTOM_RIB_PATH} \
    ${SSH_VOLUME_MOUNT} \
    --name=race-in-the-box${RIB_INSTANCE_TAG} \
    ${RIB_IMAGE} \
    /bin/bash -c \"(${INIT_COMMAND}) && (${RESTAPI_COMMAND} &) && ${RIB_COMMAND}\"\
"
eval "${RUN_COMMAND}"
result=$?

docker kill race-in-the-box-ui &> /dev/null || true

exit $result

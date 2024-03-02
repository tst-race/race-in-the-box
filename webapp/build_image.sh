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
# Build the RACE in a Box UI Image
#
# Arguments:
# -v [value], --version [value], --version=[value]
#     Version of image to build
# -l [value], --label [value], --label=[value]
#     Labels to add to the docker image. good for debugging and testing
# -no-cache
#     Build docker image without using cache if it is available
# -h, --help
#     Print help and exit
#
# Example Call:
#    bash build_image.sh {--version=1.0.0} {--label=testing} {--no-cache}
# -----------------------------------------------------------------------------



###
# Helper Functions and Setup
###


set -xe
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


FILE_DIR="$(dirname "$0")"
RIB_VERSION=$(cat "${FILE_DIR}/../VERSION")
LABELS=()

# Parse CLI Arguments
while [ "$#" -gt 0 ]
do
    key="$1"

    case $key in
        --no-cache)
        CACHE_ARG=true
        shift # past argument=value
        ;;
        -v|--version)
        RIB_VERSION="$2"
        shift
        shift
        ;;
        --version=*)
        eval RIB_VERSION="${1#*=}"
        shift
        ;;
        --label)
        LABELS+=("$2")
        shift
        shift
        ;;
        *)
        formatlog "ERROR" "unknown argument \"$1\""
        exit 1
        ;;
    esac
done

if [ -z "${RIB_VERSION}" ]
then
  formatlog "ERROR" "No RIB_VERSION Specified (--version=VERSION) or in the VERSION file"
  exit 1
fi


###
# Main Execution
###

DOCKER_LABEL_ARGS=()
for i in "${!LABELS[@]}"; do
    DOCKER_LABEL_ARGS+=(--label)
    DOCKER_LABEL_ARGS+=("${LABELS[i]}")
done

formatlog "INFO" "Building RACE in the Box UI Image: race-in-the-box-ui:${RIB_VERSION}"
DOCKER_BUILDKIT=1 docker build \
    ${CACHE_ARG:+'--no-cache'} \
    --build-arg RIB_VERSION="${RIB_VERSION}" \
    -f "${FILE_DIR}/Dockerfile" \
    -t race-in-the-box-ui:"${RIB_VERSION}" \
    --cache-from race-in-the-box-ui:"${RIB_VERSION}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "${DOCKER_LABEL_ARGS[@]}" \
    "${FILE_DIR}"
formatlog "INFO" "Built image: race-in-the-box-ui:${RIB_VERSION}"

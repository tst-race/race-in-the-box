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

set -o errexit
set -o nounset
set -o pipefail

# shellcheck disable=SC1004
HELP=\
'
Prepare a physical Android device to connect to a deployment for real-world testing.

Note: Expected to be run outside of RiB. Script has no dependency on RiB.
Note: Assumes adb is installed.

Arguments:
    -a [value], --archive [value], --archive=[value]
        Android prepare archive generated by RiB.
    -s [value], --serial [value], --serial=[value]
        Android Device ID (adb get-serialno)
    -h, --help
        Print this message.

Examples:
    bash prepare_android_bridge_device.sh -h
    bash prepare_android_bridge_device.sh \
        --archive race-client-00004-device-prepare.tar.gz
    bash prepare_android_bridge_device.sh \
        --archive race-client-00004-device-prepare.tar.gz \
        --serial ABCD0123456789
'

while [ $# -gt 0 ]
do
    key="$1"

    case $key in

        -a|--archive)
        PREPARE_ARCHIVE="$2"
        shift
        shift
        ;;
        -a=*|--archive=*)
        PREPARE_ARCHIVE="${1#*=}"
        shift
        ;;

        -s|--serial)
        SERIAL="$2"
        shift
        shift
        ;;
        -s=*|--serial=*)
        SERIAL="${1#*=}"
        shift
        ;;

        -v|--race-version)
        RACE_VERSION="$2"
        shift
        shift
        ;;
        -v=*|--race-version=*)
        RACE_VERSION="${1#*=}"
        shift
        ;;

        -p|--vpn-profile)
        VPN_PROFILE="$2"
        shift
        shift
        ;;
        -p=*|--vpn-profile=*)
        VPN_PROFILE="${1#*=}"
        shift
        ;;


        -h|--help)
        printf "%s" "${HELP}"
        exit 1;
        ;;

        *)
        echo "$HELP"
        printf "unknown argument \"%s\"" "$1"
        exit 1
        ;;
    esac
done

if [ -z "${SERIAL:-}" ]
then
    SERIAL=$(adb get-serialno)
    echo "Only one Android device detected. Using it by default. Serial number $SERIAL"
fi

if [ -z "$PREPARE_ARCHIVE" ]
then
    echo "archive must be specified"
    exit 1
fi

PREPARE_ARCHIVE_EXTRACT_DIR="/tmp/android-device-${SERIAL}-prepare-files"
ARTIFACT_DOWNLOAD_DIR="/tmp/prepare_script_artifact_downloads"

# Clean up old runs.
rm -rf "$PREPARE_ARCHIVE_EXTRACT_DIR"
mkdir "$PREPARE_ARCHIVE_EXTRACT_DIR"
rm -rf $ARTIFACT_DOWNLOAD_DIR
mkdir $ARTIFACT_DOWNLOAD_DIR

tar xvf "$PREPARE_ARCHIVE" -C "$PREPARE_ARCHIVE_EXTRACT_DIR"

# Get the RACE version if it hasn't been set by the user.
if [ -z "${RACE_VERSION:-}" ]; then
  RACE_VERSION_FILE="${PREPARE_ARCHIVE_EXTRACT_DIR}/race_version.txt"
  if [ -f "$RACE_VERSION_FILE" ]; then
    RACE_VERSION="$(cat "$RACE_VERSION_FILE")"
  else
    echo "ERROR: failed to find RACE version file ${RACE_VERSION_FILE}. Please manually specify RACE version with the --race-version option."
    exit 1
  fi
fi
echo "Using RACE version $RACE_VERSION"

# Create the RACE directory on the device.
DEVICE_DOWNLOAD_DIR="/storage/self/primary/Download"
DEVICE_RACE_DIR="${DEVICE_DOWNLOAD_DIR}/race"
adb -s "$SERIAL" shell mkdir -p "$DEVICE_RACE_DIR"

# Push the OpenVPN profile.
# TODO: should this be optional?
DEVICE_VPN_PROFILE_PATH="${DEVICE_DOWNLOAD_DIR}/race.ovpn"
# If the user provided a VPN profile then use that. Otherwise use the profile in the archive.
if [ -n "${VPN_PROFILE:-}" ]; then
  LOCAL_VPN_PROFILE_PATH=$VPN_PROFILE
else
  LOCAL_VPN_PROFILE_PATH="${PREPARE_ARCHIVE_EXTRACT_DIR}/race.ovpn"
fi
if [ ! -f "$LOCAL_VPN_PROFILE_PATH" ]; then
  echo "ERROR: failed to find vpn profile: $LOCAL_VPN_PROFILE_PATH"
  exit 1
fi
adb -s "$SERIAL" push "$LOCAL_VPN_PROFILE_PATH" "$DEVICE_VPN_PROFILE_PATH"

# Install OpenVPN app.
OPEN_VPN_APK_URL="https://github.com/schwabe/ics-openvpn/releases/download/v0.7.33/ics-openvpn-0.7.33.apk"
wget --output-document=${ARTIFACT_DOWNLOAD_DIR}/ics-openvpn-0.7.33.apk $OPEN_VPN_APK_URL
adb -s "$SERIAL" install "${ARTIFACT_DOWNLOAD_DIR}/ics-openvpn-0.7.33.apk"
echo "Installed OpenVPN."

# Install RACE node daemon.
LOCAL_RACE_DAEMON_PATH="${PREPARE_ARCHIVE_EXTRACT_DIR}/plugins/core/race-daemon/race-daemon-android-debug.apk"
if [ ! -f "$LOCAL_RACE_DAEMON_PATH" ]; then
  echo "Could not find RACE node daemon app in archive."
fi
adb -s "$SERIAL" install -g -t "$LOCAL_RACE_DAEMON_PATH"

# Push configs.
LOCAL_CONFIG_ARCHIVE_PATH="${PREPARE_ARCHIVE_EXTRACT_DIR}/configs.tar.gz"
if [ -f "$LOCAL_CONFIG_ARCHIVE_PATH" ]; then
  DEST_CONFIG_PATH="${DEVICE_RACE_DIR}/configs.tar.gz"
  adb -s "$SERIAL" push "$LOCAL_CONFIG_ARCHIVE_PATH" "$DEST_CONFIG_PATH"

  # Install RACE app.
  LOCAL_RACE_APP_PATH="${PREPARE_ARCHIVE_EXTRACT_DIR}/plugins/core/race/race.apk"
  adb -s "$SERIAL" install -g -t "$LOCAL_RACE_APP_PATH"
else
  echo "Configs not found. Assuming this node is non-genesis."
fi

# Push etc.
DEST_ETC_PATH="${DEVICE_RACE_DIR}/etc"
adb -s "$SERIAL" shell mkdir -p $DEST_ETC_PATH
LOCAL_ETC_ARCHIVE_PATH="${PREPARE_ARCHIVE_EXTRACT_DIR}/etc"
adb -s "$SERIAL" push "${LOCAL_ETC_ARCHIVE_PATH}"/* $DEST_ETC_PATH

# Push plugins.
DEVICE_PLUGIN_DIR="${DEVICE_RACE_DIR}/artifacts"
adb -s "$SERIAL" shell mkdir -p $DEVICE_PLUGIN_DIR
for dir in "${PREPARE_ARCHIVE_EXTRACT_DIR}"/plugins/*/; do
  # Don't push the core apps.
  if [ "$(basename "$dir")" = "core" ]; then
    continue
  fi
  adb -s "$SERIAL" push "$dir" $DEVICE_PLUGIN_DIR
done

# Set deployment name.
DEPLOYMENT="$(cat "${PREPARE_ARCHIVE_EXTRACT_DIR}"/deployment.txt)"
adb -s "$SERIAL" shell setprop debug.RACE_DEPLOYMENT "$DEPLOYMENT"

# Set persona.
PERSONA="$(cat "${PREPARE_ARCHIVE_EXTRACT_DIR}"/persona.txt)"
adb -s "$SERIAL" shell setprop debug.RACE_PERSONA "$PERSONA"

# Set RACE encryption type.
ENCRYPTION_TYPE="$(cat "${PREPARE_ARCHIVE_EXTRACT_DIR}"/encryption_type.txt)"
adb -s "$SERIAL" shell setprop debug.RACE_ENCRYPTION_TYPE "$ENCRYPTION_TYPE"


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

# set -o errexit
set -o nounset
set -o pipefail


set -x

HELP=\
'
Unprepare a physical Android device that was prepared with prepare_android_bridge_device.sh.

Note: Expected to be run outside of RiB. Script has no dependency on RiB.
Note: Assumes adb is installed.

Arguments:
    -s [value], --serial [value], --serial=[value]
        Android Device ID (adb get-serialno)
    -h, --help
        Print this message.

Examples:
    bash unprepare_android_bridge_device.sh -h
    bash unprepare_android_bridge_device.sh
    bash unprepare_android_bridge_device.sh --serial ABCD0123456789
'

while [ $# -gt 0 ]
do
    key="$1"

    case $key in

        -s|--serial)
        SERIAL="$2"
        shift
        shift
        ;;
        -s=*|--serial=*)
        SERIAL="${1#*=}"
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

DEVICE_DOWNLOAD_DIR="/storage/self/primary/Download"
DEVICE_RACE_DIR="${DEVICE_DOWNLOAD_DIR}/race"

# Remove OpenVPN profile.
DEVICE_VPN_PROFILE_PATH="${DEVICE_DOWNLOAD_DIR}/race.ovpn"
adb -s "$SERIAL" shell rm -rf $DEVICE_VPN_PROFILE_PATH

# Unset deployment name.
adb -s "$SERIAL" shell setprop debug.RACE_DEPLOYMENT \"\"

# Unset persona.
adb -s "$SERIAL" shell setprop debug.RACE_PERSONA \"\"

# Unset RACE encryption type.
adb -s "$SERIAL" shell setprop debug.RACE_ENCRYPTION_TYPE \"\"

# Remove all RACE data.
adb -s "$SERIAL" shell rm -rf $DEVICE_RACE_DIR
adb -s "$SERIAL" shell rm -rf "${DEVICE_DOWNLOAD_DIR}/deployment.txt"
adb -s "$SERIAL" shell rm -rf "${DEVICE_DOWNLOAD_DIR}/daemon-state-info.json"

# Uninstall OpenVPN app.
OPENVPN_PACKAGE_ID="de.blinkt.openvpn"
adb -s "$SERIAL" shell pm uninstall --user 0 "$OPENVPN_PACKAGE_ID"

# Unistall RACE node daemon app.
RACE_DAEMON_PACKAGE_ID="com.twosix.race.daemon"
adb -s "$SERIAL" shell pm uninstall --user 0 "$RACE_DAEMON_PACKAGE_ID"

# Uninstall RACE app.
RACE_APP_PACKAGE_ID="com.twosix.race"
adb -s "$SERIAL" shell pm uninstall --user 0 "$RACE_APP_PACKAGE_ID"

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

"""
Purpose:
    Utilities for interacting with Android devices via adb
"""

# Python Library Imports
import logging
import os
import socket
from adbutils import AdbClient, AdbDevice, Property as AdbProperty
from functools import cached_property, wraps
from typing import Dict, List, Optional, TypedDict, Union

# Local Python Library Imports
from rib.config import rib_host_env
from rib.utils import error_utils, network_utils, rib_utils


logger = logging.getLogger(__name__)
adb_version = "1.0.41"


###
# Decorators
###


def catch_connection_error(func):
    """
    Purpose:
        Custom decorator to catch ConnectionErrors and turn them into RIBa01 errors
    Args:
        func: Function to be decorated
    Return:
        Decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except socket.error as err:
            raise error_utils.RIBa01(err) from None

    return wrapper


def fail_if_incompatible_adb(func):
    """
    Purpose:
        Custom decorator to check that the host ADB version is compatible before executing
        the decorated function
    Args:
        func: Function to be decorated
    Return:
        Decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not rib_host_env.get_rib_env_config()["adb_compatible"]:
            raise error_utils.RIBa00(adb_version)
        return func(*args, **kwargs)

    return wrapper


###
# Types
###


class AndroidDeviceInfo(TypedDict):
    """Relevant Device Info for adb connected device"""

    serial: str
    model: str
    architecture: str
    sdk_version: int
    release_version: int


class RaceAndroidDevice:
    """
    Purpose:
        The RaceAndroidDevice Class is a representation of a connected Android
        Device that will/does host the RACE system
    """

    ###
    # Class Attributes
    ###

    _DOWNLOAD_DIR = "/storage/self/primary/Download"
    _RACE_DIR = f"{_DOWNLOAD_DIR}/race"
    remote_race_plugins_base_dir = f"{_RACE_DIR}/artifacts"
    remote_vpn_profile_file = f"{_DOWNLOAD_DIR}/race.ovpn"

    daemon_package_id = "com.twosix.race.daemon"
    app_package_id = "com.twosix.race"
    vpn_package_id = "de.blinkt.openvpn"

    race_deployment_prop_key = "debug.RACE_DEPLOYMENT"
    race_persona_prop_key = "debug.RACE_PERSONA"
    race_encryption_type_prop_key = "debug.RACE_ENCRYPTION_TYPE"

    ###
    # Lifecycle Methods
    ###

    @catch_connection_error
    def __init__(self, adb_client: AdbClient, serial: str) -> None:
        """
        Purpose:
            Initialize the RaceAndroidDevice object.
        Args:
            adb_client: ADB client
            serial: Serial Number of the Device
        Returns:
            N/A
        """

        self.adb_client = adb_client
        self.adb_device = get_adb_device(adb_client, serial)

        self.serial = serial

    def __str__(self) -> str:
        """
        Purpose:
            Representation of the RaceAndroidDevice object.
        Args:
            N/A
        Returns:
            RaceAndroidDevice: String printable representation of RaceAndroidDevice
        """

        return (
            f"<RaceAndroidDevice ({self.race_persona_prop}): "
            f"{self.device_info['model']} - {self.serial}>"
        )

    def __repr__(self) -> str:
        """
        Purpose:
            Representation of the RaceAndroidDevice object.
        Args:
            N/A
        Returns:
            RaceAndroidDevice: String true representation of RaceAndroidDevice
        """

        return f"<RaceAndroidDevice: {self.device_info}>"

    ###
    # Properties
    ###

    @property
    @catch_connection_error
    def race_deployment_prop(self) -> bool:
        """RACE deployment property value"""
        return self.device_properties.get(self.race_deployment_prop_key, cache=False)

    @property
    @catch_connection_error
    def race_persona_prop(self) -> bool:
        """RACE persona property value"""
        return self.device_properties.get(self.race_persona_prop_key, cache=False)

    @property
    @catch_connection_error
    def race_encryption_type_prop(self) -> bool:
        """RACE encryption type property value"""
        return self.device_properties.get(
            self.race_encryption_type_prop_key, cache=False
        )

    @cached_property
    @catch_connection_error
    def device_properties(self) -> AdbProperty:
        """Android device properties"""
        return self.adb_device.prop

    @cached_property
    def device_info(self) -> AndroidDeviceInfo:
        """Android device info (typed subset of properties)"""
        return AndroidDeviceInfo(
            serial=self.device_properties.get("ro.serialno"),
            model=self.device_properties.get("ro.product.system.model"),
            architecture=self.device_properties.get("ro.product.cpu.abi"),
            sdk_version=int(self.device_properties.get("ro.build.version.sdk")),
            release_version=int(self.device_properties.get("ro.build.version.release")),
        )

    @property
    @catch_connection_error
    def app_installed(self) -> bool:
        """
        Purpose:
            Is the RACE application installed? check if com.twosix.race
            is installed in the packages list
        Args:
            N/A
        Return:
            app_installed
        """

        return self.adb_device.package_info(self.app_package_id) is not None

    @property
    @catch_connection_error
    def app_running(self) -> bool:
        """
        Purpose:
            Is the RACE application running? check if com.twosix.race
            is running on the device
        Args:
            N/A
        Return:
            app_installed
        """

        return bool(self._shell(["pidof", self.app_package_id]))

    @property
    @catch_connection_error
    def daemon_installed(self) -> bool:
        """
        Purpose:
            Is the RACE daemon installed? check if com.twosix.race.daemon
            is installed in the packages list
        Args:
            N/A
        Return:
            daemon_installed
        """

        return self.adb_device.package_info(self.daemon_package_id) is not None

    @property
    @catch_connection_error
    def daemon_running(self) -> bool:
        """
        Purpose:
            Is the RACE daemon running? check if com.twosix.race.daemon
            is running on the device
        Args:
            N/A
        Return:
            daemon_installed
        """

        return bool(self._shell(["pidof", self.daemon_package_id]))

    @property
    @catch_connection_error
    def vpn_profile_exists(self) -> bool:
        """Does the VPN profile configuration file exist on the device"""

        shell_output = self._shell(["ls", self.remote_vpn_profile_file])
        if "No such file or directory" in shell_output:
            return False
        else:
            return True

    @property
    @catch_connection_error
    def vpn_app_installed(self) -> bool:
        """
        Purpose:
            Is there an openvpn client installed on the phone?
        Args:
            N/A
        Return:
            vpn_app_installed
        """

        return self.adb_device.package_info(self.vpn_package_id) is not None

    @property
    @catch_connection_error
    def vpn_connected(self) -> bool:
        """Is the VPN connected (i.e. are rib services reachable)"""

        return "unknown host" not in self._shell(["ping", "-c", "1", "rib-file-server"])

    ###
    # Internal Helper Functions
    ###

    @catch_connection_error
    def _install(self, local_apk_path: str) -> None:
        """
        Purpose:
            Installs the given app apk on the device.

            We use the `install_remote` function instead of `install` because we need to
            set the flags used for the installation.
        """

        logger.debug(f"Installing {local_apk_path}")
        remote_apk_path = f"/data/local/tmp/{os.path.basename(local_apk_path)}"
        self._push(local_apk_path, remote_apk_path)
        # Install the APK with options:
        #   -t: allow test APKs to be installed
        #   -g: grant all permissions listed in app manifest
        # docs: https://developer.android.com/studio/command-line/adb#-t-option
        self.adb_device.install_remote(
            remote_path=remote_apk_path, clean=True, flags=["-g", "-t"]
        )

    @catch_connection_error
    def _push(self, src: str, dest: str) -> None:
        """
        Purpose:
            Recursively pushes the source directory onto the device
        Args:
            src: Local source directory
            dest: Remote destination directory
        Return:
            N/A
        """
        if os.path.isfile(src):
            # Important to note that we use sync.push instead of push so that it uses
            # the socket connection to the adb server, rather than making a subprocess
            # call to the adb executable
            self.adb_device.sync.push(src, dest)
        elif os.path.isdir(src):
            src = os.path.normpath(src)
            dest = os.path.normpath(dest)
            for src_root, dirs, files in os.walk(src):
                dest_root = src_root.replace(src, dest)
                for dir in dirs:
                    self._shell(["mkdir", "-p", os.path.join(dest_root, dir)])
                for name in files:
                    self._push(
                        os.path.join(src_root, name), os.path.join(dest_root, name)
                    )
        else:
            # NOTE: this is intentionally _not_ a RiB error since it _should_ only be seen in development.
            raise Exception(f"unable to find source file: {src}")

    @catch_connection_error
    def _shell(self, cmd: Union[str, list, tuple], *args, **kwargs) -> str:
        """
        Purpose:
            Execute shell command on the device
        Args:
            cmd: Command to be executed
            args: Positional arguments to AdbDevice.shell
            kwargs: Keyword arguments to AdbDevice.shell
        Return:
            Shell command output
        """
        logger.trace(f"Executing {cmd} on device {self.serial}")
        output = self.adb_device.shell(cmd, *args, **kwargs)
        logger.trace(f"Output: {output}")
        return output

    ###
    # Inspection/status/verification Functions
    ###

    @catch_connection_error
    def verify_compatible_with_race(self, supported_architectures: List[str]) -> None:
        """
        Purpose:
            Verifies that the Android device meets all criteria in order to run the RACE
            application.
        Args:
            supported_architectures: List of supported architectures
        Return:
            N/A
        Raises:
            error_utils.RIBa01 if device is not compatible
        """

        if self.device_info["sdk_version"] < 29:
            raise error_utils.RIBa03(
                serial=self.serial,
                reason=(
                    f"Android SDK version is {self.device_info['sdk_version']} but "
                    "29 or higher is required"
                ),
            )
        if self.device_info["architecture"] not in supported_architectures:
            raise error_utils.RIBa03(
                serial=self.serial,
                reason=(
                    f"Device architecture {self.device_info['architecture']} is not "
                    f"supported, only {' or '.join(supported_architectures)} are supported"
                ),
            )

    def get_preparation_status_report(
        self,
        include_race_app_installation: bool = True,
        include_vpn_app_installation: bool = True,
    ) -> Dict[str, bool]:
        """
        Purpose:
            Creates a device preparation status report
        Args:
            include_race_app_installation: Whether to include the installation of the RACE client app
            include_vpn_app_installation: Whether to include the installation of the VPN client app
        Return:
            Dictionary of preparation status checks to values
        """
        report = {
            "VPN profile exists": self.vpn_profile_exists,
            "RACE daemon installed": self.daemon_installed,
            "RACE deployment set": bool(self.race_deployment_prop),
            "RACE persona set": bool(self.race_persona_prop),
        }
        if include_race_app_installation:
            report["RACE client installed"] = self.app_installed
        if include_vpn_app_installation:
            report["VPN client installed"] = self.vpn_app_installed
        return report

    ###
    # Install Functions
    ###

    @catch_connection_error
    def install_race_daemon(self, local_daemon_apk: str) -> None:
        """
        Purpose:
            Install the RACE Daemon application on the device
        Args:
            local_daemon_apk: Local path to the daemon apk
        Return:
            N/A
        """

        self._install(local_daemon_apk)

    @catch_connection_error
    def install_race_app(self, local_app_apk: str) -> None:
        """
        Purpose:
            Install the RACE application on the device
        Args:
            local_app_apk: Local path to the RACE client apk
        Return:
            N/A
        """

        self._install(local_app_apk)

    @catch_connection_error
    def install_vpn_app(self) -> None:
        """
        Purpose:
            Install the OpenVPN client application on the device
        Args:
            N/A
        Return:
            N/A
        """

        self._install(get_openvpn_for_android_apk())

    @catch_connection_error
    def push_vpn_profile(self, local_vpn_profile_file: str) -> None:
        """
        Purpose:
            Push the given VPN profile configuration file onto the device
        Args:
            local_vpn_profile_file: VPN profile configuration file
        Return:
            N/A
        """

        logger.debug(
            f"Pushing {local_vpn_profile_file} to {self.remote_vpn_profile_file}"
        )
        self._push(local_vpn_profile_file, self.remote_vpn_profile_file)

    @catch_connection_error
    def push_artifacts(self, local_artifact_dir: str) -> None:
        """
        Purpose:
            Push RACE plugin artifacts onto the device
        Args:
            local_artifact_dir: Local plugin artifact directory path
        Return:
            N/A
        """

        self._shell(f"mkdir -p {self.remote_race_plugins_base_dir}")

        for ta in ("network-manager", "comms", "artifact-manager"):
            local_plugin_artifact_dir = f"{local_artifact_dir}/{ta}"
            remote_plugin_artifact_dir = f"{self.remote_race_plugins_base_dir}/{ta}"
            if os.path.exists(local_plugin_artifact_dir):
                logger.debug(
                    f"Pushing {local_plugin_artifact_dir} to {remote_plugin_artifact_dir}"
                )
                self._push(local_plugin_artifact_dir, remote_plugin_artifact_dir)

    @catch_connection_error
    def push_configs(self, local_config_bundle: str) -> None:
        """
        Purpose:
            Push RACE plugin configs onto the device.
        Args:
            local_config_bundle: Local plugin config bundle path.
        """

        dest_file_name = f"{self._RACE_DIR}/configs.tar.gz"
        logger.debug(f"Pushing {local_config_bundle} to {dest_file_name}")
        self._push(local_config_bundle, dest_file_name)

    @catch_connection_error
    def push_etc(self, etc_src_dir: str) -> None:
        """
        Purpose:
            Push RACE /etc/ files onto the device.
        Args:
            etc_src_dir: Local /etc/ file path.
        """

        dest_dir = f"{self._RACE_DIR}/etc"
        logger.debug(f"Pushing {etc_src_dir} to {dest_dir}")
        self._push(etc_src_dir, dest_dir)

    ###
    # Uninstall Functions
    ###

    def remove_vpn_profile(self) -> None:
        """
        Purpose:
            Removes the remote VPN file from the device
        Args:
            N/A
        Return:
            N/A
        """

        logger.debug(f"Removing {self.remote_vpn_profile_file}")
        self._shell(["rm", "-rf", self.remote_vpn_profile_file])

    def uninstall_race_daemon(self) -> None:
        """
        Purpose:
            Uninstalls the RACE node daemon application from the device
        Args:
            N/A
        Return:
            N/A
        """

        logger.debug(f"Uninstalling {self.daemon_package_id}")
        self.adb_device.uninstall(self.daemon_package_id)

    def uninstall_race_app(self) -> None:
        """
        Purpose:
            Uninstalls the RACE client application from the device
        Args:
            N/A
        Return:
            N/A
        """

        logger.debug(f"Uninstalling {self.app_package_id}")
        self.adb_device.uninstall(self.app_package_id)

    def remove_race_data(self) -> None:
        """
        Purpose:
            Removes all RACE data from the device
        Args:
            N/A
        Return:
            N/A
        """

        def _rm(path: str) -> None:
            self._shell(["rm", "-r", path])

        _rm(self._RACE_DIR)
        # NOTE: The two files (deployment.txt and daemon-state-info.json) are created
        # by the node daemon. We remove them here, instead of relying on the daemon to
        # clean them up, to assure that they definitely get deleted, e.g. if the daemon
        # crashes.
        # TODO: consider moving these files from the download directory to app specific
        # storage so that they get deleted automatically when deleting the RACE app.
        _rm(f"{self._DOWNLOAD_DIR}/deployment.txt")
        _rm(f"{self._DOWNLOAD_DIR}/daemon-state-info.json")

    ###
    # Property Functions
    ###

    def set_race_deployment(self, name: str) -> None:
        """
        Purpose:
            Set the RACE deployment property to the given value
        Args:
            name: RACE deployment name
        Return:
            N/A
        """

        self._shell(["setprop", self.race_deployment_prop_key, name])

    def unset_race_deployment(self) -> None:
        """
        Purpose:
            Unset the RACE deployment property on the device
        Args:
            N/A
        Return:
            N/A
        """

        self._shell(["setprop", self.race_deployment_prop_key, ""])

    def set_race_persona(self, persona: str) -> None:
        """
        Purpose:
            Set the RACE persona property to the given value
        Args:
            persona: RACE node persona
        Return:
            N/A
        """

        self._shell(["setprop", self.race_persona_prop_key, persona])

    def unset_race_persona(self) -> None:
        """
        Purpose:
            Unset the RACE persona property on the device
        Args:
            N/A
        Return:
            N/A
        """

        self._shell(["setprop", self.race_persona_prop_key, ""])

    def set_race_encryption_type(self, encryption_type: str) -> None:
        """
        Purpose:
            Set the RACE encryption type property to the given value
        Args:
            encryption_type: RACE encryption type, either "ENC_NONE" or "ENC_AES"
        """

        self._shell(["setprop", self.race_encryption_type_prop_key, encryption_type])

    def unset_race_encryption_type(self) -> None:
        """
        Purpose:
            Unset the RACE encryption type property on the device
        """

        self._shell(["setprop", self.race_encryption_type_prop_key, ""])

    ###
    # Command Functions
    ###

    def start_race_daemon(self) -> None:
        """
        Purpose:
            Starts the RACE node daemon application on the device
        Args:
            N/A
        Return:
            N/A
        """

        self.adb_device.app_start(self.daemon_package_id, ".MainActivity")

    def stop_race_daemon(self) -> None:
        """
        Purpose:
            Stops the RACE node daemon application on the device
        Args:
            N/A
        Return:
            N/A
        """

        self.adb_device.app_stop(self.daemon_package_id)

    def stop_race_app(self) -> None:
        """
        Purpose:
            Stops the RACE client application on the device
        Args:
            N/A
        Return:
            N/A
        """

        self.adb_device.app_stop(self.app_package_id)

    def connect_vpn(self) -> None:
        """
        Purpose:
            Connects to the deployment VPN by instructing the RACE node daemon to
            import and start the VPN profile. The RACE node daemon uses an AIDL
            remote service to interact with the OpenVPN client application.
        Args:
            N/A
        Return:
            N/A
        """

        self._shell(
            [
                "am",
                "start",
                "-n",
                f"{self.daemon_package_id}/.VpnActivity",
                "-a",
                "com.twosix.race.daemon.CONNECT_VPN",
                "--es",
                "vpn-profile-file",
                self.remote_vpn_profile_file,
            ]
        )

    def disconnect_vpn(self) -> None:
        """
        Purpose:
            Disconnects from the deployment VPN
        Args:
            N/A
        Return:
            N/A
        """

        self._shell(
            [
                "am",
                "start",
                "-n",
                f"{self.daemon_package_id}/.VpnActivity",
                "-a",
                "com.twosix.race.daemon.DISCONNECT_VPN",
            ]
        )

    def set_daemon_as_device_owner(self) -> None:
        """
        Purpose:
            Set the daemon the device owner so it can perform silent installs
        Args:
            N/A
        Return:
            N/A
        """
        logger.debug("Setting daemon as device owner")
        self._shell(
            [
                "dpm",
                "set-device-owner",
                f"{self.daemon_package_id}/.AdminReceiver",
            ]
        )

    def remove_daemon_as_device_owner(self) -> None:
        """
        Purpose:
            Remove the daemon as the device owner.
        Args:
            N/A
        Return:
            N/A
        """
        logger.debug("Removing daemon as device owner")
        self._shell(
            [
                "dpm",
                "remove-active-admin",
                f"{self.daemon_package_id}/.AdminReceiver",
            ]
        )

    def disable_play_protect(self) -> None:
        """
        Purpose:
            Disable Play Protect so RACE app can be installed without any prompts to the user.
        Args:
            N/A
        Return:
            N/A
        """
        self._shell(
            [
                "settings",
                "put",
                "global",
                "package_verifier_user_consent",
                "-1",
            ]
        )

    def enable_play_protect(self) -> None:
        """
        Purpose:
            Enable Play Protect
        Args:
            N/A
        Return:
            N/A
        """
        self._shell(
            [
                "settings",
                "put",
                "global",
                "package_verifier_user_consent",
                "1",
            ]
        )


###
# Functions
###


def create_adb_client(
    host: str = "host.docker.internal",
    port: int = 5037,
) -> AdbClient:
    """
    Purpose:
        Creates an instance of an ADB client
    Args:
        host: Hostname of the ADB server
        port: Port on the ADB server
    Returns:
        ADB client
    """
    # This does not raise if the ADB server isn't running
    return AdbClient(host=host, port=port)


@catch_connection_error
def get_adb_device(adb_client: AdbClient, serial: str) -> AdbDevice:
    """
    Purpose:
        Obtains the device identified by the given serial number
    Args:
        adb_client: ADB client
        serial: Android device serial number
    Returns:
        Android device
    """
    try:
        device = adb_client.device(serial)
        device.prop.name  # make sure device is valid
        return device
    except:
        raise error_utils.RIBa02(
            serial, [device.serial for device in get_android_devices(adb_client)]
        ) from None


@catch_connection_error
def get_android_devices(adb_client: AdbClient) -> List[AdbDevice]:
    """
    Purpose:
        Gets the serial numbers for all connected Android devices
    Args:
        adb_client: ADB client
    Returns:
        List of device serial numbers
    """
    return adb_client.device_list()


def get_default_android_device_serial(adb_client: AdbClient) -> Optional[str]:
    """
    Purpose:
        Gets the serial number of the connected Android device, if there is only one
        Android device present
    Args:
        adb_client: ADB client
    Returns:
        Android device serial number if only one device exists, else None
    """
    devices = get_android_devices(adb_client)
    if len(devices) == 1:
        return devices.pop().serial
    return None


def get_openvpn_for_android_apk() -> str:
    """
    Purpose:
        Returns the path to the OpenVPN for Android apk file, downloading it
        if it is not already downloaded
    Args:
        N/A
    Returns:
        Path to OpenVPN for Android apk file
    """
    rib_config = rib_utils.load_race_global_configs()
    version = rib_config.OPENVPN_FOR_ANDROID_VERSION
    local_apk_path = os.path.join(
        rib_config.RIB_PATHS["docker"]["cache"], f"openvpn-for-android-{version}.apk"
    )

    if not os.path.exists(local_apk_path):
        logger.info("Downloading OpenVPN for Android...")
        network_utils.download_file(
            remote_url="https://github.com/schwabe/ics-openvpn/releases/download/v0.7.33/ics-openvpn-0.7.33.apk",
            local_path=local_apk_path,
        )
    else:
        logger.debug("Using cached OpenVPN for Android")

    return local_apk_path

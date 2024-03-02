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
    Tests for adb_utils.py
"""

# Python Library Imports
import adbutils
import pytest
from unittest.mock import MagicMock, call, create_autospec, patch

# Local Python Library Imports
from rib.utils import adb_utils, error_utils


###
# Fixtures
###


@pytest.fixture(autouse=True)
@patch("rib.utils.adb_utils.create_adb_client")
def adb_client(create_adb_client) -> adbutils.AdbClient:
    mock_client = create_autospec(adbutils.AdbClient)
    create_adb_client.return_value = mock_client
    return mock_client


@pytest.fixture
def adb_property() -> adbutils.Property:
    mock_property = adbutils.Property(None)
    mock_property.get = MagicMock()
    return mock_property


@pytest.fixture
def adb_sync() -> adbutils.Sync:
    return create_autospec(adbutils.Sync)


@pytest.fixture
def adb_device(adb_property, adb_sync) -> adbutils.AdbDevice:
    mock_device = create_autospec(adbutils.AdbDevice)
    mock_device.serial = "test-serial"
    mock_device.prop = adb_property
    mock_device.sync = adb_sync
    return mock_device


@pytest.fixture
@patch("rib.utils.adb_utils.get_adb_device")
def android_device(
    get_adb_device, adb_client, adb_device
) -> adb_utils.RaceAndroidDevice:
    get_adb_device.return_value = adb_device
    return adb_utils.RaceAndroidDevice(adb_client, "test-serial")


###
# catch_connection_error
###


def test_catch_connection_error_when_no_error():
    func = MagicMock(return_value="return value")
    decorated = adb_utils.catch_connection_error(func)
    assert "return value" == decorated("pos arg", keyword_arg="keyword value")
    func.assert_called_once_with("pos arg", keyword_arg="keyword value")


def test_catch_connection_error_when_socket_error():
    func = MagicMock(side_effect=ConnectionError)
    decorated = adb_utils.catch_connection_error(func)
    with pytest.raises(error_utils.RIBa01):
        decorated()


def test_catch_connection_error_when_other_error():
    func = MagicMock(side_effect=KeyError)
    decorated = adb_utils.catch_connection_error(func)
    with pytest.raises(KeyError):
        decorated()


###
# fail_if_incompatible_adb
###


@patch(
    "rib.config.rib_host_env.get_rib_env_config",
    MagicMock(return_value={"adb_compatible": True}),
)
def test_fail_if_incompatible_adb_when_compatible():
    func = MagicMock(return_value="return value")
    decorated = adb_utils.fail_if_incompatible_adb(func)
    assert "return value" == decorated("pos arg", keyword_arg="keyword value")
    func.assert_called_once_with("pos arg", keyword_arg="keyword value")


@patch(
    "rib.config.rib_host_env.get_rib_env_config",
    MagicMock(return_value={"adb_compatible": False}),
)
def test_fail_if_incompatible_adb_when_not_compatible():
    func = MagicMock()
    decorated = adb_utils.fail_if_incompatible_adb(func)
    with pytest.raises(error_utils.RIBa00):
        decorated()


###
# get_adb_device
###


def test_get_adb_device_when_valid(adb_client, adb_device):
    adb_client.device.return_value = adb_device
    assert adb_device == adb_utils.get_adb_device(adb_client, "test-serial")


def test_get_adb_device_when_invalid(adb_client, adb_device):
    adb_client.device.return_value = adb_device
    adb_device.prop.get.side_effect = ConnectionError
    with pytest.raises(error_utils.RIBa02):
        adb_utils.get_adb_device(adb_client, "test-serial")


###
# get_default_android_device_serial
###


def test_get_default_android_device_serial_when_no_devices(adb_client):
    adb_client.device_list.return_value = []
    assert adb_utils.get_default_android_device_serial(adb_client) is None


def test_get_default_android_device_serial_when_multiple_devices(
    adb_client, adb_device
):
    adb_client.device_list.return_value = [adb_device, adb_device]
    assert adb_utils.get_default_android_device_serial(adb_client) is None


def test_get_default_android_device_serial_when_one_device(adb_client, adb_device):
    adb_client.device_list.return_value = [adb_device]
    assert adb_utils.get_default_android_device_serial(adb_client) == "test-serial"


###
# get_openvpn_for_android_apk
###


@patch("os.path.exists", MagicMock(return_value=False))
@patch("rib.utils.network_utils.download_file")
@patch("rib.utils.rib_utils.load_race_global_configs")
def test_get_openvpn_for_android_apk_when_not_cached(
    load_race_global_configs,
    download_file,
):
    mock_rib_config = MagicMock()
    mock_rib_config.OPENVPN_FOR_ANDROID_VERSION = "x.y.z"
    mock_rib_config.RIB_PATHS = {"docker": {"cache": "/rib/cache"}}
    load_race_global_configs.return_value = mock_rib_config

    assert (
        "/rib/cache/openvpn-for-android-x.y.z.apk"
        == adb_utils.get_openvpn_for_android_apk()
    )
    download_file.assert_called_once()


@patch("os.path.exists", MagicMock(return_value=True))
@patch("rib.utils.network_utils.download_file")
@patch("rib.utils.rib_utils.load_race_global_configs")
def test_get_openvpn_for_android_apk_when_cached(
    load_race_global_configs, download_file
):
    mock_rib_config = MagicMock()
    mock_rib_config.OPENVPN_FOR_ANDROID_VERSION = "x.y.z"
    mock_rib_config.RIB_PATHS = {"docker": {"cache": "/rib/cache"}}
    load_race_global_configs.return_value = mock_rib_config

    assert (
        "/rib/cache/openvpn-for-android-x.y.z.apk"
        == adb_utils.get_openvpn_for_android_apk()
    )
    download_file.assert_not_called()


###
# RaceAndroidDevice.race_deployment_prop
###


def test_RaceAndroidDevice_race_deployment_prop(android_device, adb_property):
    adb_property.get.return_value = "deployment name"
    assert "deployment name" == android_device.race_deployment_prop
    adb_property.get.assert_called_once_with("debug.RACE_DEPLOYMENT", cache=False)


###
# RaceAndroidDevice.race_persona_prop
###


def test_RaceAndroidDevice_race_persona_prop(android_device, adb_property):
    adb_property.get.return_value = "persona"
    assert "persona" == android_device.race_persona_prop
    adb_property.get.assert_called_once_with("debug.RACE_PERSONA", cache=False)


###
# RaceAndroidDevice.device_info
###


def test_RaceAndroidDevice_device_info(android_device, adb_property):
    device_properties = {
        "ro.serialno": "serial number",
        "ro.product.system.model": "model type",
        "ro.product.cpu.abi": "arch type",
        "ro.build.version.sdk": "1234",
        "ro.build.version.release": "2468",
    }
    adb_property.get.side_effect = lambda x: device_properties.get(x, "")
    assert android_device.device_info == {
        "serial": "serial number",
        "model": "model type",
        "architecture": "arch type",
        "sdk_version": 1234,
        "release_version": 2468,
    }


###
# RaceAndroidDevice.app_installed
###


@pytest.mark.parametrize("package_info, expected", [(None, False), ({}, True)])
def test_RaceAndroidDevice_app_installed(
    package_info, expected, android_device, adb_device
):
    adb_device.package_info.return_value = package_info
    assert expected == android_device.app_installed
    adb_device.package_info.assert_called_once_with("com.twosix.race")


###
# RaceAndroidDevice.app_running
###


@pytest.mark.parametrize("shell_out, expected", [("", False), ("1234", True)])
def test_RaceAndroidDevice_app_running(shell_out, expected, android_device, adb_device):
    adb_device.shell.return_value = shell_out
    assert expected == android_device.app_running
    adb_device.shell.assert_called_once_with(["pidof", "com.twosix.race"])


###
# RaceAndroidDevice.daemon_installed
###


@pytest.mark.parametrize("package_info, expected", [(None, False), ({}, True)])
def test_RaceAndroidDevice_daemon_installed(
    package_info, expected, android_device, adb_device
):
    adb_device.package_info.return_value = package_info
    assert expected == android_device.daemon_installed
    adb_device.package_info.assert_called_once_with("com.twosix.race.daemon")


###
# RaceAndroidDevice.daemon_running
###


@pytest.mark.parametrize("shell_out, expected", [("", False), ("1234", True)])
def test_RaceAndroidDevice_daemon_running(
    shell_out, expected, android_device, adb_device
):
    adb_device.shell.return_value = shell_out
    assert expected == android_device.daemon_running
    adb_device.shell.assert_called_once_with(["pidof", "com.twosix.race.daemon"])


###
# RaceAndroidDevice.vpn_profile_exists
###


@pytest.mark.parametrize(
    "shell_out, expected", [("file", True), ("No such file or directory", False)]
)
def test_RaceAndroidDevice_vpn_profile_exists(
    shell_out, expected, android_device, adb_device
):
    adb_device.shell.return_value = shell_out
    assert expected == android_device.vpn_profile_exists
    adb_device.shell.assert_called_once_with(
        ["ls", "/storage/self/primary/Download/race.ovpn"]
    )


###
# RaceAndroidDevice.vpn_app_installed
###


@pytest.mark.parametrize("package_info, expected", [(None, False), ({}, True)])
def test_RaceAndroidDevice_vpn_app_installed(
    package_info, expected, android_device, adb_device
):
    adb_device.package_info.return_value = package_info
    assert expected == android_device.vpn_app_installed
    adb_device.package_info.assert_called_once_with("de.blinkt.openvpn")


###
# RaceAndroidDevice.vpn_connected
###


@pytest.mark.parametrize(
    "shell_out, expected",
    [
        ("rib-file-server.rib-overlay-network 11.22.33.44", True),
        ("unknown host", False),
    ],
)
def test_RaceAndroidDevice_vpn_connected(
    shell_out, expected, android_device, adb_device
):
    adb_device.shell.return_value = shell_out
    assert expected == android_device.vpn_connected
    adb_device.shell.assert_called_once_with(["ping", "-c", "1", "rib-file-server"])


###
# RaceAndroidDevice._push
###


@patch("os.path.isfile", MagicMock(return_value=True))
def test_RaceAndroidDevice__push_file(android_device):
    android_device._push("/src/file.txt", "/dest/file.txt")
    android_device.adb_device.sync.push.assert_called_once_with(
        "/src/file.txt", "/dest/file.txt"
    )


@pytest.mark.parametrize(
    "src, dest",
    [("/src/", "/dest/"), ("/src", "/dest/"), ("/src/", "/dest"), ("/src", "/dest")],
)
@patch("os.path.isfile", MagicMock(side_effect=lambda x: "file.txt" in x))
@patch("os.path.isdir", MagicMock(return_value=True))
@patch("os.walk", MagicMock(return_value=[("/src/dir", ["subdir"], ["file.txt"])]))
def test_RaceAndroidDevice__push_dir(src, dest, android_device):
    android_device._push(src, dest)
    android_device.adb_device.shell.assert_called_once_with(
        ["mkdir", "-p", "/dest/dir/subdir"]
    )
    android_device.adb_device.sync.push.assert_called_once_with(
        "/src/dir/file.txt", "/dest/dir/file.txt"
    )


###
# RaceAndroidDevice.verify_compatible_with_race
###


@pytest.mark.parametrize(
    "sdk_version, architecture, supported_archs, expected",
    [
        (28, "x86_64", ["x86_64"], False),
        (29, "x86_64", ["x86_64"], True),
        (30, "x86_64", ["x86_64"], True),
        (29, "arm64-v7a", ["x86_64", "arm64-v8a"], False),
        (29, "arm64-v8a", ["x86_64", "arm64-v8a"], True),
        (29, "x86_64", ["x86_64", "arm64-v8a"], True),
    ],
)
def test_RaceAndroidDevice_verify_compatible_with_race(
    sdk_version, architecture, supported_archs, expected, android_device
):
    android_device.device_info = dict(
        sdk_version=sdk_version, architecture=architecture
    )
    if expected:
        android_device.verify_compatible_with_race(supported_archs)
    else:
        with pytest.raises(error_utils.RIBa03):
            android_device.verify_compatible_with_race(supported_archs)


###
# RaceAndroidDevice.get_preparation_status_report
###


def test_RaceAndroidDevice_get_preparation_status_report(android_device):
    report = android_device.get_preparation_status_report()
    assert "VPN profile exists" in report
    assert "VPN client installed" in report
    assert "RACE daemon installed" in report
    assert "RACE client installed" in report
    assert "RACE deployment set" in report
    assert "RACE persona set" in report

    assert "RACE client installed" not in android_device.get_preparation_status_report(
        include_race_app_installation=False
    )

    assert "VPN client installed" not in android_device.get_preparation_status_report(
        include_vpn_app_installation=False
    )


###
# RaceAndroidDevice.install_race_daemon
###


@patch("os.path.isfile", MagicMock(return_value=True))
def test_RaceAndroidDevice_install_race_daemon(android_device):
    android_device.install_race_daemon("/apps/daemon.apk")
    android_device.adb_device.sync.push.assert_called_once_with(
        "/apps/daemon.apk", "/data/local/tmp/daemon.apk"
    )
    android_device.adb_device.install_remote.assert_called_once_with(
        "/data/local/tmp/daemon.apk", clean=True, flags=["-g", "-t"]
    )


###
# RaceAndroidDevice.install_race_app
###


@patch("os.path.isfile", MagicMock(return_value=True))
def test_RaceAndroidDevice_install_race_app(android_device):
    android_device.install_race_app("/apps/race.apk")
    android_device.adb_device.sync.push.assert_called_once_with(
        "/apps/race.apk", "/data/local/tmp/race.apk"
    )
    android_device.adb_device.install_remote.assert_called_once_with(
        "/data/local/tmp/race.apk", clean=True, flags=["-g", "-t"]
    )


###
# RaceAndroidDevice.install_vpn_app
###


@patch("os.path.isfile", MagicMock(return_value=True))
@patch(
    "rib.utils.adb_utils.get_openvpn_for_android_apk",
    MagicMock(return_value="/apps/vpn.apk"),
)
def test_RaceAndroidDevice_install_vpn_app(android_device):
    android_device.install_vpn_app()
    android_device.adb_device.sync.push.assert_called_once_with(
        "/apps/vpn.apk", "/data/local/tmp/vpn.apk"
    )
    android_device.adb_device.install_remote.assert_called_once_with(
        "/data/local/tmp/vpn.apk", clean=True, flags=["-g", "-t"]
    )


###
# RaceAndroidDevice.push_vpn_profile
###


@patch("os.path.isfile", MagicMock(return_value=True))
def test_RaceAndroidDevice_push_vpn_profile(android_device):
    android_device.push_vpn_profile("/configs/race.ovpn")
    android_device.adb_device.sync.push.assert_called_once_with(
        "/configs/race.ovpn", "/storage/self/primary/Download/race.ovpn"
    )


###
# RaceAndroidDevice.push_artifacts
###


@patch("os.path.exists", MagicMock(side_effect=[True, False, True]))
def test_RaceAndroidDevice_push_artifacts(android_device):
    android_device._push = MagicMock()
    android_device.push_artifacts("/plugins")
    assert android_device._push.call_args_list == [
        call(
            "/plugins/network-manager",
            "/storage/self/primary/Download/race/artifacts/network-manager",
        ),
        call(
            "/plugins/artifact-manager",
            "/storage/self/primary/Download/race/artifacts/artifact-manager",
        ),
    ]


###
# RaceAndroidDevice.remove_vpn_profile
###


def test_RaceAndroidDevice_remove_vpn_profile(android_device):
    android_device.remove_vpn_profile()
    android_device.adb_device.shell.assert_called_once_with(
        ["rm", "-rf", "/storage/self/primary/Download/race.ovpn"]
    )


###
# RaceAndroidDevice.uninstall_race_daemon
###


def test_RaceAndroidDevice_uninstall_race_daemon(android_device):
    android_device.uninstall_race_daemon()
    android_device.adb_device.uninstall.assert_called_once_with(
        "com.twosix.race.daemon"
    )


###
# RaceAndroidDevice.uninstall_race_app
###


def test_RaceAndroidDevice_uninstall_race_app(android_device):
    android_device.uninstall_race_app()
    android_device.adb_device.uninstall.assert_called_once_with("com.twosix.race")


###
# RaceAndroidDevice.remove_race_data
###


def test_RaceAndroidDevice_remove_race_data(android_device):
    android_device.remove_race_data()
    assert android_device.adb_device.shell.call_args_list == [
        call(["rm", "-r", "/storage/self/primary/Download/race"]),
        call(["rm", "-r", "/storage/self/primary/Download/deployment.txt"]),
        call(["rm", "-r", "/storage/self/primary/Download/daemon-state-info.json"]),
    ]


###
# RaceAndroidDevice.set_race_deployment
###


def test_RaceAndroidDevice_set_race_deployment(android_device):
    android_device.set_race_deployment("deployment name")
    android_device.adb_device.shell.assert_called_once_with(
        ["setprop", "debug.RACE_DEPLOYMENT", "deployment name"]
    )


###
# RaceAndroidDevice.unset_race_deployment
###


def test_RaceAndroidDevice_unset_race_deployment(android_device):
    android_device.unset_race_deployment()
    android_device.adb_device.shell.assert_called_once_with(
        ["setprop", "debug.RACE_DEPLOYMENT", ""]
    )


###
# RaceAndroidDevice.set_race_persona
###


def test_RaceAndroidDevice_set_race_persona(android_device):
    android_device.set_race_persona("persona")
    android_device.adb_device.shell.assert_called_once_with(
        ["setprop", "debug.RACE_PERSONA", "persona"]
    )


###
# RaceAndroidDevice.unset_race_persona
###


def test_RaceAndroidDevice_unset_race_persona(android_device):
    android_device.unset_race_persona()
    android_device.adb_device.shell.assert_called_once_with(
        ["setprop", "debug.RACE_PERSONA", ""]
    )


###
# RaceAndroidDevice.start_race_daemon
###


def test_RaceAndroidDevice_start_race_daemon(android_device):
    android_device.start_race_daemon()
    android_device.adb_device.app_start.assert_called_once_with(
        "com.twosix.race.daemon", ".MainActivity"
    )


###
# RaceAndroidDevice.stop_race_daemon
###


def test_RaceAndroidDevice_stop_race_daemon(android_device):
    android_device.stop_race_daemon()
    android_device.adb_device.app_stop.assert_called_once_with("com.twosix.race.daemon")


###
# RaceAndroidDevice.stop_race_app
###


def test_RaceAndroidDevice_stop_race_app(android_device):
    android_device.stop_race_app()
    android_device.adb_device.app_stop.assert_called_once_with("com.twosix.race")


###
# RaceAndroidDevice.connect_vpn
###


def test_RaceAndroidDevice_connect_vpn(android_device):
    android_device.connect_vpn()
    android_device.adb_device.shell.assert_called_once_with(
        [
            "am",
            "start",
            "-n",
            "com.twosix.race.daemon/.VpnActivity",
            "-a",
            "com.twosix.race.daemon.CONNECT_VPN",
            "--es",
            "vpn-profile-file",
            "/storage/self/primary/Download/race.ovpn",
        ]
    )


###
# RaceAndroidDevice.disconnect_vpn
###


def test_RaceAndroidDevice_disconnect_vpn(android_device):
    android_device.disconnect_vpn()
    android_device.adb_device.shell.assert_called_once_with(
        [
            "am",
            "start",
            "-n",
            "com.twosix.race.daemon/.VpnActivity",
            "-a",
            "com.twosix.race.daemon.DISCONNECT_VPN",
        ]
    )


###
# RaceAndroidDevice.set_daemon_as_device_owner
###


def test_RaceAndroidDevice_set_daemon_as_device_owner(android_device):
    android_device.set_daemon_as_device_owner()
    android_device.adb_device.shell.assert_called_once_with(
        [
            "dpm",
            "set-device-owner",
            "com.twosix.race.daemon/.AdminReceiver",
        ]
    )


###
# RaceAndroidDevice.remove_daemon_as_device_owner
###


def test_RaceAndroidDevice_remove_daemon_as_device_owner(android_device):
    android_device.remove_daemon_as_device_owner()
    android_device.adb_device.shell.assert_called_once_with(
        [
            "dpm",
            "remove-active-admin",
            "com.twosix.race.daemon/.AdminReceiver",
        ]
    )


###
# RaceAndroidDevice.disable_play_protect
###


def test_RaceAndroidDevice_disable_play_protect(android_device):
    android_device.disable_play_protect()
    android_device.adb_device.shell.assert_called_once_with(
        [
            "settings",
            "put",
            "global",
            "package_verifier_user_consent",
            "-1",
        ]
    )


###
# RaceAndroidDevice.enable_play_protect
###


def test_RaceAndroidDevice_enable_play_protect(android_device):
    android_device.enable_play_protect()
    android_device.adb_device.shell.assert_called_once_with(
        [
            "settings",
            "put",
            "global",
            "package_verifier_user_consent",
            "1",
        ]
    )

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
    Deployment bridge command groups are responsible for configuring and interacting with
    bridged RACE node devices
"""

# Python Library Imports
import click
import logging

# Local Python Library Imports
from rib.commands.common_options import timeout_option
from rib.commands.deployment_options import deployment_name_option, pass_rib_mode
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import adb_utils, error_utils


logger = logging.getLogger(__name__)


###
# Option Decorators
###


def android_serial_option(group: click.Group = click):
    """
    Purpose:
        Custom option decorator for the Android device serial number.
    Args:
        group: Optional parent group
    Returns:
        Function decorator
    """

    def get_default():
        """Get default Android device serial number, if one exists"""
        return adb_utils.get_default_android_device_serial(
            adb_utils.create_adb_client()
        )

    def wrapper(function):
        return group.option(
            "--serial",
            default=get_default,
            help="Android device serial number",
            type=str,
        )(function)

    return wrapper


###
# Bridged Commands
###


@click.group("bridged")
def bridged_command_group() -> None:
    """Commands for manipulating bridged devices"""


###
# Bridged Android Commands
###


@bridged_command_group.group("android")
def android_command_group() -> None:
    """Commands for manipulating bridged Android devices (physical or emulated)"""


@android_command_group.command("list")
@adb_utils.fail_if_incompatible_adb
def list_android() -> None:
    """
    List available Android devices that can be prepared
    """

    devices = adb_utils.get_android_devices(adb_utils.create_adb_client())
    if not devices:
        click.echo("No Android Devices Found")
    else:
        click.echo("Android Devices:")
        for device in devices:
            click.echo(f"\t{device.serial}: {device.prop.model}")


@android_command_group.command("info")
@android_serial_option()
@adb_utils.fail_if_incompatible_adb
def info_android(serial: str) -> None:
    """
    Report info for an Android device
    """

    device = adb_utils.RaceAndroidDevice(
        adb_client=adb_utils.create_adb_client(),
        serial=serial,
    )
    click.echo(f"Info for Android Device: {serial}")
    click.echo(f"\tDevice Info:")
    for key in sorted(device.device_info.keys()):
        click.echo(f"\t\t{key}={device.device_info[key]}")
    click.echo(f"\tVPN Client App Installed: {device.vpn_app_installed}")
    click.echo(f"\tVPN Profile Exists: {device.vpn_profile_exists}")
    click.echo(f"\tVPN Connected: {device.vpn_connected}")
    click.echo(f"\tRACE Daemon Installed: {device.daemon_installed}")
    click.echo(f"\tRACE Daemon Running: {device.daemon_running}")
    click.echo(f"\tRACE Client Installed: {device.app_installed}")
    click.echo(f"\tRACE Client Running: {device.app_running}")
    click.echo(
        f"\tRACE Deployment Property: {device.race_deployment_prop or '<not-set>'}"
    )
    click.echo(f"\tRACE Persona Property: {device.race_persona_prop or '<not-set>'}")


@android_command_group.command("status")
@android_serial_option()
@adb_utils.fail_if_incompatible_adb
def status_android(serial: str) -> None:
    """
    Report bridged operation status for an Android device
    """

    device = adb_utils.RaceAndroidDevice(
        adb_client=adb_utils.create_adb_client(),
        serial=serial,
    )
    report = device.get_preparation_status_report()
    if all(report.values()):
        click.echo(f"Android device {serial} is ready for bridged operations")
        return
    elif any(report.values()):
        click.echo(f"Android device {serial} is partially ready for bridged operations")
    else:
        click.echo(f"Android device {serial} is not ready for bridged operations")

    for key in sorted(report.keys()):
        click.echo(f"\t{key}: {report[key]}")


@android_command_group.command("prepare")
@deployment_name_option("prepare bridged Android device")
@click.option(
    "--persona",
    help="RACE node persona to prepare the device to run as",
    required=True,
    type=str,
)
@click.option(
    "--allow-silent-installs",
    flag_value=True,
    help="Enable fully-automatic RACE app installation when bootstrapping",
)
@click.option(
    "--push-configs",
    flag_value=True,
    help="Push configs during prepare instead of relying on daemon to download them",
)
@click.option(
    "--no-daemon",
    flag_value=True,
    help="Do NOT install the RACE node daemon on the device",
)
@android_serial_option()
@pass_rib_mode
@adb_utils.fail_if_incompatible_adb
def prepare_android(
    rib_mode: str,
    deployment_name: str,
    persona: str,
    allow_silent_installs: bool,
    push_configs: bool,
    no_daemon: bool,
    serial: str,
) -> None:
    """
    Prepare Android device to run as a RACE node
    """

    logger.info(f"Preparing Android device {serial} to run as {persona}")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    deployment.prepare_bridged_android_device(
        persona=persona,
        serial=serial,
        allow_silent_installs=allow_silent_installs,
        push_configs=push_configs,
        install_daemon=not no_daemon,
    )

    logger.info(f"Prepared Android device {serial} to run as {persona}")


@android_command_group.command("prepare-archive")
@deployment_name_option("prepare archive for pushing to a bridged Android device")
@click.option(
    "--persona",
    help="RACE node persona to prepare the archive for",
    required=True,
    type=str,
)
@click.option(
    "--overwrite",
    help="Overwrite any existing archive",
    flag_value=True,
)
@pass_rib_mode
@click.option(
    "--architecture",
    default="arm64-v8a",
    required=False,
    type=click.Choice(["x86_64", "arm64-v8a"]),
    help="Architecture of node that will use this prepare archive",
)
def prepare_android_archive(
    rib_mode: str,
    deployment_name: str,
    persona: str,
    overwrite: bool,
    architecture: str,
) -> None:
    """
    Prepare archive for Android device to run as a RACE node
    """

    logger.info(f"Preparing Android device archive for {persona}")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    archive_path = deployment.prepare_bridged_android_device_archive(
        persona=persona, architecture=architecture, overwrite=overwrite
    )

    logger.info(f"Prepared Android device archive for {persona} here: {archive_path}")


@android_command_group.command("connect")
@deployment_name_option("connect bridged Android device")
@android_serial_option()
@timeout_option()
@pass_rib_mode
@adb_utils.fail_if_incompatible_adb
def connect_android(
    rib_mode: str,
    deployment_name: str,
    serial: str,
    timeout: int,
) -> None:
    """
    Connect bridged Android device into deployment
    """

    logger.info(f"Connecting Android device {serial}")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    deployment.connect_bridged_android_device(serial=serial, timeout=timeout)

    logger.info(f"Connected Android device {serial}")


@android_command_group.command("disconnect")
@deployment_name_option("disconnect bridged Android device")
@android_serial_option()
@timeout_option()
@pass_rib_mode
@adb_utils.fail_if_incompatible_adb
def disconnect_android(
    rib_mode: str,
    deployment_name: str,
    serial: str,
    timeout: int,
) -> None:
    """
    Disconnect bridged Android device from deployment
    """

    logger.info(f"Disconnecting Android device {serial}")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    deployment.disconnect_bridged_android_device(serial=serial, timeout=timeout)

    logger.info(f"Disconnected Android device {serial}")


@android_command_group.command("unprepare")
@deployment_name_option("unprepare bridged Android device")
@android_serial_option()
@pass_rib_mode
@adb_utils.fail_if_incompatible_adb
def unprepare_android(
    rib_mode: str,
    deployment_name: str,
    serial: str,
) -> None:
    """
    Unprepare Android device from running as a RACE node
    """

    logger.info(f"Unpreparing Android device {serial}")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    deployment.unprepare_bridged_android_device(serial=serial)

    logger.info(f"Unprepared Android device {serial}")

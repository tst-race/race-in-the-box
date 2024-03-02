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
        Environment Class for host machine. Will hold information about the host machine (set 
        automatically, not by the user of the tool). Allows RiB to enforce compatibility requirments
"""

# Python Library Imports
import logging
import os
import re
import subprocess
from pydantic import BaseModel
from typing import Dict, Optional, get_type_hints
from typing_extensions import TypedDict

# Local Python Library Imports
from rib.utils.general_utils import Subscriptable

logger = logging.getLogger(__name__)

###
# RiB Host Env Config Class
###


class RibHostEnvConfig(BaseModel, Subscriptable):
    """RiB Host Machine Information"""

    host_os: str
    platform: str
    docker_engine_version: str
    systemd_version: str
    gpu_support: bool
    adb_support: bool
    adb_compatible: bool
    dev_kvm_support: bool


class RibCapabilityReport(TypedDict):
    """Information about a RiB capability"""

    is_supported: bool
    reason: Optional[str]
    # Example of a nested capability is Android support with architectures as children
    children: Optional[Dict[str, "RibCapabilityReport"]]


def get_rib_env_config() -> RibHostEnvConfig:
    """
    Purpose:
        Get specific RibHostEnvConfig instance

        This method will use environment variables set in the entrypoint
        script to store information about the host machine
    Args:
        N/A
    Returns:
        RIB_HOST_ENV_CONFIG (RibHostEnvConfig Obj): Object containing information
        about the host machine
    """
    docker_version_check_cmd = [
        "docker",
        "version",
        "--format",
        "'{{.Server.Version}}'",
    ]
    try:
        docker_version_check_output = subprocess.run(
            docker_version_check_cmd, check=True, capture_output=True
        )
        docker_engine_version = (
            re.search("'(.*)'", str(docker_version_check_output.stdout))
        ).group(1)
    except:
        docker_engine_version = "unknown"

    config = RibHostEnvConfig(
        host_os=os.environ.get("HOST_UNAME", "unknown"),
        platform=os.environ.get("HOST_ARCHITECTURE", "unknown"),
        docker_engine_version=docker_engine_version,
        systemd_version=os.environ.get("HOST_SYSTEMCTL", "unknown"),
        gpu_support=False,
        adb_support=os.environ.get("HOST_HAS_ADB_SUPPORT", "false") == "true",
        adb_compatible=os.environ.get("HOST_HAS_COMPATIBLE_ADB", "false") == "true",
        dev_kvm_support=os.environ.get("HOST_HAS_DEV_KVM", "false") == "true",
    )
    return config


def get_rib_capabilities_report() -> Dict[str, RibCapabilityReport]:
    """
    Purpose:
        Get report of RiB Capabilities based on Host machine info
    Args:
        N/A
    Returns:
        overall_capabilities (Dict[str, RibCapabilityReport]): Dict containing capability name
        to RibCapabilityReport
    """
    rib_env_config = get_rib_env_config()

    overall_capabilities: Dict[str, RibCapabilityReport] = {}

    get_local_deployment_capability_report(rib_env_config, overall_capabilities)
    get_android_capability_report(rib_env_config, overall_capabilities)

    return overall_capabilities


rib_host_env_config_schema = {
    "type": "object",
    "properties": {
        "host_os": {"type": "string"},
        "platform": {"type": "string"},
        "docker_engine_version": {"type": "string"},
        "systemd_version": {"type": "string"},
        "gpu_support": {"type": "boolean"},
        "adb_support": {"type": "boolean"},
        "adb_compatible": {"type": "boolean"},
        "dev_kvm_support": {"type": "boolean"},
    },
    "required": list(get_type_hints(RibHostEnvConfig).keys()),
}

##
# Checks for RiB capabilties
##


def get_local_deployment_capability_report(
    rib_env_config: RibHostEnvConfig, parent_capability: Dict[str, RibCapabilityReport]
) -> None:
    """
    Purpose:
        Get report of Local Deployment Capabilities

        Requires Systemd version <= 247 on Linux
    Args:
        rib_env_config (RibHostEnvConfig): Information about the host machine
        parent_capability (Dict[str, RibCapabilityReport]): Dictionary to place new cability report
    Returns:
        N/A
    """

    local_deployments_capability = RibCapabilityReport(is_supported=True)
    parent_capability["Local Deployments"] = local_deployments_capability

    # Main check for this capability
    if rib_env_config["host_os"] == "Linux":
        if int(rib_env_config["systemd_version"]) > 247:
            local_deployments_capability["is_supported"] = False
            local_deployments_capability[
                "reason"
            ] = "RACE requires systemctl version <= 247"

    # Get Child Capabilities
    local_deployments_capability["children"] = {}
    get_gpu_capability_report(rib_env_config, local_deployments_capability["children"])


def get_gpu_capability_report(
    rib_env_config: RibHostEnvConfig, parent_capability: Dict[str, RibCapabilityReport]
) -> None:
    """
    Purpose:
        Get report of Local GPU Deployment Capabilities

        Currently only checks based on OS.
        TODO: Update to add checks for the proper drivers
    Args:
        rib_env_config (RibHostEnvConfig): Information about the host machine
        parent_capability (Dict[str, RibCapabilityReport]): Dictionary to place new cability report
    Returns:
        N/A
    """

    gpu_deployments_capability = RibCapabilityReport(is_supported=True)
    parent_capability["GPU Deployments"] = gpu_deployments_capability

    # Main check for this capability
    # TODO this can be broken into OS and drivers check
    if not rib_env_config["gpu_support"]:
        gpu_deployments_capability["is_supported"] = False
        gpu_deployments_capability[
            "reason"
        ] = "GPU deployments require drivers installed on a Linux host machine"


def get_android_capability_report(
    rib_env_config: RibHostEnvConfig, parent_capability: Dict[str, RibCapabilityReport]
) -> None:
    """
    Purpose:
        Get report of Android Capabilities

        Android capabilities include Android in Docker and Android Bridge mode
    Args:
        rib_env_config (RibHostEnvConfig): Information about the host machine
        parent_capability (Dict[str, RibCapabilityReport]): Dictionary to place new cability report
    Returns:
        N/A
    """

    android_capability = RibCapabilityReport(is_supported=True)
    parent_capability["Android"] = android_capability

    # Main check for this capability
    # EMPTY on purpose, Android capabilities don't role up

    # Get Child Capabilities
    android_capability["children"] = {}
    get_android_bridge_mode_capability_report(
        rib_env_config, android_capability["children"]
    )
    get_android_in_docker_capability_report(
        rib_env_config, android_capability["children"]
    )

    is_android_supported = False
    for report in android_capability["children"].values():
        if report["is_supported"]:
            is_android_supported = True
    android_capability["is_supported"] = is_android_supported


def get_android_bridge_mode_capability_report(
    rib_env_config: RibHostEnvConfig, parent_capability: Dict[str, RibCapabilityReport]
) -> None:
    """
    Purpose:
        Get report of Android Bridge Mode capability

        Android Bridge Mode requires that adb is installed on the host machine
    Args:
        rib_env_config (RibHostEnvConfig): Information about the host machine
        parent_capability (Dict[str, RibCapabilityReport]): Dictionary to place new cability report
    Returns:
        N/A
    """

    android_bridge_mode_capability = RibCapabilityReport(is_supported=True)
    parent_capability["Android Bridge Mode"] = android_bridge_mode_capability

    # TODO this can be broken into OS and drivers check
    if not rib_env_config["adb_support"]:
        android_bridge_mode_capability["is_supported"] = False
        android_bridge_mode_capability["reason"] = "Android Bridge Mode requires ADB"
    elif not rib_env_config["adb_compatible"]:
        android_bridge_mode_capability["is_supported"] = False
        android_bridge_mode_capability["reason"] = "ADB version is not compatible"


def get_android_in_docker_capability_report(
    rib_env_config: RibHostEnvConfig, parent_capability: Dict[str, RibCapabilityReport]
) -> None:
    """
    Purpose:
        Get report of Android in Docker capability

        Android in Docker requires dev kvm support on the host machine
    Args:
        rib_env_config (RibHostEnvConfig): Information about the host machine
        parent_capability (Dict[str, RibCapabilityReport]): Dictionary to place new cability report
    Returns:
        N/A
    """

    android_in_docker_capability = RibCapabilityReport(is_supported=True)
    parent_capability["Android in Docker"] = android_in_docker_capability

    if not rib_env_config["dev_kvm_support"]:
        android_in_docker_capability["is_supported"] = False
        android_in_docker_capability[
            "reason"
        ] = "Android in docker requires dev kvm support"

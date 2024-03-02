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
        System Utilities for interacting with the system that the user is running
        RiB on
"""

# Python Library Imports
import click
import docker
import platform
import psutil
from typing import Any, Dict

###
# Verification Functions
###


def verify_system_requirements(system_requirements: Dict[str, Any]) -> None:
    """
    Purpose:
        Verify System Requirements, will print if the system is valid or not
    Args:
        system_requirements (Dict): Dict of the system requirements for the system from
        the RACE config
    Return:
        N/A
    """

    click.echo("Verify the System is capable of running RiB")

    user_os_system = platform.system()
    user_os = system_requirements["supported_systems"].get(user_os_system, None)
    if not user_os:
        click.echo(f"{user_os_system} not supported")
        click.echo(
            f"Supported Systems are: "
            f"{', '.join(system_requirements['supported_systems'].keys())}"
        )
        return

    system_valid = False
    if user_os == "mac":
        system_valid = verify_mac_requirements(system_requirements)
    elif user_os == "linux":
        system_valid = verify_linux_requirements(system_requirements)
    elif user_os == "windows":
        system_valid = verify_windows_requirements(system_requirements)

    if system_valid:
        click.echo(f"System Meets Requirements")
    else:
        click.echo(f"System Does not Meet Requirements")


###
# OS Specific Checks
###


def verify_mac_requirements(system_requirements: Dict[str, Any]) -> bool:
    """
    Purpose:
        Verify Mac System Requirements
    Args:
        system_requirements (Dict): Dict of the system requirements for the system from
        the RACE config
    Return:
        system_valid (Boolean): whether or not the system is meets requirements
    """

    system_valid = True

    click.echo("Verifying Requirements of Mac System to run RiB")

    # Get Docker Client
    docker_client = docker.from_env()
    docker_resource_info = docker_client.info()

    # Check CPUs
    num_cpus = docker_resource_info["NCPU"]
    if num_cpus < system_requirements["min_docker_cpu"]:
        click.echo(
            f"System does not have enough CPUs ({num_cpus} < "
            f"{system_requirements['min_docker_cpu']})"
        )
        system_valid = False

    # Check Memory
    memory_bytes = docker_resource_info["MemTotal"]
    memory_gigabytes = memory_bytes / 1024.0 / 1024.0 / 1024.0
    if memory_gigabytes < system_requirements["min_docker_memory_gig"]:
        click.echo(
            f"System does not have enough Memory ({memory_gigabytes} <"
            f" {system_requirements['min_docker_memory_gig']})"
        )
        system_valid = False

    return system_valid


def verify_linux_requirements(system_requirements: Dict[str, Any]) -> bool:
    """
    Purpose:
        Verify Linux System Requirements
    Args:
        system_requirements: Dict of the system requirements for the system from
            the RACE config in the form of:
            {
                "min_docker_cpu": 4.0,
                "min_docker_memory_gig": 4.0,
            }
    Return:
        system_valid (Boolean): whether or not the system is meets requirements
    """

    system_valid = True

    click.echo("Verifying Requirements of Linux System to run RiB")

    # Get Docker Client
    docker_client = docker.from_env()
    docker_resource_info = docker_client.info()

    # Check CPUs
    num_cpus = docker_resource_info["NCPU"]
    if num_cpus < system_requirements["min_docker_cpu"]:
        click.echo(
            f"System does not have enough CPUs ({num_cpus} < "
            f"{system_requirements['min_docker_cpu']})"
        )
        system_valid = False

    # Check Memory
    memory_bytes = docker_resource_info["MemTotal"]
    memory_gigabytes = memory_bytes / 1024.0 / 1024.0 / 1024.0
    if memory_gigabytes < system_requirements["min_docker_memory_gig"]:
        click.echo(
            f"System does not have enough Memory ({memory_gigabytes} <"
            f" {system_requirements['min_docker_memory_gig']})"
        )
        system_valid = False

    return system_valid


def verify_windows_requirements(system_requirements: Dict[str, Any]) -> bool:
    """
    Purpose:
        Verify Windows System Requirements
    Args:
        system_requirements (Dict): Dict of the system requirements for the system from
        the RACE config
    Return:
        system_valid (Boolean): whether or not the system is meets requirements
    """

    system_valid = True

    click.echo("Verifying Requirements of Windows System to run RiB")

    click.echo("TODO")
    system_valid = False

    return system_valid


###
# System Information
###


def get_cpu_count() -> int:
    """
    Purpose:
        Get the CPU count of the system
    Args:
        N/A
    Return:
        cpu_count: number of cores
    """

    return psutil.cpu_count()


def get_memory_bytes() -> int:
    """
    Purpose:
        Get the Memory (In Bytes) of the system
    Args:
        N/A
    Return:
        memory_bytes: total available memory in bytes
    """

    return dict(psutil.virtual_memory()._asdict()).get("total", 0)

#!/usr/bin/env python3

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
        Test File for system_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
from unittest import mock
from mock import patch
from typing import Any, Dict

# Local Library Imports
from rib.utils import system_utils


###
# Mocks/Fixtures
###


def get_mock_system_values_unix(cpu: int, ram_gb: float) -> Dict[str, Any]:
    """
    Purpose:
        Return a dict of the structure expected to be returned form
        docker on a unix like system (mac/linux)
    Args:
        cpu: count CPUs
        ram_mb: count GB of RAM
    Returns:
        system_values: settings of the system
    """

    return {"NCPU": cpu, "MemTotal": ram_gb * 1024.0 * 1024.0 * 1024.0}  # in bytes


def get_mock_system_values_windows(cpu: int, ram_gb: float) -> None:
    """
    Purpose:
        Return a dict of the structure expected to be returned form
        docker for a system
    Args:
        cpu: count CPUs
        ram_mb: count GB of RAM
    Returns:
        system_values: settings of the system
    """

    # TODO, how to get this?

    return {}


class MockDockerClient:
    """
    Purpose:
        A mock docker client that will return value we expect
    Args:
        N/A
    """

    def __init__(self, cpu: int, ram_mb: float, system_type: str) -> None:
        """
        Purpose:
            Initalize the object
        Args:
            N/A
        Returns:
            N/A
        """

        if system_type == "windows":
            self.system_values = get_mock_system_values_windows(cpu, ram_mb)
        else:
            self.system_values = get_mock_system_values_unix(cpu, ram_mb)

    def info(self) -> Dict[str, Any]:
        """
        Purpose:
            Get system information from the client
        Args:
            N/A
        Returns:
            info: information about the system
        """

        return self.system_values


###
# Test Functions
###


#######
# verify_mac_requirements()
#######


def test_verify_mac_requirements_passes():
    """
    Purpose:
        Test that verify_mac_requirements passes with good settings
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (passing)
    system_cpu = 5
    system_ram_gb = 5.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "unix"
        )

        is_system_valid = system_utils.verify_mac_requirements(system_requirements)

    assert is_system_valid


def test_verify_mac_requirements_fails_ram():
    """
    Purpose:
        Test that verify_mac_requirements fails with not enough ram
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (failing ram)
    system_cpu = 5
    system_ram_gb = 1.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "unix"
        )

        is_system_valid = system_utils.verify_mac_requirements(system_requirements)

    assert not is_system_valid


def test_verify_mac_requirements_fails_cpu():
    """
    Purpose:
        Test that verify_mac_requirements fails with not enough ram
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (failing ram)
    system_cpu = 1
    system_ram_gb = 5.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "unix"
        )

        is_system_valid = system_utils.verify_mac_requirements(system_requirements)

    assert not is_system_valid


#######
# verify_linux_requirements()
#######


def test_verify_linux_requirements_passes():
    """
    Purpose:
        Test that verify_linux_requirements passes with good settings
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (passing)
    system_cpu = 5
    system_ram_gb = 5.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "unix"
        )

        is_system_valid = system_utils.verify_linux_requirements(system_requirements)

    assert is_system_valid


def test_verify_linux_requirements_fails_ram():
    """
    Purpose:
        Test that verify_linux_requirements fails with not enough ram
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (failing ram)
    system_cpu = 5
    system_ram_gb = 1.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "unix"
        )

        is_system_valid = system_utils.verify_linux_requirements(system_requirements)

    assert not is_system_valid


def test_verify_linux_requirements_fails_cpu():
    """
    Purpose:
        Test that verify_linux_requirements fails with not enough ram
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (failing ram)
    system_cpu = 1
    system_ram_gb = 5.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "unix"
        )

        is_system_valid = system_utils.verify_linux_requirements(system_requirements)

    assert not is_system_valid


#######
# verify_windows_requirements()
#######


def test_verify_windows_requirements_fails_always():
    """
    Purpose:
        Test that verify_windows_requirements fails always as it's not yet supported
    Args:
        N/A
    """

    # Threshold to pass
    system_requirements = {"min_docker_cpu": 4.0, "min_docker_memory_gig": 4.0}

    # Values we will return (does not affect the pass/fail)
    system_cpu = 5
    system_ram_gb = 5.0

    with patch("docker.from_env") as mock_docker_from_env:
        mock_docker_from_env.return_value = MockDockerClient(
            system_cpu, system_ram_gb, "windows"
        )

        is_system_valid = system_utils.verify_windows_requirements(system_requirements)

    assert not is_system_valid


#######
# get_cpu_count()
#######


def test_get_cpu_count():
    """
    Purpose:
        Test that get_cpu_count uses the same lib and returns
        expected value
    Args:
        N/A
    """

    expected_cpu_count = 2

    # Mock getting CPU count from system
    with patch("psutil.cpu_count") as mock_cpu_count:
        mock_cpu_count.return_value = expected_cpu_count
        returned_cpu_count = system_utils.get_cpu_count()

    assert returned_cpu_count == expected_cpu_count

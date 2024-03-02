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
        Test File for docker_compose_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
import requests
from unittest.mock import MagicMock
from unittest import mock
from mock import patch

# Local Library Imports
from rib.utils import docker_compose_utils


###
# Mocks/Data Fixtures
###


# None at the Moment


###
# Test Cases
###


################################################################################
# run_docker_compose_up
################################################################################


def test_run_docker_compose_up() -> int:
    """
    Purpose:
        Test run_docker_compose_up works
    Args:
        N/A
    """

    # Assert method works
    with patch("pexpect.spawn", MagicMock()) as pexpect_mock:
        docker_compose_utils.run_docker_compose_up(
            deployment_name="test",
            deployment_mode="local",
            docker_compose_file="test.yml",
            env={"test": "test"},
            services=["test"],
            timeout=100,
            verbosity=2,
        )

        assert pexpect_mock.call_count == 1
        assert (
            pexpect_mock.call_args.args[0]
            == "docker-compose --file=test.yml up -d test"
        )
        assert pexpect_mock.call_args.kwargs == {
            "env": {"test": "test"},
            "timeout": 100,
        }


################################################################################
# run_docker_compose_stop
################################################################################


def test_run_docker_compose_stop() -> int:
    """
    Purpose:
        Test run_docker_compose_stop works
    Args:
        N/A
    """

    # Assert method works
    with patch("pexpect.spawn", MagicMock()) as pexpect_mock:
        docker_compose_utils.run_docker_compose_stop(
            deployment_name="test",
            docker_compose_file="test.yml",
            env={"test": "test"},
            services=["test"],
            timeout=100,
            verbosity=2,
        )

        assert pexpect_mock.call_count == 1
        assert (
            pexpect_mock.call_args.args[0] == "docker-compose --file=test.yml stop test"
        )
        assert pexpect_mock.call_args.kwargs == {
            "env": {"test": "test"},
            "timeout": 100,
        }


################################################################################
# run_docker_compose_remove
################################################################################


def test_run_docker_compose_remove() -> int:
    """
    Purpose:
        Test run_docker_compose_remove works
    Args:
        N/A
    """

    # Assert method works
    with patch("pexpect.spawn", MagicMock()) as pexpect_mock:
        docker_compose_utils.run_docker_compose_remove(
            deployment_name="test",
            docker_compose_file="test.yml",
            env={"test": "test"},
            services=["test"],
            timeout=100,
            verbosity=2,
        )

        assert pexpect_mock.call_count == 1
        assert (
            pexpect_mock.call_args.args[0]
            == "docker-compose --file=test.yml rm --force test"
        )
        assert pexpect_mock.call_args.kwargs == {
            "env": {"test": "test"},
            "timeout": 100,
        }

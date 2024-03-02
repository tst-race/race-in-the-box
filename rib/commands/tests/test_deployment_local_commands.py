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
        Test File for deployment_local_commands.py
"""

# Python Library Imports
import pytest
from mock import patch
from unittest.mock import MagicMock

# Local Library Imports
from rib.commands import deployment_local_commands
from rib.utils import error_utils

###
# Fixtures / Mocks
###


# N/A


###
# Tests
###


#########
# verify_gpu_settings
#########


def verify_gpu_settings_linux_enabled() -> int:
    """
    Purpose:
        Check `verify_gpu_settings()` works when valid
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("os.environ") as env_mock, patch(
        "sys.exit"
    ) as exit_mock:
        env_mock = {"HOST_UNAME": "Linux"}
        deployment_local_commands.verify_gpu_settings(True, "local")
        assert abort_mock.call_count == 0
        assert exit_mock.call_count == 0


def verify_gpu_settings_mac_enabled_local() -> int:
    """
    Purpose:
        Check `verify_gpu_settings()` works on mac and local deployment (fails)
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("os.environ") as env_mock, patch(
        "sys.exit"
    ) as exit_mock:
        env_mock = {"HOST_UNAME": "Darwin"}
        deployment_local_commands.verify_gpu_settings(True, "local")
        assert abort_mock.call_count == 1
        assert exit_mock.call_count == 1


def verify_gpu_settings_mac_enabled_mac_aws_enabled() -> int:
    """
    Purpose:
        Check `verify_gpu_settings()` works on mac and local deployment (succeeds)
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("os.environ") as env_mock, patch(
        "sys.exit"
    ) as exit_mock:
        env_mock = {"HOST_UNAME": "Darwin"}
        deployment_local_commands.verify_gpu_settings(True, "aws")
        assert abort_mock.call_count == 0
        assert exit_mock.call_count == 0


def verify_gpu_settings_mac_enabled_unknown_local_enabled() -> int:
    """
    Purpose:
        Check `verify_gpu_settings()` works on unknown os and local deployment (faiuls)
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("os.environ") as env_mock, patch(
        "sys.exit"
    ) as exit_mock:
        env_mock = {"HOST_UNAME": "Unknown"}
        deployment_local_commands.verify_gpu_settings(True, "local")
        assert abort_mock.call_count == 1
        assert exit_mock.call_count == 1

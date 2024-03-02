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
        Test File for aws_commands.py
"""

# Python Library Imports
import os
import sys
import pytest
from click.testing import CliRunner
from mock import patch
from unittest import mock

# Local Library Imports
from rib.utils import error_utils
from rib.commands import aws_commands


###
# Mocks
###


# N/A


###
# Data Fixtures
###


# N/A


###
# Mocked Functions
###


# N/A


###
# Test Commands
###


#########
# verify
#########


def test_verify_command_succeeds():
    """
    Purpose:
        Test that `rib aws verify` succeeds when the profile is good
    Args:
        N/A
    """

    # Run verify_aws_profile()
    with patch("rib.utils.aws_utils.verify_aws_profile") as verify_aws_profile:
        verify_aws_profile.return_value = None

        # Configure Runner
        command_runner = CliRunner()

        # Run Test
        command_result = command_runner.invoke(aws_commands.verify)

    assert command_result.exception is None


def test_verify_command_fails():
    """
    Purpose:
        Test that `rib aws verify` fails when cloudformation is missing
    Args:
        N/A
    """

    # Run verify_aws_profile() expecting failure
    with patch("rib.utils.aws_utils.verify_aws_profile") as verify_aws_profile:
        verify_aws_profile.side_effect = error_utils.RIB702(["cloudformation"])

        # Configure Runner
        command_runner = CliRunner()

        # Run Test
        command_result = command_runner.invoke(aws_commands.verify)

    assert type(command_result.exception) == error_utils.RIB702


#########
# info
#########


def test_info_command():
    """
    Purpose:
        Test that `rib aws info` returns the profile info
    Args:
        N/A
    """

    # Run Generate Config
    with patch("rib.utils.aws_utils.get_aws_profile_information") as get_info_patch:
        get_info_patch.return_value = {"profile_name": "default"}

        # Configure Runner
        command_runner = CliRunner()

        # Run Test
        command_result = command_runner.invoke(aws_commands.info)

    assert "profile_name: default" in command_result.output
    assert command_result.exception is None

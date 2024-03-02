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
        Test File for config_commands.py
"""

# Python Library Imports
import os
import sys
import pytest
from click.testing import CliRunner
from unittest import mock

# Local Library Imports
from rib.utils import error_utils
from rib.commands import config_commands


###
# Mocks
###


class MockConfig(object):
    """
    Purpose:
        Mock for the rib_config
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            initialize MockConfig
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        pass


class MockCliContextObj(object):
    """
    Purpose:
        Mock for the cli_context.obj
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            initialize MockCliContextObj
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        # Base Config Option
        self.config = MockConfig()

        # User State File
        self.user_state_file = "/tmp/user_state_file.json"

        # Race Mode
        self.rib_mode = kwargs.get("rib_mode", None)

        # Verbosity
        self.verbosity = 0

        # Mock Args
        self.invalid_user_state = kwargs.get("invalid_user_state", False)
        self.missing_state = kwargs.get("missing_state", False)

    def verify_rib_state(self):
        """
        Purpose:
            Mock verify_rib_state
        Args:
            N/A
        Returns:
            N/A
        """

        if self.invalid_user_state:
            raise error_utils.RIB203("User State File Not Found")
        elif self.missing_state:
            raise error_utils.RIB004()
        else:
            pass


###
# Data Fixtures
###


@pytest.fixture()
def mocked_cli_context_obj():
    """
    Purpose:
        Fixture of a Mocked CLI Context Object
    Args:
        N/A
    Return:
        mocked_cli_context_obj (String): Mocked CLI Context Object
    """

    return MockCliContextObj()


###
# Mocked Functions
###


# None at the Moment (Empty Test Suite)


###
# Test Commands
###


def test_verify_command_user_state_correct():
    """
    Purpose:
        Test that `rib config verify` passes when state is correct
    Args:
        N/A
    """

    # Setup CLI Context Obj
    mock_cli_context_obj = MockCliContextObj()

    # Configure Runner
    command_runner = CliRunner()

    # Run Test
    command_result = command_runner.invoke(
        config_commands.verify, obj=mock_cli_context_obj
    )

    # Assert Expected Output
    assert command_result.exit_code == 0
    assert "Verify RiB Config" in command_result.output
    assert "RiB Config Verified" in command_result.output


def test_verify_command_user_state_undefined():
    """
    Purpose:
        Test that `rib config verify` fails when when cannot find user state
    Args:
        N/A
    """

    # Setup CLI Context Obj
    mock_cli_context_obj = MockCliContextObj(invalid_user_state=True)

    # Configure Runner
    command_runner = CliRunner()

    # Run Test
    command_result = command_runner.invoke(
        config_commands.verify, obj=mock_cli_context_obj
    )

    # Assert Expected Output
    assert command_result.exit_code == 1
    assert type(command_result.exception) == type(
        error_utils.RIB203("User State File Not Found")
    )


def test_verify_command_user_state_undefined():
    """
    Purpose:
        Test that `rib config verify` fails when when cannot find user state
    Args:
        N/A
    """

    # Setup CLI Context Obj
    mock_cli_context_obj = MockCliContextObj(missing_state=True)

    # Configure Runner
    command_runner = CliRunner()

    # Run Test
    command_result = command_runner.invoke(
        config_commands.verify, obj=mock_cli_context_obj
    )

    # Assert Expected Output
    assert command_result.exit_code == 1
    assert type(command_result.exception) == type(error_utils.RIB004())

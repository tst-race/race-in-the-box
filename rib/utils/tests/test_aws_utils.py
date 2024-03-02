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
        Test File for aws_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
import requests
from mock import patch
from unittest import mock
from unittest.mock import MagicMock

# Local Library Imports
from rib.utils import aws_utils, error_utils


###
# Fixtures
###


# N/A


###
# Mocked Functions
###


# N/A


###
# Tests
###


#########
# create_aws_profile
#########


def test_create_aws_profile_success():
    """
    Purpose:
        Check `create_aws_profile()` works
    Args:
        N/A
    """

    # Run Generate Config
    with patch("os.path.isfile") as is_file, patch(
        "rib.utils.general_utils.write_data_to_file"
    ) as write_data, patch("rib.utils.aws_utils.verify_aws_profile") as verify_profile:
        is_file.return_value = False
        write_data.return_value = None
        verify_profile.return_value = None

        aws_utils.create_aws_profile("a", "b", "us-east-1", False)

        assert True


def test_create_aws_profile_success_with_overwrite():
    """
    Purpose:
        Check `create_aws_profile()` works
    Args:
        N/A
    """

    # Run Generate Config
    with patch("os.path.isfile") as is_file, patch(
        "rib.utils.general_utils.write_data_to_file"
    ) as write_data, patch("rib.utils.aws_utils.verify_aws_profile") as verify_profile:
        is_file.return_value = True
        write_data.return_value = None
        verify_profile.return_value = None

        aws_utils.create_aws_profile("a", "b", "us-east-1", True)

        assert True


def test_create_aws_profile_fails_no_overwrite():
    """
    Purpose:
        Check `create_aws_profile()` works
    Args:
        N/A
    """

    # Run Generate Config
    with patch("os.path.isfile") as is_file, patch(
        "rib.utils.general_utils.write_data_to_file"
    ) as write_data, patch("rib.utils.aws_utils.verify_aws_profile") as verify_profile:
        is_file.return_value = True
        write_data.return_value = None
        verify_profile.return_value = None

        with pytest.raises(error_utils.RIB703):
            aws_utils.create_aws_profile("a", "b", "us-east-1", False)


#########
# does_ssh_key_exist
#########


def test_does_ssh_key_exist_true() -> int:
    """
    Purpose:
        Check `does_ssh_key_exist()` returns true when key is found
    Args:
        N/A
    """

    ssh_key_name = "test"

    with patch(
        "rib.utils.aws_utils.connect_aws_session_with_profile"
    ) as session_patch, patch(
        "rib.utils.aws_utils.connect_aws_resource"
    ) as resource_patch:
        ec2_resource_mock = MagicMock()
        ec2_resource_mock.key_pairs.filter.return_value = [ssh_key_name]
        resource_patch.return_value = ec2_resource_mock

        assert aws_utils.does_ssh_key_exist(ssh_key_name)


def test_does_ssh_key_exist_false() -> int:
    """
    Purpose:
        Check `does_ssh_key_exist()` returns false when key is not found
    Args:
        N/A
    """
    ssh_key_name = "test"

    with patch(
        "rib.utils.aws_utils.connect_aws_session_with_profile"
    ) as session_patch, patch(
        "rib.utils.aws_utils.connect_aws_resource"
    ) as resource_patch:
        ec2_resource_mock = MagicMock()
        ec2_resource_mock.key_pairs.filter.return_value = []
        resource_patch.return_value = ec2_resource_mock

        assert not aws_utils.does_ssh_key_exist(ssh_key_name)

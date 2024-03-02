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
        Test File for rib_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
from dataclasses import dataclass
from typing import Any, Dict
from unittest import mock
from unittest.mock import MagicMock, patch

# Local Library Imports
from rib.utils import rib_utils
from rib.utils.rib_utils import RibInitState


###
# Mocks/Fixtures
###


@dataclass
class MockRiBState:
    """A Mock rib state object"""

    rib_mode: str
    verbosity: int


@dataclass
class MockConfig:
    """A Mock Config"""

    RIB_PATHS: Dict[str, Any]


###
# Test Functions
###


#######
# check_rib_state_initalized
#######


@patch("os.path.isdir")
@patch("os.path.isfile")
def test_check_rib_state_initalized_initialized(mock_isfile, mock_isdir):
    mock_isdir.return_value = True
    mock_isfile.return_value = True
    RIB_CONFIG = rib_utils.load_race_global_configs()
    assert rib_utils.check_rib_state_initalized(RIB_CONFIG) == RibInitState.INITIALIZED


@patch("os.path.isdir")
@patch("os.path.isfile")
def test_check_rib_state_initalized_partial(mock_isfile, mock_isdir):
    mock_isdir.return_value = False
    mock_isfile.return_value = True
    RIB_CONFIG = rib_utils.load_race_global_configs()
    assert (
        rib_utils.check_rib_state_initalized(RIB_CONFIG)
        == RibInitState.PARTLY_INITIALIZED
    )


@patch("os.path.isdir")
@patch("os.path.isfile")
def test_check_rib_state_initalized_not_initialied(mock_isfile, mock_isdir):
    mock_isdir.return_value = False
    mock_isfile.return_value = False
    RIB_CONFIG = rib_utils.load_race_global_configs()
    assert (
        rib_utils.check_rib_state_initalized(RIB_CONFIG) == RibInitState.NOT_INITIALIZED
    )


#######
# generate_node_name
#######


def test_generate_node_name() -> int:
    """
    Purpose:
        test generate_node_name works
    Args:
        N/A
    Returns:
        test_result: -1 for fail, 0 for pass
    Raises:
        N/A
    """

    assert rib_utils.generate_node_name("client", 1) == "race-client-00001"
    assert rib_utils.generate_node_name("server", 1) == "race-server-00001"


#######
# is_ssh_key_present
#######


def test_is_ssh_key_present_is_present_and_valid() -> int:
    """
    Purpose:
        test is_ssh_key_present works when key is present and valid
    Args:
        N/A
    Returns:
        test_result: -1 for fail, 0 for pass
    Raises:
        N/A
    """

    # Run Generate Config
    with patch("rib.utils.ssh_utils.get_rib_ssh_key") as _:
        assert rib_utils.is_ssh_key_present()


def test_is_ssh_key_present_exception_thrown() -> int:
    """
    Purpose:
        test is_ssh_key_present works when key is present and valid.

        Note, because we are mocking the ssh_key_from file, this does not
        necessarily test if the key is present, but that is tested in another
        test, this just tests if any exception is thrown from the function
    Args:
        N/A
    Returns:
        test_result: -1 for fail, 0 for pass
    Raises:
        N/A
    """

    # Run Generate Config
    with patch("rib.utils.ssh_utils.get_rib_ssh_key") as get_rib_ssh_key:
        get_rib_ssh_key.side_effect = Exception("test")
        assert not rib_utils.is_ssh_key_present()


#######
# get_rib_mode
#######


def test_get_rib_mode() -> int:
    """
    Purpose:
        Test that `get_rib_mode` properly returns the rib mode
    Args:
        N/A
    """

    assert (
        rib_utils.get_rib_mode(MockRiBState(rib_mode=None, verbosity=None), None)
        == "local"
    )
    assert (
        rib_utils.get_rib_mode(MockRiBState(rib_mode="aws", verbosity=None), None)
        == "aws"
    )
    assert (
        rib_utils.get_rib_mode(MockRiBState(rib_mode=None, verbosity=None), "aws")
        == "aws"
    )
    assert (
        rib_utils.get_rib_mode(MockRiBState(rib_mode="local", verbosity=None), "aws")
        == "aws"
    )


#######
# get_verbosity
#######


def test_get_verbosity() -> int:
    """
    Purpose:
        Test that `get_verbosity` properly returns the verbosity
    Args:
        N/A
    """

    assert (
        rib_utils.get_verbosity(MockRiBState(rib_mode=None, verbosity=None), None) == 0
    )
    assert rib_utils.get_verbosity(MockRiBState(rib_mode=None, verbosity=0), None) == 0
    assert rib_utils.get_verbosity(MockRiBState(rib_mode=None, verbosity=None), 0) == 0
    assert rib_utils.get_verbosity(MockRiBState(rib_mode=None, verbosity=1), 0) == 1
    assert rib_utils.get_verbosity(MockRiBState(rib_mode=None, verbosity=0), 1) == 1
    assert rib_utils.get_verbosity(MockRiBState(rib_mode=None, verbosity=5), 1) == 1


#######
# translate_docker_dir_to_host_dir
#######


def test_translate_docker_dir_to_host_dir() -> int:
    """
    Purpose:
        Test that `translate_docker_dir_to_host_dir` properly translates
        the filesystems
    Args:
        N/A
    """

    mock_config = MockConfig(
        RIB_PATHS={
            "docker": {"rib_state": "/xstate/", "test": "/x/"},
            "host": {"rib_state": "/ystate/", "test": "/y/"},
        }
    )

    assert (
        rib_utils.translate_docker_dir_to_host_dir(mock_config, "/xstate/test/")
        == "/ystate/test/"
    )
    assert (
        rib_utils.translate_docker_dir_to_host_dir(
            mock_config, "/xstate/test/", base="rib_state"
        )
        == "/ystate/test/"
    )
    assert (
        rib_utils.translate_docker_dir_to_host_dir(mock_config, "/x/test/", base="test")
        == "/y/test/"
    )

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
        Test File for config_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
from unittest import mock

# Local Library Imports
from rib.utils import error_utils, config_utils


###
# Fixtures
###


# None at the Moment (Empty Test Suite)


###
# Mocked Functions
###


# None at the Moment (Empty Test Suite)


###
# Test config_utils functions
###


# None at the Moment (Empty Test Suite)

################################################################################
# check_valid_config_options
################################################################################


def test_check_valid_config_options():
    """
    Purpose:
        Check case where config file is valid, key is valid, and value is valid
    """
    config_utils.check_valid_config_options("race-config", "level", "DEBUG")


def test_check_valid_config_options_invalid_config_file():
    """
    Purpose:
        Check case where config file is invalid, key is valid, and value is valid
    """
    with pytest.raises(
        error_utils.RIB322,
        match="Check RiB version `rib --version` or email race@twosixlabs.com",
    ):
        config_utils.check_valid_config_options("INVALID", "level", "DEBUG")


def test_check_valid_config_options_invalid_key():
    """
    Purpose:
        Check case where config file is valid, key is invalid, and value is valid
    """
    with pytest.raises(
        error_utils.RIB322, match="INVALID is not a valid key in race-config"
    ):
        config_utils.check_valid_config_options("race-config", "INVALID", "DEBUG")


def test_check_valid_config_options_invalid_value():
    """
    Purpose:
        Check case where config file is valid, key is valid, and value is invalid
    """
    with pytest.raises(
        error_utils.RIB322,
        match="INVALID is an invalid value for level in race-config",
    ):
        config_utils.check_valid_config_options("race-config", "level", "INVALID")


def test_check_valid_config_options_bandwidth():
    """
    Purpose:
        Check valid case where a number is a value
    """
    config_utils.check_valid_config_options("race-config", "bandwidth", "100")


def test_check_valid_config_options_bandwidth_invalid_nan():
    """
    Purpose:
        Check an invalid case where a number is expected but not provided
    """
    with pytest.raises(
        error_utils.RIB322,
        match="INVALID is an invalid value for bandwidth in race-config",
    ):
        config_utils.check_valid_config_options("race-config", "bandwidth", "INVALID")

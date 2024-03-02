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
        Test File for race_utils.py
"""

# Python Library Imports
import pytest

# Local Library Imports
from rib.utils import race_utils, error_utils


###
# Mocks
###


# N/A


###
# Data Fixtures
###


# N/A


###
# Test race_utils functions
###


################################################################################
# get_race_versions
################################################################################


def test_get_race_versions():
    """
    Purpose:
        Test that get_race_versions Returns a 001 until its implemented
    Args:
        N/A
    """

    with pytest.raises(error_utils.RIB001, match=r".*get_race_versions().*"):
        race_utils.get_race_versions()

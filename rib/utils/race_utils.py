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
        RACE Utilities for interacting with the RACE system/versions.

        i.e., what versions of RACE are available?
"""

# Python Library Imports
from typing import List

# Local Python Library Imports
from rib.utils import error_utils


###
# RACE Functions
###


def get_race_versions() -> List[str]:
    """
    Purpose:
        Get versions of RACE that are available to the user
    Args:
        N/A
    Returns:
        race_versions (List): List of avilable versions
    """

    race_versions: List[str] = []

    raise error_utils.RIB001("get_race_versions()")

    # TODO: Once manifests are complete, need to pull here

    # return race_versions

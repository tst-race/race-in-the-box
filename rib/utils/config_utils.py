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
        Config Utilities. Holds functionality related to config command group
"""

# Python Library Imports
# N/A

# Local Python Library Imports
from rib.utils import error_utils


###
# Globals
###


# Constant used to make code more readable. Use this for key:value pairs where any
# value should be accepted
ALL_VALUES_ACCEPTED = "ALL_VALUES_ACCEPTED"
# Constant used to make code more readable. Use this for key:value pairs where any
# positive number should be accepted
ALL_NUMBERS_ACCEPTED = "ALL_NUMBERS_ACCEPTED"

# This dict holds valid values for race.json. This needs to be maintained as
# changes to the config file in RACE are made
CONFIG_GROUP = {
    "race-config": {
        "bandwidth": ALL_NUMBERS_ACCEPTED,
        "debug": ["true", "false"],
        "level": ["DEBUG", "INFO", "WARNING", "ERROR"],
        "log-race-config": ["true", "false"],
        "log-network-manager-config": ["true", "false"],
        "log-comms-config": ["true", "false"],
    },
}


###
# Check FUnctions
###


def check_valid_config_options(config: str, key: str, value: str) -> None:
    """
    Purpose:
        Restrict changes to config files to potential options
    Args:
        config (String): Which configs are being changed
        key (String): Key to change
        value (String): Value to set
    Returns:
        N/A
    Raises:
        error_utils.RIB322: When invalid configs are passed in
    """

    valid_options = CONFIG_GROUP.get(config)
    if valid_options is None:
        raise error_utils.RIB322(
            f"changes to {config} are not supported yet",
            "Check RiB version `rib --version` or email race@twosixlabs.com",
        )

    valid_values = valid_options.get(key)
    if valid_values is None:
        raise error_utils.RIB322(
            f"{key} is not a valid key in {config}",
            f"Valid keys are {valid_options.keys()}",
        )

    if (
        value not in valid_values
        and valid_values != ALL_VALUES_ACCEPTED
        and valid_values != ALL_NUMBERS_ACCEPTED
    ):
        raise error_utils.RIB322(
            f"{value} is an invalid value for {key} in {config}",
            f"Valid values are {valid_values}",
        )

    if valid_values == ALL_NUMBERS_ACCEPTED and not value.isnumeric():
        raise error_utils.RIB322(
            f"{value} is an invalid value for {key} in {config}",
            "Valid values are positive numbers",
        )

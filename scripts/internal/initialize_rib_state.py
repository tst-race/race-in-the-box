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
        Script responsible for initalizing the RACE environment

    Steps:
        - Check to see if the system is initalized
        - Make dirs if necessary
        - Return/Exit

    Example Call:
        python3 /race_in_the_box/rib_scripts/internal/initialize_rib_state.py
"""

# Python Library Imports
import logging
import os
import sys

# Local Python Library Imports
from rib.utils import rib_utils
from rib.utils.rib_utils import RibInitState


###
# Script Main Execution
###


def main():
    """
    Purpose:
        Initialize the environment so that RiB can be utilized without issue. This
        includes filesystem and other configs.
    Args:
        N/A
    Returns:
        N/A
    """
    logging.info("Initializing RiB Environment")

    RIB_CONFIG = rib_utils.load_race_global_configs()

    # Check RiB Initialized
    rib_initialized_state = rib_utils.check_rib_state_initalized(RIB_CONFIG)

    # Based on state, initialize state as necessary
    if rib_initialized_state in (
        RibInitState.NOT_INITIALIZED,
        RibInitState.PARTLY_INITIALIZED,
    ):
        rib_utils.initialize_rib_state(RIB_CONFIG)
    elif rib_initialized_state == RibInitState.INITIALIZED:
        pass  # Do nothing, we good
    elif rib_initialized_state == RibInitState.ERROR:
        raise Exception(f"RiB State Error")
    else:
        raise Exception(f"Unknown RiB State: {rib_initialized_state}")

    rib_utils.update_rib_state(RIB_CONFIG)

    logging.info("Complete Initializing RiB Environment")


if __name__ == "__main__":

    log_level = logging.INFO
    logging.getLogger().setLevel(log_level)
    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format="[initialize_rib_state] %(asctime)s %(levelname)s %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
    )

    try:
        main()
    except Exception as err:
        logging.error(f"{os.path.basename(__file__)} failed due to error: {err}")
        raise err

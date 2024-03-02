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
        The RaceInTheBoxState is responsible for holding, caching, loading
        and all other state management needed when working with RiB. The
        following are guiding principals for the design
            - Once a user has utilized RiB once, the state should be stored
            for easier future use
            - CLI args will be higher priority than user prompts
            - No config file or corrupt config files will be treated as
            if the user is using RiB for the first time
"""

# Python Library Imports
import click
import json
import os
import sys
from typing import Dict, Optional

# Local Python Library Imports
from rib.config.config import Config
from rib.utils import error_utils


class RaceInTheBoxState:
    """
    Purpose:
        The RaceInTheBoxState is responsible for holding, caching, loading
        and all other state management needed when working with RiB. The
        following are guiding principals for the design
            - Once a user has utilized RiB once, the state should be stored
            for easier future use
            - CLI args will be higher priority than user prompts
            - No config file or corrupt config files will be treated as
            if the user is using RiB for the first time
    """

    ###
    # Attributes
    ###

    # Base Config Option
    config: Config.Production

    # User State File
    user_state_file: Optional[str] = None

    # Race Mode
    rib_mode: Optional[str] = None

    # Verbosity Level
    detail_level: Optional[int] = None
    verbosity: Optional[int] = None

    ###
    # Lifecycle Methods
    ###

    def __init__(self, config: Config.Production):
        """
        Purpose:
            Initialize the RaceInTheBoxState object.

            Will taking in runtime args (config_dir and version are always runtime) and
            any other CLI args that the user passes in. Will take this information and
            load/create a RiB state that will be used through the CLI tool.
        Args:
            config: Config object for RACE
        """

        # Load RiB Global Configs
        self.config = config
        self.user_state_file = (
            f"{config.RIB_PATHS['docker']['user_state']}/"
            f"{config.RIB_USER_STATE_FILENAME}"
        )

        # Load Config
        if os.path.isfile(self.user_state_file):
            self.load_stored_state()

    def __repr__(self) -> str:
        """
        Purpose:
            Representation of the RaceInTheBoxState object.

            Note: Needs to be updated as state changes. Should print most
            important items
        Args:
            N/A
        Returns:
            RaceInTheBoxState: String representation of RaceInTheBoxState
        """

        return f"<RaceInTheBoxState (version {self.config.RIB_VERSION})>"

    def __del__(self):
        """
        Purpose:
            Store the State of the RaceInTheBoxState object to ensure it can be loaded
            the next time RiB is loaded
        Args:
            N/A
        Returns:
            N/A
        """

    ###
    # Verify Methods
    ###

    def verify_rib_state(self):
        """
        Purpose:
            Verify RiB State. Raise exception if RiB is not set correctly
        Args:
            N/A
        Returns:
            N/A
        """

        if not os.path.isfile(self.user_state_file):
            raise error_utils.RIB002("User State File Not Found")

        missing_configs = []
        # E.g.,
        # if not self.required_config:
        #    missing_configs.append("missing required_config")

        if missing_configs:
            raise error_utils.RIB004(invalid_state_reason=", ".join(missing_configs))

    ###
    # Initialization Methods
    ###

    def clear_rib_state(self):
        """
        Purpose:
            Clear state and reinit
        Args:
            N/A
        Returns:
            N/A
        """

        # RiB Mode
        self.rib_mode = None

        # Verbosity Level
        self.detail_level = None
        self.verbosity = None

    def initalize_rib_state(
        self,
        rib_mode: Optional[str] = None,
        detail_level: Optional[int] = None,
        verbosity: Optional[int] = None,
    ):
        """
        Purpose:
            Handle setting the state of the RaceInTheBoxState object. Will
            favor CLI arguments over the config file (will overwrite them) when
            possible. Will also prompt the user for information when necessary.

            Each piece of state is handled by a specific method which is specifically
            tuned for getting the necessary information from the user into the correct
            place. This is not a 1-1 mapping of function to attribute.
        Args:
            rib_mode: RiB mode (from CLI)
            detail_level: Detail level (from CLI)
            verbosity: Verbosity level (from CLI)
        Returns:
            N/A
        """

        # RiB Mode
        self.set_rib_mode(rib_mode)  # hardcoded, but update in future

        # Verbosity
        self.set_detail_level(detail_level)
        self.set_verbosity(verbosity)

    ###
    # Setter Methods
    ###

    def set_rib_mode(self, rib_mode: Optional[str]):
        """
        Purpose:
            Handle setting RACE mode
        Args:
            rib_mode: the mode for race to operate in (local, aws)
        Returns:
            N/A
        """

        # Set State if and only if CLI Arg is set (an matches one of the options)
        if rib_mode and rib_mode in ("local", "aws"):
            self.rib_mode = rib_mode
        elif rib_mode and rib_mode not in ("local", "aws"):
            raise Exception(f"{rib_mode} is not a valid rib_mode: (local or aws)")

    def set_detail_level(self, detail_level: Optional[int]):
        """
        Purpose:
            Handle setting detail level
        Args:
            detail_level: Level of details to include in status/info output
        Returns:
            N/A
        """

        if detail_level is not None:
            self.detail_level = detail_level
        elif sys.stdin.isatty():
            self.detail_level = click.prompt(
                "What default detail level should be used for status/info reports (0=least detailed, 5=most detailed)?",
                default=0,
                show_default=True,
                type=click.IntRange(0, 5),
            )

    def set_verbosity(self, verbosity: Optional[int]):
        """
        Purpose:
            Handle setting verbosity
        Args:
            verbosity: the mode for container status to be printed during commands
        Returns:
            N/A
        """

        # Set State if and only if CLI Arg is set (and matches one of the options)
        if verbosity is not None:
            self.verbosity = verbosity
        elif sys.stdin.isatty():
            self.verbosity = click.prompt(
                "What default logging verbosity should be used (0=least verbose, 5=most verbose)?",
                default=0,
                show_default=True,
                type=click.IntRange(0, 5),
            )

    ###
    # Race in the Box State Methods
    ###

    def export_state(self) -> Dict[str, Optional[str]]:
        """
        Purpose:
            Export the current state of the object (some portions
            are runtime only like version, config dir, config file) as a
            dictionary so that it can be stored in a json file for
            later use or for printing
        Args:
            N/A
        Returns:
            rib_state: Dict state of the RiB
        """

        return {
            "rib_mode": self.rib_mode,
            "detail_level": self.detail_level,
            "verbosity": self.verbosity,
        }

    def load_stored_state(self):
        """
        Purpose:
            Load State of Object from .json file in the config
            dir from a previous run of RiB
        Args:
            N/A
        Returns:
            N/A
        """

        try:
            with open(self.user_state_file, "r") as config_file_obj:
                loaded_config = json.load(config_file_obj)
                for key, value in loaded_config.items():
                    # print(f"Loaded Config: {key} = {value}")
                    setattr(self, key, value)
        except Exception as err:
            print(f"Failed to Load Config: {err}")
            # Do not stop execution, attempt to load RiB without
            # A config and rebuild the configuration for next time
            # (assume its corrupted)

    def store_state(self):
        """
        Purpose:
            Store State of Object into .json file in the config
            dir so that future RiB usages do not need to be
            configured
        Args:
            N/A
        Returns:
            N/A
        """

        with open(self.user_state_file, "w") as config_file_obj:
            json.dump(
                self.export_state(),
                config_file_obj,
                sort_keys=True,
                indent=4,
                separators=(",", ": "),
            )

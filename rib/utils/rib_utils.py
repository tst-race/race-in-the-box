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
        RiB Utilities. Holds cross command functionality that is not cleary
        group by the command groups
"""

# Python Library Imports
import copy
import os
from enum import Enum
from typing import Optional

# Local Python Library Imports
from rib.config.config import Config
from rib.utils import error_utils, general_utils, ssh_utils


###
# Global Variables
###


class RibInitState(Enum):
    """
    Purpose:
        Track the state of RiB for init purposes
    """

    # RiB is fully initialized and ready to go
    INITIALIZED = 0

    # RiB is not initialized at all, will need to be fully init
    NOT_INITIALIZED = 1

    # There is some items missing from the expected final State
    PARTLY_INITIALIZED = 2

    # There is some items missing from the expected final State
    ERROR = -1


###
# Global Configs Functionality
###


def load_race_global_configs(environment: Optional[str] = None) -> Config:
    """
    Purpose:
        Load a configuration object depending on the environment passed in. This
        allows for settings to be dynamic between prod, qa, and dev.

        This is non-configurable or changeable configs from the users
        perspective. Meant for things that are set by the RACE dev team that
        are used throughout RiB, but not set by the performer

        * Defaults to development environment
    Args:
        environment (String): Environment to get configs for and run the RiB in.
            Basically acts as a "mode" that determines where images are pulled from
            and pushed to (as an example)
    Returns:
        config (Config obj): Configuration object with RiB static configs
    Raises:
        N/A
    """

    return copy.deepcopy(Config.get(environment=environment))


###
# Initialization Functions
###


def check_rib_state_initalized(config: Config) -> RibInitState:
    """
    Purpose:
        Check to see if all of the files that are supposed to exist for user
        state in RiB exist. if not, we need to initialize RiB.
    Args:
        config (Config obj): Configuration object with RiB static configs
    Return:
        rib_state: the RibInitState enum of current state
    Raises:
        N/A
    """

    rib_state_initalized = None

    # What to Verify
    rib_directories_to_verify = []
    for directory_name, rib_directory in config.RIB_PATHS["docker"].items():
        if isinstance(rib_directory, str):
            rib_directories_to_verify.append(rib_directory)
        else:
            for sub_directory_name, rib_sub_directory in rib_directory.items():
                rib_directories_to_verify.append(rib_sub_directory)

    rib_files_to_verify = [
        f"{config.RIB_PATHS['docker']['user_state']}/{config.RIB_USER_STATE_FILENAME}"
    ]

    # Whether or not items are found or missing
    dir_missing = False
    dir_found = False
    file_missing = False
    file_found = False

    # Assumption: directories can be missing in a previously initialized RiB deployment
    for rib_directory in rib_directories_to_verify:
        if not os.path.isdir(rib_directory):
            dir_missing = True
        else:
            dir_found = True

    # Assumption: If user state file is missing, RiB is considered uninitialized
    for rib_file in rib_files_to_verify:
        if not os.path.isfile(rib_file):
            file_missing = True
        else:
            file_found = True

    # Set state based on
    if (dir_missing and file_missing) and not (dir_found or file_found):
        rib_state = RibInitState.NOT_INITIALIZED
    elif (dir_missing or file_missing) and (dir_found or file_found):
        rib_state = RibInitState.PARTLY_INITIALIZED
    elif not (dir_missing or file_missing) and (dir_found and file_found):
        rib_state = RibInitState.INITIALIZED
    else:
        rib_state = RibInitState.ERROR

    return rib_state


def remove_previous_rib_state(config: Config) -> None:
    """
    Purpose:
        Remove the previous state dir. Will delete ~/.race/rib
    Args:
        config (Config obj): Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        Exception: If the remove fails or if the dir does not exist
    """

    general_utils.remove_dir_file(config.DOCKER_RIB_STATE_PATH)


def initialize_rib_state(config: Config) -> None:
    """
    Purpose:
        Initialize the state dir for RiB. Will create directories, will copy the
        build-outputs, deployments, and docker-images from RiB on the container
        so that the user gets the same structure and can begin adding their things
        into the same.
    Args:
        config (Config obj): Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        Exception: If creating files fails
        Exception: If copying files/dirs fails
    """

    # Set base path to rib artifacts
    artifact_path = config.RIB_PATHS["docker"]["artifacts"]

    # Directories to Create
    create_base_dirs(config)
    create_base_files(config)

    # Create Bash history file
    create_bash_history(config)


def update_rib_state(config: Config) -> None:
    """
    Purpose:
        Update/Overwrite RiB State with updates to make sure RiB is functional.
        This is so that someone who runs RiB does not have to reset their state when
        a change is pushed that breaks some of the old state.
    Args:
        config (Config obj): Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        Exception: If copying canned deployments/aws envs fails
    """

    # Set base path to rib artifacts
    artifact_path = config.RIB_PATHS["docker"]["artifacts"]

    # Copy Files to Persistence Dir (Volume Mounted In)
    copy_canned_aws_envs(artifact_path, config)
    copy_canned_deployments(artifact_path, config)


###
# Copy/Create/Overwrite State Functions
###


def create_base_dirs(config: Config) -> None:
    """
    Purpose:
        Directories to Create in the user's home dir for persistence
        across RiB Runs
    Args:
        config: Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        N/A
    """

    rib_directories_to_create = [
        config.RIB_PATHS["docker"]["aws_envs"]["root"],
        config.RIB_PATHS["docker"]["aws_state"],
        config.RIB_PATHS["docker"]["build_outputs"],
        config.RIB_PATHS["docker"]["cache"],
        config.RIB_PATHS["docker"]["deployments"]["root"],
        config.RIB_PATHS["docker"]["github"],
        config.RIB_PATHS["docker"]["range_configs"],
        config.RIB_PATHS["docker"]["rib_logs"],
        config.RIB_PATHS["docker"]["user_state"],
        config.RIB_PATHS["docker"]["plugins-cache"],
        f"{config.RIB_PATHS['docker']['deployments']['root']}/aws",
        f"{config.RIB_PATHS['docker']['deployments']['root']}/local",
        f"{config.RIB_PATHS['docker']['rib_state']}/docker-images",
    ]
    for directory_to_create in rib_directories_to_create:
        general_utils.make_directory(
            directory_to_create, create_parents=True, ignore_exists=True
        )


def create_base_files(config: Config) -> None:
    """
    Purpose:
        Files to Create in the user's home dir for persistence
        across RiB Runs. Includes user state files and similar
    Args:
        config: Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        N/A
    """

    # Files to Manually Create
    rib_files_to_create = [
        f"{config.RIB_PATHS['docker']['user_state']}/{config.RIB_USER_STATE_FILENAME}"
    ]
    for rib_file_to_create in rib_files_to_create:
        try:
            general_utils.write_data_to_file(
                rib_file_to_create, {}, data_format="json", overwrite=False
            )
        except error_utils.RIB006:
            # If the file exists, RiB was partially init and not an issue
            pass


def create_bash_history(config: Config) -> None:
    """
    Purpose:
        Create a bash history file for RiB to persist history between runs
    Args:
        config: Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        N/A
    """

    # Create Bash History File if it doesn't already exist
    try:
        general_utils.write_data_to_file(
            f"{config.RIB_PATHS['docker']['user_state']}/.bash_history",
            "",  # No data for now, history will be added
            data_format="string",
            overwrite=False,
        )
    except error_utils.RIB006:
        # If the file exists, RiB was partially init and not an issue
        pass


def copy_canned_aws_envs(artifact_path: str, config: Config) -> None:
    """
    Purpose:
        Copy any/all AWS Envs to the users home dir. This holds logs/metadata
        that needs to be changed over time, so we need it in the home dir for
        persistence
    Args:
        artifact_path: path to race in the box artifacts in the image
        config: Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        N/A
    """

    # Setting source (where rib is installed) and dest (user persistent dir)
    src_aws_env_path = f"{artifact_path}/envs/aws/"
    dest_aws_env_path = config.RIB_PATHS["docker"]["aws_envs"]["root"]

    # checking for canned, named with canned-... structure
    canned_aws_envs = [
        aws_env_name
        for aws_env_name in os.listdir(src_aws_env_path)
        if aws_env_name.startswith("canned")
    ]

    # Loop through. Only overwrite what doesn't exist to not blow away logs
    # metadata, etc. Once a canned aws env is set in the user persistent, it
    # will change as the up/down it
    for canned_aws_env in canned_aws_envs:
        dest_canned_aws_env = f"{dest_aws_env_path}/{canned_aws_env}"
        if not os.path.isdir(dest_canned_aws_env):
            general_utils.copy_dir_file(
                f"{src_aws_env_path}/{canned_aws_env}",
                dest_canned_aws_env,
                overwrite=False,  # again, do not overwrite this ever
            )


def copy_canned_deployments(artifact_path: str, config: Config) -> None:
    """
    Purpose:
        Copy any/all Deployments to the users home dir. This holds logs/metadata
        that needs to be changed over time, so we need it in the home dir for
        persistent
    Args:
        artifact_path: path to race in the box artifacts in the image
        config: Configuration object with RiB static configs
    Return:
        N/A
    Raises:
        N/A
    """

    # Get path of persistent Deployments
    rib_deployment_root_path = config.RIB_PATHS["docker"]["deployments"]["root"]

    for deployment_mode in config.DEPLOYMENT_MODES:
        # Setting source (where rib is installed) and dest (user persistent dir)
        src_deployment_path = f"{artifact_path}/deployments/{deployment_mode}/"
        dest_deployment_path = f"{rib_deployment_root_path}/{deployment_mode}/"

        # checking for canned, named with canned-... structure
        canned_deployments = [
            deployment_name
            for deployment_name in os.listdir(src_deployment_path)
            if deployment_name.startswith("canned")
        ]

        # Loop through. Only overwrite what doesn't exist to not blow away logs
        # metadata, etc. Once a canned deployment is set in the user persistent, it
        # will change as the up/down it
        for canned_deployment in canned_deployments:
            dest_canned_deployment = f"{dest_deployment_path}/{canned_deployment}"
            if not os.path.isdir(dest_canned_deployment):
                general_utils.copy_dir_file(
                    f"{src_deployment_path}/{canned_deployment}",
                    dest_canned_deployment,
                    overwrite=False,  # again, do not overwrite this ever
                )


###
# State/Arg Utils
###


def get_rib_mode(rib_state_obj: object, rib_mode_arg: str) -> Optional[str]:
    """
    Purpose:
        Get the RiB mode through either the RiB State or the argument. Argument
        overrides state if possible, and the RiB mode must be set or an exception
        should be thrown
    Args:
        rib_state_obj (RaceInTheBoxState Obj): state object holding the RiB global
            mode if set
        rib_mode_arg (String): String mode passed in for the command (if set)
    Return:
        rib_mode (String): Race Mode to use
    """

    rib_mode = None

    # Get rib_mode from state or CLI args
    if not rib_mode_arg and not rib_state_obj.rib_mode:
        rib_mode = "local"  # Defaulting to Local Mode for now
    elif rib_mode_arg:
        rib_mode = rib_mode_arg
    else:
        rib_mode = rib_state_obj.rib_mode

    return rib_mode


def get_verbosity(rib_state_obj: object, verbosity_arg: int) -> Optional[int]:
    """
    Purpose:
        Get the Verbosity level through either the RiB State or the argument. Argument
        overrides state if possible
    """

    # Get verbosity from state or CLI args
    if not verbosity_arg and not rib_state_obj.verbosity:
        verbosity = 0  # Defaulting to off for now
    elif verbosity_arg is not None and verbosity_arg > 0:
        verbosity = verbosity_arg
    else:
        verbosity = rib_state_obj.verbosity
    return verbosity


###
# Filesystem Translation
###


def translate_docker_dir_to_host_dir(
    config: Config, docker_dir: str, base: Optional[str] = "state"
) -> str:
    """
    Purpose:
        Translate a RiB Docker dir to the corresponding host dir

        Note, can either pass in state/code as the base dir to translate
    Args:
        config (Config Obj): An initialized config object
        docker_dir (String): Path to translate
        base (String): Base mount in docker to pivot the translation around, support
            state/code ATM
    Returns:
        host_dir (String): The corresponding host dir
    Raises:
        N/A
    """

    if base == "state":
        base = "rib_state"

    if base not in config.RIB_PATHS["docker"]:
        raise error_utils.RIB001(f"Translating {base} Dirs From Docker to Host")

    return docker_dir.replace(
        config.RIB_PATHS["docker"][base], config.RIB_PATHS["host"][base]
    )


def translate_docker_dir_to_relative_dir(
    config: Config, docker_dir: str, base: Optional[str] = "state"
) -> str:
    """
    Purpose:
        Translate a RiB Docker dir to the relative dir from host

        Note, can either pass in state/code as the base dir to translate
    Args:
        config (Config Obj): An initialized config object
        docker_dir (String): Path to translate
        base (String): Base mount in docker to pivot the translation around
    Returns:
        host_dir (String): The corresponding host dir
    Raises:
        N/A
    """

    if base not in config.RIB_PATHS["docker"]:
        raise error_utils.RIB001(f"Translating {base} Dirs From Docker to Host")

    return docker_dir.replace(
        config.RIB_PATHS["docker"][base], config.RIB_PATHS["portable"][base]
    )


###
# RiB Node Functions
###


def generate_node_name(node_type: str, node_id: int) -> str:
    """
    Purpose:
        Build the RiB Node Name from type/num
    Args:
        node_type: client/server
        node_id: id of the node
        fill: how much to fill the node name
    Returns:
        node_name: the name of the node
    Raises:
        N/A
    """

    rib_config = load_race_global_configs()

    return f"race-{node_type}-{str(node_id).zfill(rib_config.NODE_ID_WIDTH)}"


###
# RiB SSH Mount
###


def is_ssh_key_present() -> bool:
    """
    Purpose:
        Check that the ssh key for rib is properly mounted and
        available. this will be necessary for aws env functionality
        and remote deployments
    Args:
        N/A
    Returns:
        ssh_key_present: if the ssh key file exists (not that it is valid)
    Raises:
        N/A
    """

    try:
        ssh_utils.get_rib_ssh_key()
    except Exception as err:
        return False

    return True

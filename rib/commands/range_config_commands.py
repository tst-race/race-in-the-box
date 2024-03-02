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
    Range-config commands
"""

# Python Library Imports
import click
import os
from typing import Any, Dict

# Local Python Library Imports
from rib.commands.deployment_options import (
    android_client_count_option,
    android_client_uninstalled_count_option,
    linux_client_count_option,
    linux_client_uninstalled_count_option,
    linux_server_count_option,
    linux_server_uninstalled_count_option,
)
from rib.utils import (
    general_utils,
    range_config_utils,
    rib_utils,
)


###
# Generating Config Commands
###


@click.command("create")
@click.option(
    "--name",
    "config_name",
    required=True,
    help="Name of configs to generate and store?",
)
@android_client_count_option()
@android_client_uninstalled_count_option()
@linux_client_count_option()
@linux_client_uninstalled_count_option()
@linux_server_count_option()
@linux_server_uninstalled_count_option()
@click.pass_context
def create(
    cli_context,
    config_name: str,
    android_client_count: int,
    android_client_uninstalled_count: int,
    linux_client_count: int,
    linux_client_uninstalled_count: int,
    linux_server_count: int,
    linux_server_uninstalled_count: int,
) -> None:
    """
    Create a Range Config
    """

    click.echo("Generating Configs and Storing")

    if (android_client_count + linux_client_count) < 1:
        click.confirm("Create range-config with no clients?", abort=True)

    # Add .json to the config name if its not present
    if ".json" not in config_name:
        config_name += ".json"

    # Getting the range config dir from the configs
    rib_config = rib_utils.load_race_global_configs()
    range_config_path = rib_config.RIB_PATHS["docker"]["range_configs"]
    full_config_filename = f"{range_config_path}/{config_name}"

    # Build Range Config
    range_config = range_config_utils.create_local_range_config(
        name=config_name,
        android_client_count=android_client_count,
        android_client_uninstalled_count=android_client_uninstalled_count,
        linux_client_count=linux_client_count,
        linux_client_uninstalled_count=linux_client_uninstalled_count,
        linux_server_count=linux_server_count,
        linux_server_uninstalled_count=linux_server_uninstalled_count,
        bastion={
            "internet_ip": "localhost",
            "reachable_from": ["localhost"],
            "usernames": ["rib"],
        },
    )

    # Store config to file in range-config dir
    general_utils.write_data_to_file(
        full_config_filename, range_config, data_format="json", overwrite=True
    )

    click.echo("Created files:")
    click.echo(f"RiB Docker Filesystem: {full_config_filename}")
    click.echo(
        f"Host Filesystem: "
        f"{rib_utils.translate_docker_dir_to_host_dir(rib_config, full_config_filename)}"
    )


@click.command("list")
@click.pass_context
def list_deployment_config(cli_context):
    """
    List Generated Config Files
    """

    # Getting the range config dir from the configs
    rib_config = rib_utils.load_race_global_configs()

    # Getting possible files from the dir and if they are .json
    config_files = [
        config_file
        for config_file in os.listdir(rib_config.RIB_PATHS["docker"]["range_configs"])
        if config_file.endswith(".json")
    ]

    # Outputting Results
    if config_files:
        click.echo("Config Files:")
        for config_file in config_files:
            click.echo("\t" + config_file)
    else:
        click.echo("No Files Found")


@click.command("remove")
@click.option(
    "--name",
    "config_name",
    required=True,
    help="Name of configs to generate and store?",
)
@click.pass_context
def remove(cli_context, config_name):
    """
    Remove a Generated Config File
    """

    # Add .json to the config name if its not present
    if ".json" not in config_name:
        config_name += ".json"

    # Getting the range config dir from the configs
    rib_config = rib_utils.load_race_global_configs()
    range_config_path = rib_config.RIB_PATHS["docker"]["range_configs"]

    # Getting possible files from the dir and if they are .json
    config_files = [
        config_file
        for config_file in os.listdir(range_config_path)
        if config_file.endswith(".json")
    ]

    # Checking to see if the file exists
    if config_name not in config_files:
        click.echo(f"Config {config_name} does not exist")
    else:
        full_config_filename = f"{range_config_path}/{config_name}"
        click.echo(f"Removing {full_config_filename}")
        os.remove(full_config_filename)

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
    Common deployment config commands
"""

# Python Library Imports
import click
import logging
import json
from typing import Any, List, Optional

# Local Python Library Import
from rib.commands.common_options import (
    timeout_option,
    generate_timestamp,
)
from rib.commands.deployment_options import (
    deployment_name_option,
    nodes_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import general_utils, error_utils

logger = logging.getLogger(__name__)


###
# Generic Deployment Configs Commands
###


@click.group("config")
def config_command_group() -> None:
    """Commands for generating and managing RACE configs"""


@config_command_group.group("runtime")
def runtime_config_command_group() -> None:
    """Commands for managing runtime configs"""


def _validate_json_object(
    ctx: click.Context, param: click.Parameter, value: str
) -> Any:
    """Ensure that value is a valid JSON dictionary"""
    try:
        if value:
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                raise click.BadParameter("must be a JSON object")
        return value
    except:
        raise click.BadParameter("must be a valid JSON object") from None


@config_command_group.command("generate")
@deployment_name_option("generate plugin configs")
@click.option(
    "--network-manager-custom-args",
    default="",
    help=(
        "Custom arguments for the network manager plugin's config generation script.\nExample: "
        '--network-manager-custom-args="--arg1=value --arg2 ..."'
    ),
    type=str,
)
@click.option(
    "--comms-custom-args",
    callback=_validate_json_object,
    default="",
    help=(
        "JSON map of comms channel IDs to custom arguments for the channel's config "
        "generation script.\nExample: "
        '--comms-custom-args=\'{"channel_id":"--arg1=value --arg2 ..."}\''
    ),
    type=str,
)
@click.option(
    "--artifact-manager-custom-args",
    callback=_validate_json_object,
    default="",
    help=(
        "JSON map of artifact manager plugin IDs to custom arguments for the plugin's config "
        "generation script.\nExample: "
        '--artifact-manager-custom-args=\'{"plugin_id":"--arg1=value --arg2 ..."}\''
    ),
    type=str,
)
@click.option(
    "--force",
    flag_value=True,
    help="Force config generation to overwrite existing configs",
)
@timeout_option(
    command_help="Time to allow each iteration of config generation to run (up to 3,600 seconds)",
    default=300,
)
@click.option(
    "--max-iterations",
    default=20,
    help="Number of iterations to allow between network manager and comms channel config generation (up to 100)",
    show_default=True,
    type=click.IntRange(1, 100),
)
@click.option(
    "--no-tar",
    flag_value=True,
    help="Do not tar configs after generation",
)
@pass_rib_mode
def generate(
    rib_mode: str,
    deployment_name: str,
    network_manager_custom_args: str,
    comms_custom_args: str,
    artifact_manager_custom_args: str,
    force: bool,
    timeout: int,
    max_iterations: int,
    no_tar: bool,
) -> None:
    """
    Generate deployment configs for the network manager plugin, all comms channels, and all artifact manager
    plugins
    """
    click.echo(f"Generating configs for deployment {deployment_name} ({rib_mode})")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    comms_custom_args_map = {}
    if comms_custom_args:
        comms_custom_args_map = json.loads(comms_custom_args)

    artifact_manager_custom_args_map = {}
    if artifact_manager_custom_args:
        artifact_manager_custom_args_map = json.loads(artifact_manager_custom_args)

    deployment.generate_plugin_or_channel_configs(
        force=force,
        network_manager_custom_args=network_manager_custom_args,
        comms_custom_args_map=comms_custom_args_map,
        artifact_manager_custom_args_map=artifact_manager_custom_args_map,
        timeout=timeout,
        max_iterations=max_iterations,
        skip_config_tar=no_tar,
    )


@config_command_group.command("tar")
@deployment_name_option("tar configs for the deployment")
@nodes_option("config tar")
@timeout_option(default=300)
@click.option(
    "--overwrite",
    flag_value=True,
    help="overwrite existing config tars",
)
@pass_rib_mode
def tar_configs(
    rib_mode: str,
    deployment_name: str,
    overwrite: bool,
    timeout: int,
    nodes: Optional[List[str]],
) -> None:
    """
    tar configs for the deployment
    """
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Taring configs for nodes {general_utils.stringify_nodes(nodes)} in Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Taring configs for all nodes in Deployment: {deployment_name} ({rib_mode})"
        )

    deployment.tar_configs(force=overwrite, timeout=timeout, nodes=nodes)


@config_command_group.command("publish")
@deployment_name_option("Publish configs for the deployment")
@timeout_option(default=300)
@nodes_option("config publish")
@click.option(
    "--overwrite",
    flag_value=True,
    help="publish over existing config tars",
)
@pass_rib_mode
def publish_configs(
    rib_mode: str,
    deployment_name: str,
    overwrite: bool,
    timeout: int,
    nodes: Optional[List[str]],
) -> None:
    """
    Publish configs for the deployment
    """
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Publishing configs for nodes {general_utils.stringify_nodes(nodes)} in Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Publishing configs all nodes in Deployment: {deployment_name} ({rib_mode})"
        )

    deployment.upload_configs(force=overwrite, timeout=timeout, nodes=nodes)


@config_command_group.command("install")
@deployment_name_option("Install configs on the specified nodes")
@timeout_option(default=300)
@nodes_option("config install")
@click.option(
    "--force",
    flag_value=True,
    help="Install configs tars regardless of node status",
)
@pass_rib_mode
def install_configs(
    rib_mode: str,
    deployment_name: str,
    force: bool,
    timeout: int,
    nodes: Optional[List[str]],
) -> None:
    """
    Install configs for the specified nodes
    """
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Installing configs for nodes {general_utils.stringify_nodes(nodes)} in Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Installing configs for all nodes in Deployment: {deployment_name} ({rib_mode})"
        )

    deployment.install_configs(force=force, timeout=timeout, nodes=nodes)


@runtime_config_command_group.command("pull")
@deployment_name_option("from which to pull the active runtime configs")
@click.option(
    "--config-name",
    "config_name",
    required=False,
    default=generate_timestamp,
    type=str,
    help="The directory name used to store the runtime configs (defaults to current time)",
)
@click.option(
    "--overwrite",
    flag_value=True,
    help="overwrite existing configs if the config name already exists",
)
@timeout_option(default=300)
@pass_rib_mode
def pull_runtime_configs(
    rib_mode: str,
    deployment_name: str,
    config_name: str,
    overwrite: bool,
    timeout: int,
) -> None:
    """
    pull the current runtime configs from each of the RACE nodes in a deployment.
    """
    logger.info(f"Pulling runtime configs...")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.pull_runtime_configs(config_name, overwrite=overwrite, timeout=timeout)

    logger.info(
        f'Pulled runtime configs to directory: {deployment.paths.dirs["runtime-configs"]}/{config_name}'
    )


@runtime_config_command_group.command("publish")
@deployment_name_option("to publish previously saved runtime configs")
@click.option(
    "--config-name",
    "config_name",
    required=True,
    help="Saved runtime configs to publish into the deployment",
)
@timeout_option(default=300)
@pass_rib_mode
def publish_runtime_configs(
    rib_mode: str,
    deployment_name: str,
    config_name: str,
    timeout: int,
) -> None:
    """
    publish previously saved runtime configs to each of the RACE nodes in a deployment.
    """
    # TODO: add support for publishing to a subset of nodes, similar to publish_configs.
    logger.info(
        f'Publishing runtime configs "{config_name}" to {rib_mode} deployment {deployment_name}...'
    )

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    try:
        deployment.push_runtime_configs(config_name, timeout)
    except error_utils.RIB000 as error:
        logger.error(error)
        logger.error('nodes must be in "ready to publish configs" state.')
        logger.error(
            f"did you remember to call `rib deployment {rib_mode} clear --name {deployment_name}`?"
        )
        exit(1)

    logger.info(
        f'Published runtime configs "{config_name}" to {rib_mode} deployment {deployment_name}'
    )
    logger.info(
        f"run `rib deployment {rib_mode} config install --name {deployment_name}` to install the configs before calling start"
    )


@runtime_config_command_group.command("list")
@deployment_name_option(
    "for which to list the runtime configs that have been previously pulled"
)
@pass_rib_mode
def list_runtime_configs(
    rib_mode: str,
    deployment_name: str,
) -> None:
    """
    list all the runtime configs that have been previously pulled from a deployment.
    """
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    runtime_config_dirs = deployment.list_runtime_configs()

    if len(runtime_config_dirs):
        for dir in runtime_config_dirs:
            logger.info(dir)
    else:
        logger.info("No runtime configs found")
        exit(1)

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
    Deployment comms commands group is responsible for execute remote procedural calls (RPC)
    directly against comms channels
"""

# Python Library Imports
import click
import logging
from typing import Optional, List

# Local Python Library Imports
from rib.commands.deployment_options import (
    deployment_name_option,
    nodes_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils.general_utils import stringify_nodes


logger = logging.getLogger(__name__)


###
# Comms Commands
###


@click.group("comms")
def comms_command_group() -> None:
    """Commands for executing remote commands directly against comms channels"""


@comms_command_group.command("enable")
@deployment_name_option("enable a channel")
@nodes_option("enable a channel")
@click.option(
    "--channel",
    "channel_gid",
    help="ID of the channel to enable",
    required=True,
    type=str,
)
@pass_rib_mode
def enable_channel(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    channel_gid: str,
) -> None:
    """
    Enable a comms channel
    """

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)

    logger.info(
        f"Enabling channel {channel_gid} on {stringify_nodes(nodes)} in deployment: "
        f"{deployment_name} ({rib_mode})"
    )
    deployment.rpc.enable_channel(channel_gid=channel_gid, nodes=nodes)


@comms_command_group.command("disable")
@deployment_name_option("disable a channel")
@nodes_option("disable a channel")
@click.option(
    "--channel",
    "channel_gid",
    help="ID of the channel to disable",
    required=True,
    type=str,
)
@pass_rib_mode
def disable_channel(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    channel_gid: str,
) -> None:
    """
    Disable a comms channel
    """

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)

    logger.info(
        f"Disabling channel {channel_gid} on {stringify_nodes(nodes)} in deployment: "
        f"{deployment_name} ({rib_mode})"
    )
    deployment.rpc.disable_channel(channel_gid=channel_gid, nodes=nodes)


@comms_command_group.command("deactivate")
@deployment_name_option("deactivate a channel")
@nodes_option("deactivate a channel")
@click.option(
    "--channel",
    "channel_gid",
    help="ID of the channel to deactivate",
    required=True,
    type=str,
)
@pass_rib_mode
def deactivate_channel(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    channel_gid: str,
) -> None:
    """
    Deactivate a comms channel
    """

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)

    logger.info(
        f"Deactivating channel {channel_gid} on {stringify_nodes(nodes)} in deployment: "
        f"{deployment_name} ({rib_mode})"
    )
    deployment.rpc.deactivate_channel(
        channel_gid=channel_gid,
        nodes=nodes,
    )


@comms_command_group.command("destroy")
@deployment_name_option("destroy a link")
@nodes_option("destroy a link")
@click.option(
    "--link",
    "link_id",
    help="ID of the link to destroy (or <ChannelId>/* to destroy all links for a channel)",
    required=True,
    type=str,
)
@pass_rib_mode
def destroy_link(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    link_id: str,
) -> None:
    """
    Destroy a comms link (or all links for a comms channel)
    """

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)

    if link_id.endswith("/*"):
        channel_gid = link_id[0:-2]
        logger.info(
            f"Destroying all links for channel {channel_gid} on {stringify_nodes(nodes)} in "
            f"deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Destroying link {link_id} on {stringify_nodes(nodes)} in deployment: "
            f"{deployment_name} ({rib_mode})"
        )

    deployment.rpc.destroy_link(
        link_id=link_id,
        nodes=nodes,
    )


@comms_command_group.command("close")
@deployment_name_option("close a connection")
@nodes_option("close a connection")
@click.option(
    "--connection",
    "connection_id",
    help="ID of the connection to close",
    required=True,
    type=str,
)
@pass_rib_mode
def close_connection(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    connection_id: str,
) -> None:
    """
    Close a comms connection (or all connections for a comms link)
    """

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)

    if connection_id.endswith("/*"):
        link_id = connection_id[0:-2]
        logger.info(
            f"Closing all connections for link {link_id} on {stringify_nodes(nodes)} in deployment: "
            f"{deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Closing connection {connection_id} on {stringify_nodes(nodes)} in deployment: "
            f"{deployment_name} ({rib_mode})"
        )

    deployment.rpc.close_connection(
        connection_id=connection_id,
        nodes=nodes,
    )

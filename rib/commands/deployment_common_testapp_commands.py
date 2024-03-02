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
    Common deployment testapp commands
"""

# Python Library Imports
from typing import List, Optional
import click
import logging

# Local Python Library Imports
from rib.commands.deployment_options import (
    deployment_name_option,
    nodes_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import general_utils


logger = logging.getLogger(__name__)


###
# Generic Deployment Testapp Commands
###


@click.group("testapp")
def testapp_command_group() -> None:
    """Commands for testapp functionality with nodes"""


@testapp_command_group.command("configure")
@deployment_name_option("configure RACE test application")
@nodes_option("testapp configure")
@click.option(
    "--period",
    default=None,
    help="Test App's time between status publications, in seconds",
    type=click.IntRange(0, 3_600),
)
@click.option(
    "--ttl-factor",
    default=None,
    help="The factor to multiply the period by to get the TTL",
)
@click.option(
    "--reset",
    flag_value=True,
    help="Reset node's testapp-configs to default",
)
@click.option(
    "--force",
    flag_value=True,
    help="Configure testapp-config regardless of node status",
)
@pass_rib_mode
def configure_testapp_configs(
    deployment_name: str,
    rib_mode: str,
    nodes: Optional[List[str]],
    period: int,
    ttl_factor: int,
    reset: bool,
    force: bool,
):
    """
    "re-configure a node's testapp
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Configuring racetestapp-config for nodes {general_utils.stringify_nodes(nodes)} in Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Configuring racetestapp-config for all nodes in Deployment: {deployment_name} ({rib_mode})"
        )

    if reset:
        # Warn user about reset behavior in relation to ttl and period
        if reset and (ttl_factor or period):
            click.confirm(
                "Reset takes priority over user input, do you wish to set to defaults?",
                abort=True,
            )

    deployment.update_testapp_config(
        nodes=nodes, period=period, ttl_factor=ttl_factor, reset=reset, force=force
    )
    logger.info("Updated testapp-configs")

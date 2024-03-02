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
    Deployment logs command group is responsible for manipulating logs for RACE
    nodes in a deployment
"""

# Python Library Imports
import click
import logging
from datetime import datetime
from typing import List, Optional

# Local Python Library Imports
from rib.commands.common_options import timeout_option, generate_timestamp
from rib.commands.deployment_options import (
    deployment_name_option,
    nodes_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment


logger = logging.getLogger(__name__)


###
# Log Commands
###


@click.group("logs")
def logs_command_group() -> None:
    """Commands for manipulating RACE logs"""


@logs_command_group.command("backup")
@deployment_name_option("backup logs")
@nodes_option("backup logs")
@click.option(
    "--backup-id",
    required=False,
    default=generate_timestamp,
    type=str,
    help="Identifier to use for backed up logs directory name (defaults to current time)",
)
@click.option("--force", flag_value=True, help="Force log backup?")
@timeout_option()
@click.option(
    "--yes", "-y", flag_value=True, help="Accept AWS egress cost prompt", hidden=True
)
@pass_rib_mode
def backup_logs(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    backup_id: str,
    force: bool,
    timeout: int,
    yes: bool,
) -> None:
    """
    Backup RACE application logs
    """

    logger.info("Backing Up Log Files")

    if rib_mode == "aws" and not yes:
        click.secho(
            "Backing up logs out of AWS will incur a potentially significant egress data cost.",
            fg="yellow",
        )
        click.confirm("Do you want to proceed?", abort=True)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.rotate_logs(
        backup_id=backup_id,
        delete=False,
        force=force,
        nodes=nodes,
        timeout=timeout,
    )

    logger.info(f"Backed Up Log Files to directory {backup_id}")


@logs_command_group.command("delete")
@deployment_name_option("delete logs")
@nodes_option("delete logs")
@click.option("--force", flag_value=True, help="Force log deletion?")
@timeout_option()
@pass_rib_mode
def delete_logs(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    force: bool,
    timeout: int,
) -> None:
    """
    Delete RACE application logs
    """

    logger.info("Deleting Log Files")

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.rotate_logs(
        backup_id="",
        delete=True,
        force=force,
        nodes=nodes,
        timeout=timeout,
    )

    logger.info("Deleted Log Files")


@logs_command_group.command("rotate")
@deployment_name_option("rotate logs")
@nodes_option("rotate logs")
@click.option(
    "--backup-id",
    required=False,
    default=generate_timestamp,
    type=str,
    help="Identifier to use for backed up logs directory name (defaults to current time)",
)
@click.option("--force", flag_value=True, help="Force log rotation?")
@timeout_option()
@click.option(
    "--yes", "-y", flag_value=True, help="Accept AWS egress cost prompt", hidden=True
)
@pass_rib_mode
def rotate_logs(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    backup_id: str,
    force: bool,
    timeout: int,
    yes: bool,
) -> None:
    """
    Rotate (backup and delete) RACE application logs
    """

    logger.info("Rotating Log Files")

    if rib_mode == "aws" and not yes:
        click.secho(
            "Backing up logs out of AWS will incur a potentially significant egress data cost.",
            fg="yellow",
        )
        click.confirm("Do you want to proceed?", abort=True)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.rotate_logs(
        backup_id=backup_id,
        delete=True,
        force=force,
        nodes=nodes,
        timeout=timeout,
    )

    logger.info(
        f'Rotated Log Files to directory: {deployment.paths.dirs["previous-runs"]}/{backup_id}'
    )

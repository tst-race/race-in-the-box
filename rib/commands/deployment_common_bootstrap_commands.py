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
    Common deployment bootstrap commands
"""

# Python Library Imports
import click
import logging
import random
import string

# Local Python Library Imports
from rib.commands.deployment_options import deployment_name_option, pass_rib_mode
from rib.deployment.rib_deployment import RibDeployment


logger = logging.getLogger(__name__)


###
# Generic Deployment Bootstrap Commands
###


@click.group("bootstrap")
def bootstrap_command_group() -> None:
    """Commands for bootstrapping RACE nodes"""


def generate_random_passphrase() -> str:
    """
    Purpose:
        Generates a random bootstrap passphrase
    Args:
        N/A
    Returns:
        Randomly generated passphrase
    """
    passphrase = "".join(random.choices(string.ascii_letters, k=20))
    logger.info(f"Using randomly generated passphrase: {passphrase}")
    return passphrase


@bootstrap_command_group.command("node")
@deployment_name_option("bootstrap a node")
@click.option(
    "--introducer",
    required=True,
    help="Node to act as the introducer for the target node",
)
@click.option(
    "--target",
    required=True,
    help="Node to be introduced to the RACE network",
)
@click.option(
    "--passphrase",
    default=generate_random_passphrase,
    required=False,
    help="Passphrase to use for bootstrapping",
)
@click.option(
    "--architecture",
    default="auto",
    required=False,
    type=click.Choice(["x86_64", "arm64-v8a", "auto"]),
    help="Architecture of node to bootstrap",
)
@click.option(
    "--channel-id",
    default="",
    required=False,
    help="Preferred channel for bootstrapping (first one found will be used if none specified)",
)
@click.option(
    "--timeout",
    default=600,
    required=False,
    type=int,
    help="Bootstrap timeout",
)
@click.option(
    "--force",
    help="Force bootstrap",
    flag_value=True,
)
@pass_rib_mode
def bootstrap_node(
    deployment_name: str,
    rib_mode: str,
    force: bool,
    introducer: str,
    target: str,
    passphrase: str,
    architecture: str,
    channel_id: str,
    timeout: int,
):
    """
    Bootstrap a non-RACE node into the RACE network
    """

    click.echo("Bootstrapping non-RACE Node Into RACE Network")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.bootstrap_node(
        force=force,
        introducer=introducer,
        target=target,
        passphrase=passphrase,
        architecture=architecture,
        bootstrapChannelId=channel_id,
        timeout=timeout,
    )

    click.echo("Bootstrapped Node Into RACE Network")

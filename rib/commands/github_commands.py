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
    The GitHub command group is responsible for configuring GitHub and RiB connectivity
"""

# Python Library Imports
import click
import logging

# Local Python Library Imports
from rib.utils import general_utils, github_utils


logger = logging.getLogger(__name__)


###
# GitHub Commands
###


@click.group("github")
def github_command_group() -> None:
    """Commands for configuring GitHub"""


@github_command_group.command("config")
@click.option(
    "--access-token",
    default=None,
    help="Access token for GitHub",
    type=str,
)
@click.option(
    "--username",
    default=None,
    help="GitHub account username",
    type=str,
)
@click.option(
    "--default-org",
    default=None,
    help="Default GitHub organization to use (if any)",
    type=str,
)
@click.option(
    "--default-race-images-org",
    default=None,
    help="Default GitHub organization to use for race-images (if different than the default org)",
    type=str,
)
@click.option(
    "--default-race-images-repo",
    default=None,
    help="Default GitHub repository to use for race-images (if different than 'race-images')",
    type=str,
)
@click.option(
    "--default-race-images-tag",
    default=None,
    help="Default race-images Docker tag (if different than 'latest')",
    type=str,
)
@click.option(
    "--default-race-core-org",
    default=None,
    help="Default GitHub organization to use for race-core (if different than the default org)",
    type=str,
)
@click.option(
    "--default-race-core-repo",
    default=None,
    help="Default GitHub repository to use for race-core (if different than 'race-core')",
    type=str,
)
@click.option(
    "--default-race-core-source",
    default=None,
    help="Default source to use for race-core (if any)",
    type=str,
)
def config(**kwargs):
    """Update GitHub configuration"""
    if kwargs:
        new_config = github_utils.GitHubConfig()
        for key, value in kwargs.items():
            if not hasattr(new_config, key):
                logger.error(
                    f"GitHubConfig and `github config` command have diverged, unrecognized key: {key}"
                )
                continue
            if value is not None:
                setattr(new_config, key, value)

        github_utils.update_github_config(new_config)
        click.echo("GitHub config has been updated")

    else:
        click.echo("No changes made to GitHub config")


@github_command_group.command("list")
def list_config():
    """Show GitHub configuration"""
    click.echo(
        general_utils.pretty_print_json(github_utils.read_github_config().dict())
    )

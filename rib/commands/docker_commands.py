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
        Docker Command Group is responsible for building and managing docker images
        associated with the RACE project. Commands will enable the pulling of images from
        the container registry, building them locally if necessary. pushing them to the
        container registry, and more.
"""

# Python Library Imports
import click

# Local Python Library Imports
from rib.utils import docker_utils, github_utils


###
# Docker Commands
###


@click.command("verify")
@click.pass_context
def verify(cli_context: click.core.Context) -> None:
    """
    Verify docker is installed and running. Also verify that the user is logged
    into the container registry to be able to pull/push images
    """

    click.echo("Verifying Docker Status (Is installed and running)")
    docker_utils.get_docker_client()
    click.echo("Docker Status Verified Successfully")


@click.command("login")
@click.pass_context
def login(cli_context: click.core.Context) -> None:
    """
    Login to the RACE container registry
    """

    click.echo("Log Into Docker Container Registry")
    docker_utils.login_docker_registry(
        username=github_utils.get_username(),
        password=github_utils.get_access_token(),
        registry=cli_context.obj.config.CONTAINER_REGISTRY_URL,
        user_state_path=cli_context.obj.config.RIB_PATHS["docker"]["user_state"],
    )
    click.echo("Log Into Docker Container Successful")

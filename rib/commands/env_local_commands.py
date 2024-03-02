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
        Local Environment Command Group is responsible for providing information about the
        Host machine and what RiB fetaures are supported
"""

# Python Library Imports
import click

# Local Python Library Imports
from rib.utils import docker_utils, general_utils
from rib.commands.common_options import detail_level_option, format_option
from rib.config import rib_host_env

###
# Local Environment Commands
###


@click.command("capabilities")
@format_option()
def capabilities(format: str) -> None:
    """Report capabilities of RiB based on host machine info"""

    info = rib_host_env.get_rib_capabilities_report()

    if format == "json":
        click.echo(general_utils.pretty_print_json(info))
    else:
        click.echo(general_utils.pretty_print_yaml(info))


@click.command("info")
@format_option()
def info(format: str) -> None:
    """Report information about the host machine"""

    info = rib_host_env.get_rib_env_config()

    if format == "json":
        click.echo(general_utils.pretty_print_json(info))
    else:
        click.echo(general_utils.pretty_print_yaml(info))


@click.command("status")
@detail_level_option()
@format_option()
def status(detail_level: int, format: str) -> None:
    """Report Status Of An Local Environment e.g. docker ps and adb devices"""

    status = {}
    docker_containers = docker_utils.get_all_running_container_names()

    status["Docker Containers"] = docker_containers
    # TODO add adb devices

    if format == "json":
        click.echo(general_utils.pretty_print_json(status))
    else:
        click.echo(general_utils.pretty_print_yaml(status))

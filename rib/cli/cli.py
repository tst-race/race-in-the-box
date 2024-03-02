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
    Entrypoint script for RACE in the Box. Is the CLI interface for allowing
    performers of the RACE project build, test, configure, etc the RACE system
    in a deterministic way for development and deployment settings.

Steps:
    - Enter the CLI Entrypoint
    - Initialize or Load Configs
        - Including Override any new values
    - Parse Command Structure (Nested, args, etc)
    - Execute Command
    - Return/Exit

Script Call:
    python3 cli.py COMMAND_GROUP COMMAND [ARGS]...
    OR
    rib COMMAND_GROUP COMMAND [ARGS]...

Example Call:
    python3 cli/run_race_in_the_box.py --help
    OR
    rib --help
"""

# Python Library Imports
import click
import click_completion
import logging
import os
import sys
import time
from datetime import timedelta
from typing import Optional

# Local Python Library Imports
import rib.commands as rib_commands
import rib.commands.help_commands as help_commands
from rib.commands.alias_group import AliasGroup
from rib.state.rib_state import RaceInTheBoxState
from rib.utils import log_utils, rib_utils


###
# Globals
###


RIB_CONFIG = rib_utils.load_race_global_configs()

# `rib deployment <command>` shortcuts rely on the RiB mode being set in the
# environment variable RIB_MODE and the deployment name in the DEPLOYMENT_NAME
# environment variable.
RIB_MODE = os.getenv("RIB_MODE")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")


def is_valid_rib_mode(rib_mode: Optional[str]) -> bool:
    """Check if RiB mode value is a valid value"""
    return rib_mode and rib_mode in ("local", "aws")


###
# CLI Setup
###


click_completion.init()


###
# CLI Entrypoint
###


@click.group(invoke_without_command=False)
@click.version_option(RIB_CONFIG.RIB_VERSION)
@click.pass_context
def race_in_the_box_cli(cli_context: click.core.Context) -> None:
    """
    RiB entrypoint command
    """

    # Get context about the command being run (which Click had a better
    # way to do this)
    # cli_command = " ".join(sys.argv[:])
    # command_root = cli_context.command_path
    command_subcommand = cli_context.invoked_subcommand

    if command_subcommand != "config":
        cli_context.obj.verify_rib_state()


###
# Command Groups
###


@race_in_the_box_cli.group("aws", cls=AliasGroup)
@click.pass_context
def aws_command_group(cli_context: click.core.Context) -> None:
    """
    AWS Command Group is responsible for interacting with AWS using RiB
    """

    # aws_commands = cli_context.command.list_commands(cli_context)


@race_in_the_box_cli.group("config", cls=AliasGroup)
@click.pass_context
def config_command_group(cli_context: click.core.Context) -> None:
    """
    Config Command Group is responsible for generating and verifying configs
    for the RACE network.
    """

    # config_commands = cli_context.command.list_commands(cli_context)


@race_in_the_box_cli.group("deployment", cls=AliasGroup)
@click.pass_context
def deployment_command_group(cli_context: click.core.Context) -> None:
    """
    Deployment Command Group is responsible for configuring, launching, and tearing
    down a RACE in the Box deployment. This includes choosing the plugins, configuration,
    size, etc.
    """

    if is_valid_rib_mode(RIB_MODE) and DEPLOYMENT_NAME:
        cli_context.obj.rib_mode = RIB_MODE

    # deployment_commands = cli_context.command.list_commands(cli_context)


@deployment_command_group.group("aws", cls=AliasGroup)
@click.pass_context
def deployment_aws_command_group(cli_context: click.core.Context) -> None:
    """Commands for creating and manipulating AWS deployments"""

    cli_context.obj.rib_mode = "aws"


@deployment_command_group.group("local", cls=AliasGroup)
@click.pass_context
def deployment_local_command_group(cli_context: click.core.Context) -> None:
    """Commands for creating and manipulating local deployments"""

    cli_context.obj.rib_mode = "local"


@race_in_the_box_cli.group("docker", cls=AliasGroup)
@click.pass_context
def docker_command_group(cli_context: click.core.Context) -> None:
    """
    Docker Command Group is responsible for building and managing docker images
    associated with the RACE project. Commands will enable the pulling of images from
    the container registry, building them locally if necessary. pushing them to the
    container registry, and more.
    """

    # docker_commands = cli_context.command.list_commands(cli_context)


@race_in_the_box_cli.group("env", cls=AliasGroup)
@click.pass_context
def env_command_group(cli_context: click.core.Context) -> None:
    """
    Environment Command Group is responsible for configuring and preparing
    environments in which RACE deployments can be run.
    """

    # env_commands = cli_context.command.list_commands(cli_context)


@env_command_group.group("aws", cls=AliasGroup)
@click.pass_context
def env_aws_command_group(cli_context: click.core.Context) -> None:
    """
    AWS Environment Command Group is responsible for configuring and provisioning
    cloud environments in AWS for RACE deployments.
    """

    # env_aws_commands = cli_context.command.list_commands(clic_context)


@env_command_group.group("local", cls=AliasGroup)
@click.pass_context
def env_local_command_group(cli_context: click.core.Context) -> None:
    """
    Local Environment Command Group provides information about the host machine
    to explain what RiB features are usable on the machine
    """

    # env_local_commands = cli_context.command.list_commands(clic_context)


@race_in_the_box_cli.group("race", cls=AliasGroup)
@click.pass_context
def race_command_group(cli_context: click.core.Context) -> None:
    """
    RACE Command Group is responsible for information about RACE system (e.g.
    versions)
    """

    # race_commands = cli_context.command.list_commands(cli_context)


@race_in_the_box_cli.group("range-config", cls=AliasGroup)
def range_config_command_group() -> None:
    """Commands for creating and manipulating range-configs"""


@race_in_the_box_cli.group("system", cls=AliasGroup)
@click.pass_context
def system_command_group(cli_context: click.core.Context) -> None:
    """
    System Command Group is responsible for verifying and configuring the user's system.
    """

    # system_commands = cli_context.command.list_commands(cli_context)


@race_in_the_box_cli.group("test", cls=AliasGroup)
@click.pass_context
def testing_command_group(cli_context: click.core.Context) -> None:
    """
    Test Command Group is deprecated. Please use 'rib deployment <mode> test --help' to see new syntax
    """

    # testing_commands = cli_context.command.list_commands(cli_context)


###
# CLI Startup
###


def setup_common_deployment_commands(group: click.Group) -> None:
    """
    Purpose:
        Setup common deployment commands under a mode-specific deployment command group
    Args:
        group: Base deployment command group
    Return:
        N/A
    """
    # Deployment Commands
    group.add_command(rib_commands.deployment_common_commands.copy, aliases=["cp"])
    group.add_command(rib_commands.deployment_common_commands.clear)
    group.add_command(rib_commands.deployment_common_commands.reset)
    group.add_command(rib_commands.deployment_common_commands.kill)
    group.add_command(rib_commands.deployment_common_commands.info)
    group.add_command(
        rib_commands.deployment_common_commands.list_deployments, aliases=["ls"]
    )
    group.add_command(rib_commands.deployment_common_commands.refresh_plugins)
    group.add_command(
        rib_commands.deployment_common_commands.notify_epoch, aliases=["epoch"]
    )
    group.add_command(rib_commands.deployment_common_commands.remove, aliases=["rm"])
    group.add_command(rib_commands.deployment_common_commands.rename, aliases=["mv"])
    group.add_command(rib_commands.deployment_common_commands.start)
    group.add_command(rib_commands.deployment_common_commands.stop)
    group.add_command(rib_commands.deployment_common_commands.set_timezone)

    group.add_command(
        rib_commands.deployment_common_bridged_commands.bridged_command_group
    )

    # Command groups
    group.add_command(
        rib_commands.deployment_common_bootstrap_commands.bootstrap_command_group
    )
    group.add_command(
        rib_commands.deployment_common_config_commands.config_command_group
    )
    group.add_command(rib_commands.deployment_common_link_commands.link_command_group)
    group.add_command(rib_commands.deployment_common_logs_commands.logs_command_group)
    group.add_command(
        rib_commands.deployment_common_message_commands.message_command_group
    )
    group.add_command(
        rib_commands.deployment_common_status_commands.status_command_group
    )
    group.add_command(rib_commands.deployment_common_comms_commands.comms_command_group)
    group.add_command(rib_commands.deployment_common_test_commands.test_command_group)
    group.add_command(
        rib_commands.deployment_common_testapp_commands.testapp_command_group
    )
    group.add_command(
        rib_commands.deployment_common_daemon_commands.daemon_command_group
    )
    group.add_command(
        rib_commands.deployment_common_voa_commands.deployment_voa_command_group
    )


@click.command(
    add_help_option=False,
    context_settings=dict(ignore_unknown_options=True),
    hidden=True,
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def deprecated_test_command(cli_context: click.core.Context, args):
    """
    Print suggestion message for updated test command syntax
    """
    rib_mode = "local"
    if cli_context.obj and cli_context.obj.rib_mode:
        rib_mode = cli_context.obj.rib_mode
    click.echo(
        f"No such command {cli_context.command_path!r}. 'rib test' is deprecated. "
        f"Did you mean 'rib deployment {rib_mode} test'?"
    )
    cli_context.exit(1)


@click.command(
    add_help_option=False,
    context_settings=dict(ignore_unknown_options=True),
    hidden=True,
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def deprecated_aws_env_command(cli_context: click.core.Context, args):
    """
    Print suggestion message for updated env aws command syntax
    """
    click.echo(
        f"No such command {cli_context.info_name!r}. Did you mean 'rib env aws'?"
    )
    cli_context.exit(1)


@click.command(
    add_help_option=False,
    context_settings=dict(ignore_unknown_options=True),
    hidden=True,
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def deprecated_deployment_command(cli_context: click.core.Context, args):
    """
    Print suggestion message for updated deployment command syntax
    """
    rib_mode = "local"
    if cli_context.obj and cli_context.obj.rib_mode:
        rib_mode = cli_context.obj.rib_mode
    click.echo(
        f"No such command {cli_context.info_name!r}. "
        f"Did you mean 'rib deployment {rib_mode} {cli_context.info_name}'?"
    )
    cli_context.exit(1)


def setup_deprecated_deployment_commands(group: click.Group) -> None:
    """
    Purpose:
        Setup legacy deployment "commands" to recommend the updated command to the user
    Args:
        group: Base deployment command group
    Return:
        N/A
    """

    group.add_command(deprecated_deployment_command, name="active")
    group.add_command(deprecated_deployment_command, name="bootstrap")
    group.add_command(deprecated_deployment_command, name="config")
    group.add_command(deprecated_deployment_command, name="copy", aliases=["cp"])
    group.add_command(deprecated_deployment_command, name="create")
    group.add_command(deprecated_deployment_command, name="down")
    group.add_command(deprecated_deployment_command, name="kill")
    group.add_command(deprecated_deployment_command, name="logs")
    group.add_command(deprecated_deployment_command, name="info")
    group.add_command(deprecated_deployment_command, name="list", aliases=["ls"])
    group.add_command(deprecated_deployment_command, name="message")
    group.add_command(deprecated_deployment_command, name="pull")
    group.add_command(deprecated_deployment_command, name="push")
    group.add_command(deprecated_deployment_command, name="refresh-plugins")
    group.add_command(deprecated_deployment_command, name="remove", aliases=["rm"])
    group.add_command(deprecated_deployment_command, name="rename", aliases=["mv"])
    group.add_command(deprecated_deployment_command, name="start")
    group.add_command(deprecated_deployment_command, name="status")
    group.add_command(deprecated_deployment_command, name="stop")
    group.add_command(deprecated_deployment_command, name="up")


def setup_race_in_the_box_cli() -> None:
    """
    Purpose:
        Build Command Groups for RiB CLI. This includes nesting the commands
        in order so that CLI commands can be utilized similar to docker
    Args:
        N/A
    Returns:
        N/A
    """

    # AWS Commands
    aws_command_group.add_command(rib_commands.aws_commands.init)
    aws_command_group.add_command(rib_commands.aws_commands.info)
    aws_command_group.add_command(rib_commands.aws_commands.verify)
    aws_command_group.add_command(
        rib_commands.aws_topology_commands.topology_command_group
    )
    aws_command_group.add_command(deprecated_aws_env_command, name="env")

    # Config Commands
    config_command_group.add_command(rib_commands.config_commands.init)
    config_command_group.add_command(
        rib_commands.config_commands.list_config, aliases=["ls"]
    )
    config_command_group.add_command(rib_commands.config_commands.verify)
    config_command_group.add_command(rib_commands.config_commands.update)

    # Deployment Auto Commands
    if is_valid_rib_mode(RIB_MODE) and DEPLOYMENT_NAME:
        setup_common_deployment_commands(deployment_command_group)

        if RIB_MODE == "aws":
            deployment_command_group.add_command(
                rib_commands.deployment_aws_commands.up
            )
            deployment_command_group.add_command(
                rib_commands.deployment_aws_commands.down
            )
        elif RIB_MODE == "local":
            deployment_command_group.add_command(
                rib_commands.deployment_local_commands.up
            )
            deployment_command_group.add_command(
                rib_commands.deployment_local_commands.down
            )

    else:
        setup_deprecated_deployment_commands(deployment_command_group)

    # Deployment AWS Commands
    deployment_aws_command_group.add_command(
        rib_commands.deployment_aws_commands.active
    )
    deployment_aws_command_group.add_command(
        rib_commands.deployment_aws_commands.create
    )
    deployment_aws_command_group.add_command(rib_commands.deployment_aws_commands.up)
    deployment_aws_command_group.add_command(rib_commands.deployment_aws_commands.down)
    setup_common_deployment_commands(deployment_aws_command_group)

    # Deployment Local Commands
    deployment_local_command_group.add_command(
        rib_commands.deployment_local_commands.active
    )
    deployment_local_command_group.add_command(
        rib_commands.deployment_local_commands.create
    )
    deployment_local_command_group.add_command(
        rib_commands.deployment_local_commands.down
    )
    deployment_local_command_group.add_command(
        rib_commands.deployment_local_commands.up
    )
    setup_common_deployment_commands(deployment_local_command_group)

    # Docker Commands
    docker_command_group.add_command(rib_commands.docker_commands.login)
    docker_command_group.add_command(rib_commands.docker_commands.verify)

    # Env AWS Commands
    env_aws_command_group.add_command(rib_commands.env_aws_commands.active)
    env_aws_command_group.add_command(
        rib_commands.env_aws_commands.copy, aliases=["cp"]
    )
    env_aws_command_group.add_command(rib_commands.env_aws_commands.create)
    env_aws_command_group.add_command(rib_commands.env_aws_commands.info)
    env_aws_command_group.add_command(
        rib_commands.env_aws_commands.list_envs, aliases=["ls"]
    )
    env_aws_command_group.add_command(rib_commands.env_aws_commands.provision)
    env_aws_command_group.add_command(
        rib_commands.env_aws_commands.remove, aliases=["rm"]
    )
    env_aws_command_group.add_command(
        rib_commands.env_aws_commands.rename, aliases=["mv"]
    )
    env_aws_command_group.add_command(rib_commands.env_aws_commands.runtime_info)
    env_aws_command_group.add_command(rib_commands.env_aws_commands.status)
    env_aws_command_group.add_command(rib_commands.env_aws_commands.unprovision)

    # Env Local Commands
    env_local_command_group.add_command(rib_commands.env_local_commands.capabilities)
    env_local_command_group.add_command(rib_commands.env_local_commands.info)
    env_local_command_group.add_command(rib_commands.env_local_commands.status)

    # GitHub Group
    race_in_the_box_cli.add_command(rib_commands.github_commands.github_command_group)

    # Help Command
    race_in_the_box_cli.add_command(help_commands.print_help)

    # RACE Commands
    race_command_group.add_command(rib_commands.race_commands.versions)

    # Range Config Commands
    range_config_command_group.add_command(rib_commands.range_config_commands.create)
    range_config_command_group.add_command(
        rib_commands.range_config_commands.list_deployment_config, aliases=["ls"]
    )
    range_config_command_group.add_command(rib_commands.range_config_commands.remove)

    # System Commands
    system_command_group.add_command(rib_commands.system_commands.verify)

    # Testing Commands
    testing_command_group.add_command(deprecated_test_command, name="deployment")
    testing_command_group.add_command(deprecated_test_command, name="ta2_channel")
    testing_command_group.add_command(deprecated_test_command, name="generate_plan")


def execute_race_in_the_box_cli() -> None:
    """
    Purpose:
        Sets up and then executes the race-in-the-box CLI application
    Args:
        N/A
    Returns:
        N/A
    """
    setup_race_in_the_box_cli()
    log_utils.setup_global_verbosity_option()

    config_obj = RaceInTheBoxState(RIB_CONFIG)
    log_utils.setup_logger(config_obj.config)

    # Special logger that doesn't print to console
    logger = logging.getLogger("command")

    # Record exactly what was run by the user to the log file (if not disabled)
    # A user may want to disable this if the command includes secrets (e.g., auth
    # tokens) and they don't want it to be logged
    if os.environ.get("RIB_DISABLE_COMMAND_LOG", "").lower() not in [
        "true",
        "yes",
        "1",
    ]:
        logger.info(" ".join(sys.argv))

    start_time = time.time()
    try:
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        race_in_the_box_cli(obj=config_obj)
    except Exception as err:
        logger.error(err)
        raise err
    finally:
        stop_time = time.time()
        duration = timedelta(seconds=stop_time - start_time)
        logger.debug(f"{get_command()} took {duration} to execute")


def get_command() -> str:
    """
    Purpose:
        Gets the command name from the sys.argv list without any flags/options
    Args:
        N/A
    Returns:
        Command name
    """
    command = []
    for argv in sys.argv:
        if argv.startswith("-"):
            break
        command.append(argv)
    # Ignore the first argv since it's going to be "/usr/local/bin/rib" and we want just "rib"
    return f"rib {' '.join(command[1:])}"

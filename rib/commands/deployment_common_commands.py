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
        Deployment Command Group is responsible for configuring, launching, and tearing
        down a RACE in the Box deployment. This includes choosing the plugins,
        configuration, size, etc.
"""

# Python Library Imports
import click
import logging
from typing import List, Optional
import pytz
from rib.commands.option_group import (
    MutuallyExclusiveOptions,
)

# Local Python Library Imports
from rib.commands.common_options import (
    cache_option,
    timeout_option,
)
from rib.commands.deployment_options import (
    deployment_name_option,
    nodes_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import (
    click_utils,
    general_utils,
    plugin_utils,
)


logger = logging.getLogger(__name__)


###
# Deployment Commands
###


@click.command("copy")
@click.option(
    "--current",
    "current_deployment_name",
    required=True,
    help="What is the existing deployment name",
)
@click.option(
    "--new",
    "new_deployment_name",
    required=True,
    help="What is the new deployment name",
)
@click.option("--force", "force", flag_value=True, help="Force Copy?")
@pass_rib_mode
@click.pass_context
def copy(
    cli_context: click.core.Context,
    rib_mode: str,
    current_deployment_name: str,
    new_deployment_name: str,
    force: bool,
) -> None:
    """
    Copy an existing Deployment to a new name
    """

    logger.info(
        f"Copying Deployment from {current_deployment_name} to {new_deployment_name} ({rib_mode})"
    )

    # Verifying current deployment exists and new doesnt
    current_deployment = RibDeployment.get_existing_deployment_or_fail(
        current_deployment_name, rib_mode
    )
    RibDeployment.ensure_deployment_not_existing_or_fail(new_deployment_name, rib_mode)

    # Copying Deployment
    current_deployment.copy(
        new_deployment_name, click_utils.get_run_command(cli_context), force=force
    )

    logger.info(
        f"Copied Deployment from {current_deployment_name} to {new_deployment_name} ({rib_mode})"
    )


@click.command("clear")
@deployment_name_option(
    "Clear configs and etc from Genesis nodes; configs, etc and artifacts from Non-Genesis nodes)"
)
@nodes_option("clear")
@click.option("--force", "force", flag_value=True, help="Force Clear?")
@pass_rib_mode
def clear(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    force: bool,
) -> None:
    """
    Clear configs and etc from Genesis nodes; configs, etc and artifacts from Non-Genesis nodes)
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Clearing Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Clearing All Nodes In Deployment: {deployment_name} ({rib_mode})")

    deployment.clear(nodes=nodes, force=force)

    if nodes:
        logger.info(
            f"Cleared Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Cleared All Nodes In Deployment: {deployment_name} ({rib_mode})")


@click.command("reset")
@deployment_name_option(
    "Reset nodes back to the post-up state (runtime configs are cleared, bootstrapped nodes have the app uninstalled)"
)
@nodes_option("reset")
@click.option("--force", "force", flag_value=True, help="Force Reset?")
@pass_rib_mode
def reset(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    force: bool,
) -> None:
    """
    Reset nodes back to the post-up state (runtime configs are cleared, bootstrapped nodes have the app uninstalled)
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Resetting Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Resetting All Nodes In Deployment: {deployment_name} ({rib_mode})"
        )

    deployment.reset(nodes=nodes, force=force)

    if nodes:
        logger.info(
            f"Reset Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Reset All Nodes In Deployment: {deployment_name} ({rib_mode})")


@click.command("kill")
@deployment_name_option("kill RACE nodes")
@nodes_option("kill", required=True)
@click.option("--force", "force", flag_value=True, help="Force Kill?")
@pass_rib_mode
def kill(
    rib_mode: str,
    deployment_name: str,
    nodes: List[str],
    force: bool,
) -> None:
    """
    Kill the RACE App on specific Nodes in a deployment
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    nodes = deployment.get_nodes_from_regex(nodes)
    logger.info(
        f"Killing Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
    )

    deployment.kill(nodes=nodes, force=force)

    logger.info(
        f"Killed Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
    )


@click.command("info")
@deployment_name_option("report configuration info")
@click.option(
    "--format",
    default="yaml",
    help="Format output as JSON or YAML",
    show_default=True,
    type=click.Choice(["json", "yaml"]),
)
@pass_rib_mode
def info(
    rib_mode: str,
    deployment_name: str,
    format: str,
) -> None:
    """Report Configuration & Metadata Info About A Deployment"""

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    info = {
        "config": deployment.config.dict(),
        "metadata": deployment.metadata.dict(),
    }

    if format == "json":
        click.echo(general_utils.pretty_print_json(info))
    else:
        click.echo(general_utils.pretty_print_yaml(info))


@click.command("list")
@pass_rib_mode
def list_deployments(
    rib_mode: str,
) -> None:
    """
    List configured deployments that can be launched
    """
    # Get the correct class based on mode
    rib_deployment_class = RibDeployment.get_deployment_class(rib_mode)

    # Getting all available deployments and listing
    deployments = rib_deployment_class.get_defined_deployments()
    if not deployments.compatible and not deployments.incompatible:
        click.echo("No Deployments Found")

    if deployments.compatible:
        click.echo("Compatible Deployments:")
        for deployment_name in sorted(deployments.compatible):
            click.echo(f"\t{deployment_name}")

    if deployments.incompatible:
        click.echo("Incompatible Deployments (from previous RiB versions):")
        for deployment in sorted(deployments.incompatible):
            click.echo(f"\t{deployment.name} (RiB {deployment.rib_version})")


@click.command("refresh-plugins")
@deployment_name_option("refresh plugins")
@cache_option()
@click.option("--unsafe", "force", flag_value=True, help="Force unsafe plugin refresh?")
@pass_rib_mode
def refresh_plugins(
    rib_mode: str,
    deployment_name: str,
    cache: plugin_utils.CacheStrategy,
    force: bool,
) -> None:
    """
    Refresh plugin for a deployment.

    For a local deployment this is like creating a new deployment with the same
    create command except the logs and configs are kept. Updated config gen scripts were
    copied in so you may run `rib deployment config generate` to recreate configs.

    For remote deployments this still copies all the plugin artifacts to your deployment
    directory but because complete images are used this does not update the nodes. You may
    artifact manager plugins with the deployment which will re-upload the new plugin
    artifacts and overwrite plugin artifacts on start
    """

    logger.info(f"Refreshing plugins of deployment: {deployment_name} ({rib_mode})")

    # Getting instance of existing deployment and status of the deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Check status before getting plugins, as it will break a running/up deployment
    if not force:
        deployment.status.verify_deployment_is_down("refresh plugins")

    deployment.get_plugins(cache=cache)
    deployment.update_race_json()
    deployment.create_distribution_artifacts()


@click.command("remove")
@deployment_name_option("remove")
@click.option("--force", "force", flag_value=True, help="Force Remove?")
@click.option(
    "--yes", "-y", flag_value=True, help="Accept legacy RiB version prompt", hidden=True
)
@pass_rib_mode
def remove(
    rib_mode: str,
    deployment_name: str,
    force: bool,
    yes: bool,
) -> None:
    """
    Remove configured deployment
    """
    logger.info(f"Removing Deployment: {deployment_name} ({rib_mode})")
    # Get the correct class based on mode
    rib_deployment_class = RibDeployment.get_deployment_class(rib_mode)
    if rib_deployment_class.deployment_exists(deployment_name):
        # Try to load it
        deployment = None
        try:
            deployment = rib_deployment_class.get_deployment(deployment_name)
        except:
            # Else it's a legacy deployment, remove by brute force
            if yes or click.confirm(
                "This Deployment was created with an older version of RiB. Are you sure you want to forcibly remove it?",
                abort=True,
            ):
                rib_deployment_class.remove_legacy_deployment(deployment_name)
            else:
                logger.error("Aborting")
                return

        if deployment:
            deployment.remove(force=force)
    else:
        click.secho(f"No Deployment exists: {deployment_name}", fg="yellow")

    logger.info(f"Removed Deployment: {deployment_name}")


@click.command("rename")
@click.option(
    "--old",
    "old_deployment_name",
    required=True,
    help="What is the existing deployment name",
)
@click.option(
    "--new",
    "new_deployment_name",
    required=True,
    help="What is the new deployment name",
)
@click.option("--force", "force", flag_value=True, help="Force Rename?")
@pass_rib_mode
def rename(
    rib_mode: str,
    old_deployment_name: str,
    new_deployment_name: str,
    force: bool,
) -> None:
    """
    Rename an existing Deployment
    """

    logger.info(
        f"Renaming Deployment from {old_deployment_name} to {new_deployment_name} ({rib_mode})"
    )

    # Verifying old deployment exists and new doesn't
    old_deployment = RibDeployment.get_existing_deployment_or_fail(
        old_deployment_name, rib_mode
    )
    RibDeployment.ensure_deployment_not_existing_or_fail(new_deployment_name, rib_mode)

    # Renaming Deployment
    old_deployment.rename(new_deployment_name, force=force)

    logger.info(
        f"Renamed Deployment from {old_deployment_name} to {new_deployment_name} ({rib_mode})"
    )


timezone_opt_groups = MutuallyExclusiveOptions()
time_group = timezone_opt_groups.group("local time")
zone_group = timezone_opt_groups.group("timezone name")


@click.command("set-timezone")
@deployment_name_option("set timezone")
@nodes_option("set-timezone")
@pass_rib_mode
@time_group.option(
    "--local-time",
    "local_time",
    help="Set a new local node time, as the desired hour of the day (0-24)",
    required=False,
    type=click.IntRange(0, 24),
    default=None,
)
@zone_group.option(
    "--zone",
    "zone",
    help="Name of the timezone to be set on the node(s)",
    required=False,
    type=click.Choice(sorted(list(pytz.all_timezones_set)), case_sensitive=False),
    default=None,
)
@timezone_opt_groups.result(expose_value=False, required=True, name="")
def set_timezone(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    zone: Optional[str] = None,
    local_time: Optional[int] = None,
) -> None:
    """
    Set node local timezone
    """
    logger.info("Starting timezone change")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Setting Timezone For Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Setting Timezone For All Nodes In Deployment: {deployment_name} ({rib_mode})"
        )

    deployment.set_timezone(
        nodes=nodes,
        zone=zone,
        local_time=local_time,
    )


@click.command("start")
@deployment_name_option("start RACE nodes")
@nodes_option("start")
@click.option("--force", "force", flag_value=True, help="Force start?")
@timeout_option(default=300)
@pass_rib_mode
@click.pass_context
def start(
    cli_context: click.core.Context,
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    force: bool,
    timeout: int,
) -> None:
    """
    Start the RACE App on all Nodes configured in a deployment
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Starting Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Starting All Nodes In Deployment: {deployment_name} ({rib_mode})")

    deployment.start(
        last_start_command=click_utils.get_run_command(cli_context),
        nodes=nodes,
        force=force,
        timeout=timeout,
    )

    if nodes:
        logger.info(
            f"Started Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Started All Nodes In Deployment: {deployment_name} ({rib_mode})")


@click.command("stop")
@deployment_name_option("stop RACE nodes")
@nodes_option("stop")
@click.option("--force", "force", flag_value=True, help="Force Stop?")
@timeout_option(default=300)
@pass_rib_mode
def stop(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    force: bool,
    timeout: int,
) -> None:
    """
    Stop the RACE App on specified (or all) Nodes configured in a deployment
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Stopping Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Stopping All Nodes In Deployment: {deployment_name} ({rib_mode})")

    deployment.stop(force=force, nodes=nodes, timeout=timeout)

    if nodes:
        logger.info(
            f"Stopped Nodes {general_utils.stringify_nodes(nodes)} In Deployment: {deployment_name} ({rib_mode})"
        )
    else:
        logger.info(f"Stopped All Nodes In Deployment: {deployment_name} ({rib_mode})")


@click.command("notify-epoch")
@deployment_name_option("notify RACE nodes of epoch")
@nodes_option("notify RACE nodes of epoch")
@click.option(
    "--data",
    "data",
    required=False,
    default="{}",
    help="Data to pass to the network manager plugin",
)
@pass_rib_mode
def notify_epoch(
    rib_mode: str,
    deployment_name: str,
    nodes: Optional[List[str]],
    data: str,
) -> None:
    """
    Stop the RACE App on specified (or all) Nodes configured in a deployment
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        logger.info(
            f"Notifying {general_utils.stringify_nodes(nodes)} of epoch in deployment: "
            f"{deployment_name} ({rib_mode})"
        )
    else:
        logger.info(
            f"Notifying all nodes of epoch in deployment: "
            f"{deployment_name} ({rib_mode})"
        )

    deployment.rpc.notify_epoch(
        nodes=nodes,
        data=data,
    )

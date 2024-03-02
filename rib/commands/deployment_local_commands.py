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
    Local deployment commands
"""

# Python Library Imports
import click
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Local Python Library Imports
from rib.commands.common_options import (
    cache_option,
    rib_mode_option,
    verbosity_option,
)
from rib.commands.deployment_options import (
    android_app_option,
    android_client_count_option,
    android_client_image_option,
    android_client_uninstalled_count_option,
    android_client_bridge_count_option,
    artifact_manager_kits_option,
    comms_channels_option,
    comms_kits_option,
    deployment_name_option,
    disabled_channels_option,
    enable_ui_option,
    fetch_plugins_on_start_option,
    linux_app_option,
    race_core_option,
    race_log_level_option,
    race_node_arch_option,
    registry_app_option,
    node_daemon_option,
    linux_client_count_option,
    linux_client_image_option,
    linux_client_uninstalled_count_option,
    linux_client_bridge_count_option,
    linux_server_count_option,
    linux_server_image_option,
    linux_server_uninstalled_count_option,
    linux_server_bridge_count_option,
    registry_client_count_option,
    registry_client_uninstalled_count_option,
    gpu_registry_client_count_option,
    registry_client_image_option,
    network_manager_kit_option,
    no_config_gen_option,
    range_config_option,
    validate_image_names,
    disable_config_encryption_option,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.rib_local_deployment import RibLocalDeployment
from rib.utils import (
    click_utils,
    error_utils,
    general_utils,
)
from rib.commands.option_group import (
    GroupedOptionCommand,
    MutuallyExclusiveOptions,
    OptionGroup,
)


logger = logging.getLogger(__name__)


@click.command("active")
def active() -> None:
    """
    Get active deployments to find which is running for each (or a specified) mode
    """
    logger.info("Getting Active Deployments")

    # Calling util to print all active deployments
    RibDeployment.print_active_deployments("local")


config_opts = OptionGroup("configs", name="Application Configuration Options")
artifacts = OptionGroup("artifacts", name="Artifact Revision Options")
node_def_strategy = MutuallyExclusiveOptions()
range_config_opts = node_def_strategy.group(
    key="range_config",
    name="Range-Config Definition Options",
    help="Use a range-config to define the nodes in the deployment",
)
node_counts = node_def_strategy.group(
    key="node_counts",
    name="Node Count Definition Options",
    help="Use node counts to define the nodes in the deployment",
)
images = OptionGroup("images", name="Docker Image Options")


@click.command("create", cls=GroupedOptionCommand)
@deployment_name_option("create")
@click.option("--force", "force", flag_value=True, help="overwrite existing deployment")
# config options
@disabled_channels_option(group=config_opts)
@fetch_plugins_on_start_option(group=config_opts)
@no_config_gen_option(group=config_opts)
@disable_config_encryption_option(group=config_opts)
@race_log_level_option(group=config_opts)
# artifact options
@race_core_option(
    command_help="What RACE core is the deployment testing?", group=artifacts
)
@cache_option(group=artifacts)
@network_manager_kit_option(group=artifacts)
@comms_channels_option(group=artifacts)
@comms_kits_option(group=artifacts)
@artifact_manager_kits_option(group=artifacts)
@android_app_option(group=artifacts)
@linux_app_option(group=artifacts)
@registry_app_option(group=artifacts)
@node_daemon_option(group=artifacts)
# image options
@android_client_image_option(group=images)
@linux_client_image_option(group=images)
@linux_server_image_option(group=images)
@registry_client_image_option(group=images)
# range-config options
@range_config_option(group=range_config_opts)
# node count options
@race_node_arch_option(group=node_counts)
@android_client_count_option(group=node_counts)
@android_client_uninstalled_count_option(group=node_counts)
@android_client_bridge_count_option(group=node_counts)
@enable_ui_option(
    command_help="Android clients for which to enable user input UI",
    group=node_counts,
    param="--android-client-enable-ui-for",
)
@linux_client_count_option(group=node_counts)
@linux_client_uninstalled_count_option(group=node_counts)
@linux_client_bridge_count_option(group=node_counts)
@linux_server_count_option(group=node_counts, required=False)
@linux_server_uninstalled_count_option(group=node_counts)
@linux_server_bridge_count_option(group=node_counts)
@registry_client_count_option(group=node_counts)
@registry_client_uninstalled_count_option(group=node_counts)
@gpu_registry_client_count_option(group=node_counts)
@node_def_strategy.result("node_def_strategy", expose_value=False)
@click.option(
    "--disable-elasticsearch-volume-mounts",
    "disable_elasticsearch_volume_mounts",
    flag_value=True,
    help="disable elasticsearch volume mounts",
)
@click.option(
    "--enable-gpu",
    required=False,
    flag_value=True,
    help="Enable GPU device access for RACE nodes",
)
@click.option(
    "--tmpfs",
    "tmpfs_size",
    required=False,
    default=None,
    type=int,
    help="If set, will create tmpfs mount at /tmpfs of specified size in bytes",
)
@click.option(
    "--disable-open-tracing",
    required=False,
    flag_value=True,
    help="Disable Open Tracing (Running without open tracing will break message verification in RiB)",
)
@click.pass_context
@validate_image_names
def create(
    cli_context: click.core.Context,
    deployment_name: str,
    force: bool,
    **kwargs: Dict[str, Any],
) -> None:
    """
    Create a New Deployment and configure it
    """

    # Do a check to ensure that if the user is enabling GPU, they have a valid os
    verify_gpu_settings(kwargs.get("enable_gpu", False), "local")

    # Make sure deployment doesn't already exist (or remove it if force)
    RibLocalDeployment.ensure_deployment_not_existing_or_remove(
        deployment_name, "local", force=force
    )

    host_has_dev_kvm = os.environ.get("HOST_HAS_DEV_KVM", "false") == "true"
    kwargs["android_client_accel"] = host_has_dev_kvm

    if (
        kwargs.get("android_client_count", 0) > 0
        and kwargs.get("android_client_count", 0)
        != kwargs.get("android_client_bridge_count", 0)
        and not host_has_dev_kvm
    ):
        click.secho(
            "WARNING: performance of Android clients will be poor without host hardware acceleration",
            fg="red",
        )

    click.echo(f"Creating Local Deployment: {deployment_name}")
    try:
        RibLocalDeployment.create(
            create_command=click_utils.get_run_command(cli_context),
            deployment_name=deployment_name,
            **kwargs,
        )
    except Exception as err:
        if isinstance(err, error_utils.RIB000):
            raise err from None
        # If this is *not* a RiB generated exception then just raise it, don't
        # wrap/swallow it.
        # TODO: where are non-RiB exceptions getting swallowed? Is this some weird click thing?
        #       if I don't do a try/except here then the cli just prints "Aborted!" which is...
        #       less than helpful. I have to explicitly print the exception to get the info.
        click.secho(f"ERROR: {err}", fg="red")
        raise
    click.echo(f"Created Local Deployment: {deployment_name}")
    click.echo(
        f"Run `rib-use local {deployment_name}` to enable shortcut commands for this deployment"
    )


@click.command("up")
@deployment_name_option("stand up")
@rib_mode_option()
@click.option(
    "--force",
    "force",
    flag_value=True,
    help="Forces up. Bypasses container/node status checks.",
)
@click.option(
    "--node",
    "nodes",
    multiple=True,
    required=False,
    type=str,
    default=None,
    help="What individual RACE node(s) to be stood up (or all if not specified)",
)
@click.option(
    "--no-publish",
    flag_value=True,
    help="If set, configs will not be published after upping",
)
@click.option(
    "--timeout",
    type=click.IntRange(0, 3_600),
    default=300,
    required=False,
    show_default=True,
    help="Timeout for operation (in seconds)",
)
@verbosity_option()
@click.pass_context
def up(
    cli_context: click.core.Context,
    deployment_name: str,
    rib_mode: str,
    force: bool,
    nodes: Optional[List[str]],
    no_publish: bool,
    timeout: int,
    verbosity: int,
) -> None:
    """
    Stage configs, run containers, and start API on all nodes configured in deployment
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        click.echo(
            f"Standing Up Nodes {general_utils.stringify_nodes(nodes)} in Deployment: {deployment_name}"
        )
    else:
        click.echo(f"Standing Up Deployment: {deployment_name}")

    deployment.up(
        force=force,
        last_up_command=click_utils.get_run_command(cli_context),
        nodes=nodes,
        no_publish=no_publish,
        timeout=timeout,
        verbose=verbosity,
    )

    if nodes:
        click.echo(f"Stood Up Nodes in Deployment: {deployment_name}")
    else:
        click.echo(f"Stood Up Deployment: {deployment_name}")


@click.command("down")
@deployment_name_option("tear down")
@rib_mode_option()
@click.option("--force", "force", flag_value=True, help="Force Down?")
@click.option(
    "--node",
    "nodes",
    multiple=True,
    required=False,
    type=str,
    default=None,
    help="What individual RACE node(s) to be stood up (or all if not specified)",
)
@click.option(
    "--timeout",
    type=click.IntRange(0, 3_600),
    default=300,
    required=False,
    show_default=True,
    help="Timeout for operation (in seconds)",
)
@verbosity_option()
def down(
    deployment_name: str,
    rib_mode: str,
    force: bool,
    nodes: Optional[List[str]],
    timeout: int,
    verbosity: int,
) -> None:
    """
    Clear staged configs and stop all containers running (if local)
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    if nodes:
        nodes = deployment.get_nodes_from_regex(nodes)
        click.echo(
            f"Tearing Down Nodes {general_utils.stringify_nodes(nodes)} in Deployment: {deployment_name}"
        )
    else:
        click.echo(f"Tearing Down Deployment: {deployment_name}")

    deployment.down(force=force, nodes=nodes, verbose=verbosity, timeout=timeout)

    if nodes:
        click.echo(f"Tore Down Nodes in Deployment: {deployment_name}")
    else:
        click.echo(f"Tore Down Deployment: {deployment_name}")


###
# Helper Methods
###


def verify_gpu_settings(gpu_enabled: bool, rib_mode: str) -> None:
    """
    Purpose:
        Checks that GPU is only enabled on Linux (in local mode).

    Args:
        gpu_enabled: if GPU is enabled
    """

    if (
        "Linux" not in os.environ.get("HOST_UNAME", "Unknown")
        and gpu_enabled
        and rib_mode == "local"
    ):
        click.secho(
            "ERROR: --gpu-enabled is only valid in Linux OS systems",
            fg="red",
        )
        sys.exit(1)

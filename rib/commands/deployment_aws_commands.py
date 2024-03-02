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
    AWS Deployment Command Group is responsible for configuring, standing up,
    and tearing down of AWS deployment for RiB.
"""

# Python Library Imports
import click
import logging
from typing import List

# Local Python Library Import
from rib.aws_env.rib_aws_env import RibAwsEnv
from rib.commands.common_options import (
    ansible_verbosity_option,
    cache_option,
    dry_run_option,
    timeout_option,
)
from rib.commands.deployment_options import (
    android_app_option,
    android_client_count_option,
    android_client_image_option,
    android_client_uninstalled_count_option,
    android_client_bridge_count_option,
    artifact_manager_kits_option,
    bastion_image_option,
    comms_channels_option,
    comms_kits_option,
    deployment_name_option,
    disabled_channels_option,
    enable_ui_option,
    fetch_plugins_on_start_option,
    linux_app_option,
    registry_app_option,
    registry_client_count_option,
    registry_client_uninstalled_count_option,
    gpu_registry_client_count_option,
    race_log_level_option,
    registry_client_image_option,
    node_daemon_option,
    linux_client_count_option,
    linux_client_image_option,
    linux_client_uninstalled_count_option,
    linux_client_bridge_count_option,
    linux_gpu_client_count_option,
    linux_gpu_server_count_option,
    linux_server_count_option,
    linux_server_image_option,
    linux_server_uninstalled_count_option,
    linux_server_bridge_count_option,
    network_manager_kit_option,
    no_config_gen_option,
    pass_default_artifact_revisions,
    race_core_option,
    race_node_arch_option,
    range_config_option,
    validate_image_names,
    disable_config_encryption_option,
)
from rib.commands.option_group import (
    GroupedOptionCommand,
    MutuallyExclusiveOptions,
    OptionGroup,
)
from rib.deployment.rib_aws_deployment import RibAwsDeployment
from rib.utils import click_utils, error_utils, github_utils


logger = logging.getLogger(__name__)


###
# AWS Deployment Commands
###


@click.command("active")
@click.option(
    "--aws-env-name",
    help="AWS environment on which to list the active deployments",
    required=True,
    type=str,
)
def active(aws_env_name: str) -> None:
    """
    Get active deployments on an AWS environment
    """
    click.echo(f"Getting active AWS Deployments on {aws_env_name}")

    aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)
    deployment_name = aws_env.get_active_deployment()
    if deployment_name:
        click.echo(deployment_name)
    else:
        click.echo(f"No deployment active on {aws_env_name}")


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
topology_strategy = MutuallyExclusiveOptions()
topology_file = topology_strategy.group(
    key="topology_file",
    name="Topology File Options",
    help="Use a topology file for the assignment of nodes onto the host env",
)
topology_auto = topology_strategy.group(
    key="topology_auto",
    name="Implicit Topology Options",
    help="Use an implicitly-created topology for the assigniment of nodes onto the host env",
)
images = OptionGroup("images", name="Docker Image Options")


@click.command("create", cls=GroupedOptionCommand)
@deployment_name_option("create")
@click.option(
    "--aws-env-name",
    help="AWS environment to use for the deployment",
    required=True,
    type=str,
)
@click.option("--force", "force", flag_value=True, help="Overwrite existing deployment")
# config options
@disabled_channels_option(group=config_opts)
@fetch_plugins_on_start_option(group=config_opts)
@race_log_level_option(group=config_opts)
@no_config_gen_option(group=config_opts)
# artifact options
@race_core_option(
    command_help="What RACE core is the deployment testing?",
    group=artifacts,
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
@registry_client_image_option(group=images, hidden=True)
@bastion_image_option(group=images)
# range-config options
@range_config_option(group=range_config_opts)
@disable_config_encryption_option(group=config_opts)
# node count options
@android_client_count_option(group=node_counts)
@android_client_uninstalled_count_option(group=node_counts)
@android_client_bridge_count_option(group=node_counts)
@race_node_arch_option(
    group=node_counts,
    param="--android-client-arch",
    command_help="Architecture to use for RACE Android client nodes",
)
@enable_ui_option(
    command_help="Android clients for which to enable user input UI",
    group=node_counts,
    param="--android-client-enable-ui-for",
)
@linux_client_count_option(group=node_counts)
@linux_client_uninstalled_count_option(group=node_counts)
@linux_client_bridge_count_option(group=node_counts)
@linux_gpu_client_count_option(group=node_counts)
@race_node_arch_option(
    group=node_counts,
    param="--linux-client-arch",
    command_help="Architecture to use for RACE Linux client nodes",
)
@linux_server_count_option(group=node_counts)
@linux_server_uninstalled_count_option(group=node_counts)
@linux_server_bridge_count_option(group=node_counts)
@linux_gpu_server_count_option(group=node_counts)
@race_node_arch_option(
    group=node_counts,
    param="--linux-server-arch",
    command_help="Architecture to use for RACE Linux server nodes",
)
@registry_client_count_option(group=node_counts)
@registry_client_uninstalled_count_option(group=node_counts)
@gpu_registry_client_count_option(group=node_counts)
@race_node_arch_option(
    group=node_counts,
    param="--registry-client-arch",
    command_help="Architecture to use for RACE Linux registry nodes",
)
# topology options
@topology_file.option(
    "--topology",
    "topology_file",
    type=str,
    default=None,
    required=False,
    help="Topology JSON file",
)
@topology_auto.option(
    "--colocate-clients-and-servers",
    "--colocate",
    flag_value=True,
    help="Co-locate clients and servers on the same instances",
)
@node_def_strategy.result("", default="node_counts", expose_value=False)
@topology_strategy.result("", default="topology_auto", expose_value=False)
@click.pass_context
@pass_default_artifact_revisions
@validate_image_names
def create(
    cli_context: click.core.Context,
    deployment_name: str,
    **kwargs,
) -> None:
    """Create A New AWS Deployment"""
    click.echo(f"Creating AWS Deployment: {deployment_name}")
    try:
        RibAwsDeployment.create(
            create_command=click_utils.get_run_command(cli_context),
            name=deployment_name,
            **kwargs,
        )
        click.echo(f"Created AWS Deployment: {deployment_name}")
        click.echo(
            f"Run `rib-use aws {deployment_name}` to enable shortcut commands for this deployment"
        )
    except Exception as err:
        RibAwsDeployment.remove_legacy_deployment(deployment_name)
        if isinstance(err, error_utils.RIB000):
            raise err from None
        # If this is *not* a RiB generated exception then just raise it, don't
        # wrap/swallow it.
        raise


@click.command("up")
@deployment_name_option("stand up")
@dry_run_option()
@click.option(
    "--force", flag_value=True, help="Forces up. Bypasses container/node status checks."
)
@timeout_option(default=3_600)
@click.option(
    "--no-publish",
    flag_value=True,
    help="If set, configs will not be published after upping",
)
@ansible_verbosity_option()
@click.pass_context
def up(
    cli_context: click.core.Context,
    deployment_name: str,
    dry_run: bool,
    force: bool,
    timeout: int,
    no_publish: bool,
    ansible_verbosity: int,
) -> None:
    """
    Stage configs, run containers, and start daemon on all nodes in the deployment
    """

    click.echo(f"Standing Up AWS Deployment: {deployment_name}")
    deployment = RibAwsDeployment.get_existing_deployment_or_fail(
        deployment_name, RibAwsDeployment.rib_mode
    )

    github_config = github_utils.read_github_config()

    deployment.up(
        last_up_command=click_utils.get_run_command(cli_context),
        dry_run=dry_run,
        docker_token=github_config.access_token,
        docker_user=github_config.username,
        force=force,
        timeout=timeout,
        verbosity=ansible_verbosity,
        no_publish=no_publish,
    )
    click.echo(f"Stood Up AWS Deployment: {deployment_name}")


@click.command("down")
@deployment_name_option("tear down")
@click.option(
    "--purge",
    flag_value=True,
    help="Purge all data, images, etc from the host environment?",
)
@dry_run_option()
@click.option(
    "--force", flag_value=True, help="Force the tearing down of the deployment?"
)
@timeout_option(default=600)
@ansible_verbosity_option()
@click.pass_context
def down(
    cli_context: click.core.Context,
    deployment_name: str,
    dry_run: bool,
    force: bool,
    purge: bool,
    timeout: int,
    ansible_verbosity: int,
) -> None:
    """
    Clear staged configs, stop all running containers
    """

    click.echo(f"Tearing Down AWS Deployment: {deployment_name}")
    deployment = RibAwsDeployment.get_existing_deployment_or_fail(
        deployment_name, RibAwsDeployment.rib_mode
    )
    deployment.down(
        last_down_command=click_utils.get_run_command(cli_context),
        dry_run=dry_run,
        force=force,
        purge=purge,
        timeout=timeout,
        verbosity=ansible_verbosity,
    )
    click.echo(f"Tore Down AWS Deployment: {deployment_name}")

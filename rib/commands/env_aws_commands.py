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
        AWS Environment Command Group is responsible for configuring, provisioning,
        and tearing down of AWS environments for RiB.
"""

# Python Library Imports
import click
import logging
import os
from typing import Optional

# Local Python Library Imports
from rib.aws_env.rib_aws_env import RibAwsEnv
from rib.commands.aws_env_options import (
    aws_env_name_option,
    instance_count_options,
    instance_ebs_size_options,
    instance_type_options,
    pass_instance_counts,
    pass_instance_ebs_sizes,
    pass_instance_type_names,
)
from rib.commands.common_options import (
    ansible_verbosity_option,
    detail_level_option,
    dry_run_option,
    timeout_option,
)
from rib.commands.option_group import GroupedOptionCommand, MutuallyExclusiveOptions
from rib.utils import (
    aws_topology_utils,
    click_utils,
    error_utils,
    general_utils,
)
from rib.utils.status_utils import print_status_report


logger = logging.getLogger(__name__)


###
# AWS Environment Commands
###


@click.command("active")
def active() -> None:
    """Get Active AWS Environments Across the AWS Account"""
    click.echo("Getting Active AWS Environments")

    envs = RibAwsEnv.get_active_aws_envs()

    if not envs.owned and not envs.unowned:
        click.echo("No Active AWS Environments Found")

    if envs.owned:
        click.echo(
            "My Active AWS Environments (launched by the current user/RiB instance):"
        )
        for env_name in sorted(envs.owned):
            click.echo(f"\t{env_name}")

    if envs.unowned:
        click.echo(
            "Other Active AWS Environments (launched by another user/RiB instance):"
        )
        for env_name in sorted(envs.unowned):
            click.echo(f"\t{env_name}")


@click.command("copy")
@click.option(
    "--from",
    "from_aws_env_name",
    help="Name of the existing AWS Environment to be copied",
    required=True,
    type=str,
)
@click.option(
    "--to",
    "to_aws_env_name",
    help="New AWS Environment name",
    required=True,
    type=str,
)
@click.option("--force", flag_value=True, help="Force copy of AWS environment")
def copy(from_aws_env_name: str, to_aws_env_name: str, force: bool) -> None:
    """Copy An AWS Environment"""
    click.echo(f"Copying AWS Environment from {from_aws_env_name} to {to_aws_env_name}")

    if RibAwsEnv.aws_env_exists(to_aws_env_name):
        raise error_utils.RIB707(to_aws_env_name)

    from_aws_env = RibAwsEnv.get_aws_env_or_fail(from_aws_env_name)
    from_aws_env.copy(name=to_aws_env_name, force=force)

    click.echo(f"Copied AWS Environment from {from_aws_env_name} to {to_aws_env_name}")


instance_count_strategy = MutuallyExclusiveOptions()
explicit_instance_counts = instance_count_strategy.group(
    key="instance_counts",
    name="Instance Count Options",
    help="Explicitly define EC2 instance counts",
)
topology_instance_counts = instance_count_strategy.group(
    key="topology",
    name="Topology Options",
    help="Derive EC2 instance counts from node instance topology",
)


@click.command("create", cls=GroupedOptionCommand)
@aws_env_name_option("create", validate=True)
@click.option(
    "--ssh-key-name",
    help="Name of the SSH keypair in AWS to link to EC2 instances",
    required=True,
    type=str,
)
@click.option(
    "--remote-username",
    default="rib",
    help="Account to create on EC2 instances",
    type=str,
)
@click.option(
    "--region",
    default="us-east-1",
    help="AWS region in which to create the AWS environment",
    show_default=True,
    type=str,
)
@click.option("--force", flag_value=True, help="Overwrite existing AWS environment")
@click.option(
    "--yes", "-y", flag_value=True, help="Accept AWS environment creation prompt"
)
@instance_count_options(explicit_instance_counts)
@topology_instance_counts.option(
    "--topology",
    "topology_file",
    type=str,
    default=None,
    required=False,
    help="Topology JSON file",
)
@instance_type_options(services=True)
@instance_ebs_size_options()
@instance_count_strategy.result("", default="instance_counts", expose_value=False)
@pass_instance_counts
@pass_instance_ebs_sizes
@pass_instance_type_names
@click.pass_context
def create(
    cli_context: click.core.Context,
    aws_env_name: str,
    ssh_key_name: str,
    remote_username: str,
    region: str,
    topology_file: Optional[str],
    instance_counts: aws_topology_utils.InstanceCounts,
    instance_type_names: aws_topology_utils.InstanceTypeNames,
    instance_ebs_sizes: aws_topology_utils.InstanceEbsSizes,
    force: bool,
    yes: bool,
) -> None:
    """Create A New AWS Environment"""
    click.echo(f"Creating AWS Environment: {aws_env_name}")

    if topology_file:
        topology = aws_topology_utils.read_topology_from_file(topology_file)
        instance_counts = aws_topology_utils.instance_counts_from_topology(topology)

    if instance_counts.total == 0:
        raise error_utils.RIB720(
            "No RACE node host instances requested",
            "Retry create with non-zero instance counts",
        )

    click.echo("AWS Environment will be created with:")
    for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
        if instance_counts.get(platform, gpu, arch):
            click.echo(
                f"\t{instance_counts.get(platform, gpu, arch)} "
                f"{instance_type_names.get(platform, gpu, arch)} EC2 instances for RACE nodes"
            )
    click.echo(
        f"\t1 {instance_type_names.cluster_manager_instance_type_name} "
        "EC2 instance as the cluster manager"
    )
    click.echo(
        f"\t1 {instance_type_names.service_host_instance_type_name} "
        "EC2 instance as the external service host"
    )
    if not yes:
        click.confirm("Do you want to proceed?", abort=True)

    # Make sure env doesn't already exist (or remove it if force)
    if RibAwsEnv.aws_env_exists(aws_env_name):
        if not force:
            raise error_utils.RIB707(aws_env_name)

        click.echo("Removing existing AWS Environment")

        # Try to load it
        aws_env = RibAwsEnv.load_aws_env(aws_env_name)
        if aws_env:
            aws_env.remove()
        else:
            # Else it's a legacy env, remove by brute force
            if click.confirm(
                "This AWS Environment was created with an older version of RiB. Are you sure you want to forcibly remove it?"
            ):
                RibAwsEnv.remove_legacy_aws_env(aws_env_name)
            else:
                raise click.Abort()

    RibAwsEnv.create(
        aws_env_name=aws_env_name,
        create_command=click_utils.get_run_command(cli_context),
        instance_counts=instance_counts,
        instance_ebs_sizes=instance_ebs_sizes,
        instance_type_names=instance_type_names,
        region=region,
        remote_username=remote_username,
        ssh_key_name=ssh_key_name,
    )

    click.echo(f"Created AWS Environment: {aws_env_name}")


@click.command("info")
@aws_env_name_option("report configuration info")
@click.option(
    "--format",
    default="yaml",
    help="Format output as JSON or YAML",
    show_default=True,
    type=click.Choice(["json", "yaml"]),
)
def info(aws_env_name: str, format: str) -> None:
    """Report Configuration & Metadata Info About An AWS Environment"""

    aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)
    info = {
        "config": aws_env.config.dict(),
        "metadata": aws_env.metadata,
    }

    if format == "json":
        click.echo(general_utils.pretty_print_json(info))
    else:
        click.echo(general_utils.pretty_print_yaml(info))


@click.command("list")
def list_envs() -> None:
    """List all AWS environments created on the local machine"""

    envs = RibAwsEnv.get_local_aws_envs()

    if not envs.compatible and not envs.incompatible:
        click.echo("No AWS Environments Found")

    if envs.compatible:
        click.echo("Compatible AWS Environments:")
        for env_name in sorted(envs.compatible):
            click.echo(f"\t{env_name}")

    if envs.incompatible:
        click.echo("Incompatible AWS Environments (from previous RiB versions):")
        for env in sorted(envs.incompatible):
            click.echo(f"\t{env.name} (RiB {env.rib_version})")


@click.command("provision")
@aws_env_name_option("provision")
@timeout_option(default=3_600)
@click.option("--force", flag_value=True, help="Force re-provision of AWS environment")
@dry_run_option()
@ansible_verbosity_option()
@click.pass_context
def provision(
    cli_context: click.core.Context,
    aws_env_name: str,
    timeout: int,
    force: bool,
    dry_run: bool,
    ansible_verbosity: int,
) -> None:
    """Provision An AWS Environment"""
    click.echo(f"Provisioning AWS Environment: {aws_env_name}")

    aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)
    aws_env.provision(
        current_username=os.environ.get("HOST_USER", "rib"),
        dry_run=dry_run,
        force=force,
        provision_command=click_utils.get_run_command(cli_context),
        timeout=timeout,
        verbosity=ansible_verbosity,
    )

    click.echo(f"Provisioned AWS Environment: {aws_env_name}")


@click.command("remove")
@aws_env_name_option("remove")
def remove(aws_env_name: str) -> None:
    """Remove An AWS Environment"""
    click.echo(f"Removing AWS Environment: {aws_env_name}")

    if RibAwsEnv.aws_env_exists(aws_env_name):
        # Try to load it
        aws_env = RibAwsEnv.load_aws_env(aws_env_name)
        if aws_env:
            aws_env.remove()
        else:
            # Else it's a legacy env, remove by brute force
            if click.confirm(
                "This AWS Environment was created with an older version of RiB. Are you sure you want to forcibly remove it?"
            ):
                RibAwsEnv.remove_legacy_aws_env(aws_env_name)
            else:
                click.echo("Aborting")
                return
    else:
        click.secho(f"No AWS Environment exists: {aws_env_name}", fg="yellow")

    click.echo(f"Removed AWS Environment: {aws_env_name}")


@click.command("rename")
@click.option(
    "--from",
    "from_aws_env_name",
    help="Name of the existing AWS Environment to be renamed",
    required=True,
    type=str,
)
@click.option(
    "--to",
    "to_aws_env_name",
    help="New AWS Environment name",
    required=True,
    type=str,
)
def rename(from_aws_env_name: str, to_aws_env_name: str) -> None:
    """Rename An AWS Environment"""
    click.echo(
        f"Renaming AWS Environment from {from_aws_env_name} to {to_aws_env_name}"
    )

    if RibAwsEnv.aws_env_exists(to_aws_env_name):
        raise error_utils.RIB707(to_aws_env_name)

    old_aws_env = RibAwsEnv.get_aws_env_or_fail(from_aws_env_name)
    old_aws_env.rename(to_aws_env_name)

    click.echo(f"Renamed AWS Environment from {from_aws_env_name} to {to_aws_env_name}")


@click.command("runtime-info")
@aws_env_name_option("report runtime info")
@click.option(
    "--format",
    default="yaml",
    help="Format output as JSON or YAML",
    show_default=True,
    type=click.Choice(["json", "yaml"]),
)
def runtime_info(aws_env_name: str, format: str) -> None:
    """Report Runtime Info About An AWS Environment"""

    aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)
    info = aws_env.get_runtime_info()

    if format == "json":
        click.echo(general_utils.pretty_print_json(info))
    else:
        click.echo(general_utils.pretty_print_yaml(info))


@click.command("status")
@aws_env_name_option("report status")
@detail_level_option()
@click.option(
    "--format",
    default=None,
    help="Format output as raw JSON or YAML",
    type=click.Choice(["json", "yaml"]),
)
def status(aws_env_name: str, detail_level: int, format: str) -> None:
    """Report Status Of An AWS Environment"""

    aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)
    status = aws_env.get_status_report()

    if format:
        if format == "json":
            click.echo(general_utils.pretty_print_json(status.components))
        else:
            click.echo(general_utils.pretty_print_yaml(status.components))
    else:
        click.echo(f"AWS Environment {aws_env_name} is {repr(status.status)}")
        if detail_level > 0:
            print_status_report(
                detail_level=detail_level - 1,
                details=status.components,
                printer=click.echo,
            )


@click.command("unprovision")
@aws_env_name_option("unprovision")
@timeout_option(
    command_help="Timeout for unprovisioning (in seconds per CloudFormation stack)",
    default=600,
)
@click.option("--force", flag_value=True, help="Force un-provision of AWS environment")
@dry_run_option()
@ansible_verbosity_option()
@click.pass_context
def unprovision(
    cli_context: click.core.Context,
    aws_env_name: str,
    timeout: int,
    force: bool,
    dry_run: bool,
    ansible_verbosity: int,
) -> None:
    """Unprovision An AWS Environment"""
    click.echo(f"Unprovisioning AWS Environment: {aws_env_name}")

    aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)
    aws_env.unprovision(
        dry_run=dry_run,
        force=force,
        timeout=timeout,
        unprovision_command=click_utils.get_run_command(cli_context),
        verbosity=ansible_verbosity,
    )

    click.echo(f"Unprovisioned AWS Environment: {aws_env_name}")

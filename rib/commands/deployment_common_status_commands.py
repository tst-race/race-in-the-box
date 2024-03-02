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
    Common deployment status commands
"""

# Python Library Imports
import click
from click_default_group import DefaultGroup
from typing import Iterable, List, Optional

# Local Python Library Imports
from rib.commands.common_options import detail_level_option, format_option
from rib.commands.deployment_options import (
    deployment_name_option,
    nodes_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import general_utils, status_utils
from rib.utils.status_utils import StatusReport, print_count_report, print_status_report


###
# Generic Deployment Status Commands
###


@click.group("status", cls=DefaultGroup, default="all", default_if_no_args=True)
def status_command_group() -> None:
    """Report Status Of A Deployment"""


@status_command_group.command("all")
@deployment_name_option("report deployment status")
@detail_level_option()
@format_option()
@pass_rib_mode
@click.pass_context
def status_all(
    cli_context: click.core.Context,
    rib_mode: str,
    deployment_name: str,
    detail_level: int,
    format: Optional[str],
) -> None:
    """Report Status Of Deployment Apps, Containers, and Services"""

    if not cli_context.invoked_subcommand:
        # Get all status reports first, then print them out so the output is cleaner (some of the
        # get_*_status_report methods have logging output)
        deployment = RibDeployment.get_existing_deployment_or_fail(
            deployment_name, rib_mode
        )
        deployment.status.verify_deployment_is_active("report status for", none_ok=True)
        app_status_report = deployment.status.get_app_status_report()
        container_status_report = deployment.status.get_container_status_report()
        service_status_report = deployment.status.get_services_status_report()

        _print_report(
            description=f"Deployment {deployment_name} apps",
            detail_level=detail_level,
            format=format,
            status_report=app_status_report,
            status_type=status_utils.NodeStatus,
        )
        _print_report(
            description=f"Deployment {deployment_name} containers",
            detail_level=detail_level,
            format=format,
            status_report=container_status_report,
            status_type=status_utils.ContainerStatus,
        )
        _print_report(
            description=f"Deployment {deployment_name} services",
            detail_level=detail_level,
            format=format,
            status_report=service_status_report,
            status_type=status_utils.ServiceStatus,
        )


@status_command_group.command("app")
@deployment_name_option("report app status")
@detail_level_option()
@format_option()
@nodes_option("app status")
@pass_rib_mode
def status_app(
    rib_mode: str,
    deployment_name: str,
    detail_level: int,
    nodes: Optional[List[str]],
    format: Optional[str],
) -> None:
    """Report Status Of RACE Apps In A Deployment"""

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.status.verify_deployment_is_active("report status for", none_ok=True)
    _print_report(
        description=f"Deployment {deployment_name} apps",
        detail_level=detail_level,
        format=format,
        status_report=deployment.status.get_app_status_report(nodes=nodes),
        status_type=status_utils.NodeStatus,
    )


@status_command_group.command("containers")
@deployment_name_option("report container status")
@detail_level_option()
@format_option()
@pass_rib_mode
def status_containers(
    rib_mode: str,
    deployment_name: str,
    detail_level: int,
    format: Optional[str],
) -> None:
    """Report Status Of Deployment RACE Containers"""

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    deployment.status.verify_deployment_is_active("report status for", none_ok=True)
    _print_report(
        description=f"Deployment {deployment_name} containers",
        detail_level=detail_level,
        format=format,
        status_report=deployment.status.get_container_status_report(),
        status_type=status_utils.ContainerStatus,
    )


@status_command_group.command("services")
@deployment_name_option("report services status")
@detail_level_option()
@format_option()
@pass_rib_mode
def status_services(
    rib_mode: str,
    deployment_name: str,
    detail_level: int,
    format: Optional[str],
) -> None:
    """Report Status Of Deployment Services"""

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )
    deployment.status.verify_deployment_is_active("report status for", none_ok=True)
    _print_report(
        description=f"Deployment {deployment_name} services",
        detail_level=detail_level,
        format=format,
        status_report=deployment.status.get_services_status_report(),
        status_type=status_utils.ServiceStatus,
    )


def _print_report(
    description: str,
    detail_level: int,
    format: Optional[str],
    status_report: StatusReport,
    status_type: Iterable[str],
) -> None:
    """
    Purpose:
        Prints the status report to standard output
    Args:
        description: Description of the status report
        detail_level: Level of detail
        format: If specified, print report as raw JSON/YAML
        status_report: Status report to be printed
        status_type: Status types for the first level of children in the report (may be an enum)
    Return:
        N/A
    """
    if format:
        if format == "json":
            click.echo(general_utils.pretty_print_json(status_report))
        else:
            click.echo(general_utils.pretty_print_yaml(status_report))
    else:
        click.echo(f"{description}: {repr(status_report['status'])}")
        if detail_level > 0:
            click.echo("Counts:")
            print_count_report(
                detail_level=detail_level - 1,
                details=status_report.get("children", {}),
                printer=click.echo,
                status_type=status_type,
            )
        if detail_level > 1:
            click.echo("Details:")
            print_status_report(
                detail_level=detail_level - 2,
                details=status_report.get("children", {}),
                printer=click.echo,
            )

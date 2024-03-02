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
    AWS Topology Command Group is responsible for creating AWS topologies
"""

# Python Library Imports
import click
import logging
from typing import Callable, Optional

# Local Python Library Imports
from rib.commands.aws_env_options import (
    colocate_across_instances_option,
    colocate_clients_and_servers_option,
    instance_count_options,
    instance_type_options,
    node_count_options,
    node_resource_constraint_options,
    nodes_per_instance_options,
    pass_instance_counts,
    pass_instance_type_names,
    pass_node_counts,
    pass_node_resource_constraints,
    pass_nodes_per_instance,
)
from rib.commands.common_options import format_option, out_option
from rib.commands.option_group import GroupedOptionCommand, MutuallyExclusiveOptions
from rib.utils import aws_topology_utils, general_utils

# Set up logger
logger = logging.getLogger(__name__)


###
# Utility functions
###


def _print_utilization(prefix: str, used: float, total: float) -> None:
    """
    Purpose:
        Prints the given resource utilization
    Args:
        prefix: Prefix (resource) to be printed before each line
        used: Amount of resource used
        total: Total amount of resource
    Returns:
        N/A
    """
    percent = (used / total) * 100
    click.echo(f"{prefix}: {used:.1f}/{total:.1f} ({percent:.1f}%)")


def _print_capacity(
    capacity: aws_topology_utils.NodeInstanceCapacity, prefix: str = ""
) -> None:
    """
    Purpose:
        Prints the given instance capacity to standard out
    Args:
        capacity: Node instance capacity
        prefix: Prefix (indentation) to be printed before each line
    Returns:
        N/A
    """

    click.echo(f"{prefix}Android Clients: {capacity.android_client_count}")
    click.echo(f"{prefix}Linux GPU-enabled Clients: {capacity.linux_gpu_client_count}")
    click.echo(f"{prefix}Linux GPU-enabled Servers: {capacity.linux_gpu_server_count}")
    click.echo(f"{prefix}Linux Clients: {capacity.linux_client_count}")
    click.echo(f"{prefix}Linux Servers: {capacity.linux_server_count}")


def _print_topology(
    topology: aws_topology_utils.NodeInstanceTopology, format: Optional[str]
) -> None:
    """
    Purpose:
        Prints the given topology to standard out
    Args:
        topology: Node instance topology
        format: Optional format to print ("yaml" or "json")
    Returns:
        N/A
    """

    if format:
        if format == "json":
            click.echo(general_utils.pretty_print_json(topology.dict()))
        else:
            click.echo(general_utils.pretty_print_yaml(topology.dict()))
    else:
        click.echo("AWS Node Instance Topology:")
        count = 1
        for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
            click.echo(f"\t{platform}{' GPU-enabled' if gpu else ''} {arch} instances:")
            for capacity in topology.get(platform, gpu, arch):
                click.echo(f"\t\tInstance #{count}:")
                _print_capacity(capacity, "\t\t\t")
                count += 1


def _print_host_topology(
    topology: aws_topology_utils.HostInstanceTopology, format: Optional[str]
) -> None:
    """
    Purpose:
        Prints the given host topology to standard out
    Args:
        topology: Host instance topology
        format: Optional format to print ("yaml" or "json")
    Returns:
        N/A
    """

    if format:
        _print_topology(topology.instance_topology, format)
    else:
        click.echo("AWS Node Instance Topology:")
        count = 1
        for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
            click.echo(f"\t{platform}{' GPU-enabled' if gpu else ''} {arch} instances:")
            for instance in topology.get(platform, gpu, arch):
                click.echo(f"\t\tInstance #{count}:")
                click.echo(f"\t\t\tEC2 instance type: {instance.details.name}")
                _print_capacity(instance.capacity, "\t\t\t")
                _print_utilization(
                    "\t\t\tRAM utilization",
                    instance.guaranteed_ram + instance.overcommitted_ram,
                    instance.details.ram_mb,
                )
                _print_utilization(
                    "\t\t\tCPU utilization",
                    instance.guaranteed_cpus + instance.overcommitted_cpus,
                    instance.details.cpus,
                )
                if instance.details.gpus:
                    _print_utilization(
                        "\t\t\tGPU utilization",
                        instance.guaranteed_gpus + instance.overcommitted_gpus,
                        instance.details.gpus,
                    )
                count += 1


###
# AWS Topology Commands
###


@click.group("topology")
def topology_command_group() -> None:
    """Commands for creating AWS topologies"""


@topology_command_group.command("by-instance-count", cls=GroupedOptionCommand)
@colocate_clients_and_servers_option()
@format_option()
@out_option()
@node_count_options()
@instance_count_options()
@pass_instance_counts
@pass_node_counts
def create_by_instance_count(
    colocate_clients_and_servers: bool,
    instance_counts: aws_topology_utils.InstanceCounts,
    node_counts: aws_topology_utils.NodeCounts,
    format: Optional[str],
    out: Optional[str],
):
    """Create AWS topology using fixed instance counts"""

    topology = aws_topology_utils.create_topology_from_instance_counts(
        instance_counts=instance_counts,
        colocate_clients_and_servers=colocate_clients_and_servers,
        node_counts=node_counts,
    )

    if out:
        aws_topology_utils.write_topology_to_file(topology, out)
        click.echo(f"Topology written to {out}")
    else:
        _print_topology(topology, format)


nodes_per_instance_strategy = MutuallyExclusiveOptions()
nodes_per_instance_node_counts = nodes_per_instance_strategy.group(
    key="node_counts",
    name="Node Count Options",
    help="Use fixed node counts to determine instance counts",
)
nodes_per_instance_instance_counts = nodes_per_instance_strategy.group(
    key="instance_counts",
    name="Instance Count Options",
    help="Use fixed instance counts to determine node counts",
)


@topology_command_group.command("by-nodes-per-instance", cls=GroupedOptionCommand)
@colocate_clients_and_servers_option()
@format_option()
@out_option()
@nodes_per_instance_options()
@node_count_options(nodes_per_instance_node_counts)
@instance_count_options(nodes_per_instance_instance_counts)
@nodes_per_instance_strategy.result("strategy", default="node_counts")
@pass_instance_counts
@pass_node_counts
@pass_nodes_per_instance
def create_by_nodes_per_instance(
    colocate_clients_and_servers: bool,
    nodes_per_instance: aws_topology_utils.NodeCounts,
    strategy: str,
    instance_counts: aws_topology_utils.InstanceCounts,
    node_counts: aws_topology_utils.NodeCounts,
    format: Optional[str],
    out: Optional[str],
):
    """Create AWS topology using nodes-per-instance constraints"""

    topology = aws_topology_utils.create_topology_from_nodes_per_instance(
        colocate_clients_and_servers=colocate_clients_and_servers,
        nodes_per_instance=nodes_per_instance,
        instance_counts=instance_counts if strategy == "instance_counts" else None,
        node_counts=node_counts if strategy == "node_counts" else None,
    )

    if out:
        aws_topology_utils.write_topology_to_file(topology, out)
        click.echo(f"Topology written to {out}")
    else:
        _print_topology(topology, format)


@topology_command_group.command(
    "by-node-resource-requirements", cls=GroupedOptionCommand
)
@colocate_across_instances_option()
@format_option()
@out_option()
@node_resource_constraint_options()
@node_count_options()
@instance_type_options()
@pass_instance_type_names
@pass_node_counts
@pass_node_resource_constraints
def create_by_node_resource_requirements(
    colocate_across_instances: bool,
    instance_type_names: aws_topology_utils.InstanceTypeNames,
    node_counts: aws_topology_utils.NodeCounts,
    node_resource_constraints: aws_topology_utils.NodeResourceConstraints,
    format: Optional[str],
    out: Optional[str],
):
    """Create AWS topology using node resource requirement constraints"""

    topology = aws_topology_utils.create_topology_from_node_resource_requirements(
        allow_colocation=colocate_across_instances,
        instance_type_names=instance_type_names,
        node_counts=node_counts,
        node_resource_constraints=node_resource_constraints,
    )

    if out:
        aws_topology_utils.write_topology_to_file(topology.instance_topology, out)
        click.echo(f"Topology written to {out}")
    else:
        _print_host_topology(topology, format)

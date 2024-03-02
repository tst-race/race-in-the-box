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
    Custom decorators to standardize click options for AWS env commands
"""

# Python Library Imports
import click
import functools
import re
from typing import Any, Callable, Optional

# Local Python Library Imports
from rib.commands.option_group import OptionGroup
from rib.utils import aws_topology_utils


###
# Command decorators
###


def pass_instance_counts(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to create instance counts command argument from instance
        count options
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance_counts = aws_topology_utils.InstanceCounts()
        for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
            instance_counts.set(
                platform,
                gpu,
                arch,
                kwargs.pop(f"{platform}{'_gpu' if gpu else ''}_{arch}_instance_count"),
            )
        kwargs["instance_counts"] = instance_counts

        return func(*args, **kwargs)

    return wrapper


def pass_instance_ebs_sizes(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to create instance EBS sizes command argument from instance EBS
        size options
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance_ebs_sizes = aws_topology_utils.InstanceEbsSizes(
            android_instance_ebs_size_gb=kwargs.pop("android_instance_ebs_size"),
            linux_gpu_instance_ebs_size_gb=kwargs.pop("linux_gpu_instance_ebs_size"),
            linux_instance_ebs_size_gb=kwargs.pop("linux_instance_ebs_size"),
            cluster_manager_instance_ebs_size_gb=kwargs.pop(
                "cluster_manager_instance_ebs_size"
            ),
            service_host_instance_ebs_size_gb=kwargs.pop(
                "service_host_instance_ebs_size"
            ),
        )
        kwargs["instance_ebs_sizes"] = instance_ebs_sizes

        return func(*args, **kwargs)

    return wrapper


def pass_instance_type_names(func: Callable) -> Callable:
    """
    Purpose:
        custom command decorator to create instance type names command argument from instance type
        options
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance_types = aws_topology_utils.InstanceTypeNames()
        for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
            instance_types.set(
                platform,
                gpu,
                arch,
                kwargs.pop(f"{platform}{'_gpu' if gpu else ''}_{arch}_instance_type"),
            )
        # These instance types are optional (not used as part of topology creation)
        instance_types.cluster_manager_instance_type_name = kwargs.pop(
            "cluster_manager_instance_type", None
        )
        instance_types.service_host_instance_type_name = kwargs.pop(
            "service_host_instance_type", None
        )

        kwargs["instance_type_names"] = instance_types

        return func(*args, **kwargs)

    return wrapper


def pass_node_counts(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to create node counts command argument from node count options
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        node_counts = aws_topology_utils.NodeCounts()
        for platform, gpu, arch, node_type in aws_topology_utils.NODE_COMBOS:
            node_counts.set(
                platform,
                gpu,
                arch,
                node_type,
                kwargs.pop(
                    f"{platform}{'_gpu' if gpu else ''}_{arch}_{node_type}_count"
                ),
            )
        kwargs["node_counts"] = node_counts

        return func(*args, **kwargs)

    return wrapper


def pass_nodes_per_instance(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to create nodes-per-instance command argument from
        nodes-per-instance options
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        node_counts = aws_topology_utils.NodeCounts()
        for platform, gpu, arch, node_type in aws_topology_utils.NODE_COMBOS:
            node_counts.set(
                platform,
                gpu,
                arch,
                node_type,
                kwargs.pop(
                    f"{platform}{'_gpu' if gpu else ''}_{arch}_{node_type}s_per_instance"
                ),
            )
        kwargs["nodes_per_instance"] = node_counts

        return func(*args, **kwargs)

    return wrapper


def pass_node_resource_constraints(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to create node resource constraints command argument from node
        resource constraint options
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        constraints = aws_topology_utils.NodeResourceConstraints(
            ram_per_android_client=kwargs.pop("ram_per_android_client"),
            ram_per_linux_client=kwargs.pop("ram_per_linux_client"),
            ram_per_linux_server=kwargs.pop("ram_per_linux_server"),
            ram_overcommit=kwargs.pop("ram_overcommit"),
            cpus_per_android_client=kwargs.pop("cpus_per_android_client"),
            cpus_per_linux_client=kwargs.pop("cpus_per_linux_client"),
            cpus_per_linux_server=kwargs.pop("cpus_per_linux_server"),
            cpu_overcommit=kwargs.pop("cpu_overcommit"),
            gpus_per_linux_client=kwargs.pop("gpus_per_linux_client"),
            gpus_per_linux_server=kwargs.pop("gpus_per_linux_server"),
            gpu_overcommit=kwargs.pop("gpu_overcommit"),
        )
        kwargs["node_resource_constraints"] = constraints

        return func(*args, **kwargs)

    return wrapper


###
# Option decorators
###


def _validate_aws_env_name(
    context: click.Context, param: click.Parameter, value: Any
) -> str:
    """Ensure that AWS env name contains only allowed characters"""
    if re.fullmatch(r"[a-zA-Z][-a-zA-Z0-9]*", value) is not None:
        return value
    raise click.BadParameter("Only alphanumeric and `-` characters are allowed")


def aws_env_name_option(action: str, validate: bool = False):
    """
    Purpose:
        Custom option decorator for the AWS environment name option.
    Args:
        action: AWS environment action
        validate: Whether to validate the name value
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @aws_env_name_option("provision")
        def foo(aws_env_name: str):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--name",
            "aws_env_name",
            callback=_validate_aws_env_name if validate else None,
            envvar="ENV_NAME",
            help=f"What AWS environment to {action}?",
            required=True,
            type=str,
        )(function)

    return wrapper


def colocate_across_instances_option():
    """
    Purpose:
        Custom option decorator for the colocate-across-instances option.
    Args:
        N/A
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @colocate_across_instances_option()
        def foo(colocate_across_instances: bool):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--colocate-across-instances",
            "--colocate",
            flag_value=True,
            help="Co-locate RACE nodes across instances as applicable",
        )(function)

    return wrapper


def colocate_clients_and_servers_option():
    """
    Purpose:
        Custom option decorator for the colocate-clients-and-servers option.
    Args:
        N/A
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @colocate_clients_and_servers_option()
        def foo(colocate_clients_and_servers: bool):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--colocate-clients-and-servers",
            "--colocate",
            flag_value=True,
            help="Co-locate clients and servers on the same instances",
        )(function)

    return wrapper


def _validate_instance_type(
    ctx: click.Context, param: click.Parameter, value: str
) -> Any:
    """Ensure that instance type is a valid instance identifier"""
    parts = value.split(".")
    if len(parts) != 2:
        raise click.BadParameter("format must be '<type>.<size>' (e.g., t3.large)")
    return value


def instance_count_options(group: Optional[OptionGroup] = None) -> Callable:
    """
    Purpose:
        Custom option decorator for the instance count options.
    Args:
        group: Optional option group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @instance_count_options()
        def foo(android_arm64_instance_count, android_x86_64_instance_count, **kwargs):
            pass
        ```
    """

    if not group:
        group = OptionGroup("instance_counts", name="Instance Count Options")

    def wrapper(func):
        for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
            func = group.option(
                f"--{platform}{'-gpu' if gpu else ''}-{arch}-instance-count",
                default=0,
                help=f"How many {platform}{' GPU-enabled' if gpu else ''} {arch} RACE node instances",
                type=click.IntRange(min=0),
            )(func)
        return func

    return wrapper


def instance_ebs_size_options(group: Optional[OptionGroup] = None) -> Callable:
    """
    Purpose:
        Custom option decorator for the instance EBS size options.
    Args:
        group: Optional option group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @instance_ebs_size_options()
        def foo(android_instance_ebs_size_gb, linux_instance_ebs_size_gb, **kwargs):
            pass
        ```
    """

    if not group:
        group = OptionGroup("ebs_sizes", name="Instance EBS Sizes")

    def wrapper(func):
        # Note, these are run in "backwards" order so that the help printout uses the
        # order that we would have gotten if these were defined as usual @click.option
        # decorations.

        # gp2 EBS volumes can be sized from 1 GiB to 16 TiB
        min_size = 32
        max_size = 16 * 1024

        func = group.option(
            "--service-host-instance-ebs-size",
            default=64,
            help="AWS EBS size, in GB, for EC2 instance running external services",
            show_default=True,
            type=click.IntRange(min=min_size, max=max_size),
        )(func)
        func = group.option(
            "--cluster-manager-instance-ebs-size",
            default=64,
            help="AWS EBS size, in GB, for EC2 instance running cluster management",
            show_default=True,
            type=click.IntRange(min=min_size, max=max_size),
        )(func)
        func = group.option(
            "--android-instance-ebs-size",
            default=128,
            help="AWS EBS size, in GB, for EC2 instance running Android RACE client nodes",
            show_default=True,
            type=click.IntRange(min=min_size, max=max_size),
        )(func)
        func = group.option(
            "--linux-gpu-instance-ebs-size",
            default=128,
            help="AWS EBS size, in GB, for EC2 instance running Linux GPU-enabled RACE nodes",
            show_default=True,
            type=click.IntRange(min=min_size, max=max_size),
        )(func)
        func = group.option(
            "--linux-instance-ebs-size",
            default=64,
            help="AWS EBS size, in GB, for EC2 instance running Linux RACE nodes",
            show_default=True,
            type=click.IntRange(min=min_size, max=max_size),
        )(func)

        return func

    return wrapper


def instance_type_options(
    group: Optional[OptionGroup] = None, services: bool = False
) -> Callable:
    """
    Purpose:
        Custom option decorator for the instance type options.
    Args:
        group: Optional option group
        services: Whether to include service/cluster manager host instance type options
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @instance_type_options
        def foo(android_arm64_instance_type_name, android_x86_64_instance_type_name, **kwargs):
            pass
        ```
    """

    if not group:
        group = OptionGroup(
            "instance_types",
            name="Instance Type Options",
            help="See https://aws.amazon.com/ec2/instance-types/",
        )

    def wrapper(func):
        if services:
            func = group.option(
                "--service-host-instance-type",
                callback=_validate_instance_type,
                default="t3a.2xlarge",
                help="AWS EC2 instance type for running external services",
                show_default=True,
                type=str,
            )(func)
            func = group.option(
                "--cluster-manager-instance-type",
                callback=_validate_instance_type,
                default="t3a.2xlarge",
                help="AWS EC2 instance type for running cluster management",
                show_default=True,
                type=str,
            )(func)
        func = group.option(
            "--android-arm64-instance-type",
            callback=_validate_instance_type,
            default="a1.metal",
            help="AWS EC2 instance type for running Android ARM64 RACE nodes",
            show_default=True,
            type=str,
        )(func)
        func = group.option(
            "--android-x86_64-instance-type",
            callback=_validate_instance_type,
            default="c5.metal",
            help="AWS EC2 instance type for running Android x86_64 RACE nodes",
            show_default=True,
            type=str,
        )(func)
        func = group.option(
            "--linux-gpu-arm64-instance-type",
            callback=_validate_instance_type,
            default="g5g.2xlarge",
            help="AWS EC2 instance type for running Linux ARM64 GPU-enabled RACE nodes",
            show_default=True,
            type=str,
        )(func)
        func = group.option(
            "--linux-gpu-x86_64-instance-type",
            callback=_validate_instance_type,
            default="p3.2xlarge",
            help="AWS EC2 instance type for running Linux x86_64 GPU-enabled RACE nodes",
            show_default=True,
            type=str,
        )(func)
        func = group.option(
            "--linux-arm64-instance-type",
            callback=_validate_instance_type,
            default="t4g.xlarge",
            help="AWS EC2 instance type for running Linux ARM64 RACE nodes",
            show_default=True,
            type=str,
        )(func)
        func = group.option(
            "--linux-x86_64-instance-type",
            callback=_validate_instance_type,
            default="t3a.2xlarge",
            help="AWS EC2 instance type for running Linux x86_64 RACE nodes",
            show_default=True,
            type=str,
        )(func)

        return func

    return wrapper


def node_count_options(group: Optional[OptionGroup] = None) -> Callable:
    """
    Purpose:
        Custom option decorator for the node count options.
    Args:
        group: Optional option group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @node_count_options()
        def foo(android_arm64_client_count, android_x86_64_client_count, **kwargs):
            pass
        ```
    """

    if not group:
        group = OptionGroup("node_counts", name="Node Count Options")

    def wrapper(func):
        for platform, gpu, arch, node_type in aws_topology_utils.NODE_COMBOS:
            func = group.option(
                f"--{platform}{'-gpu' if gpu else ''}-{arch}-{node_type}-count",
                default=0,
                help=f"How many {platform}{' GPU-enabled' if gpu else ''} {arch} {node_type}s",
                type=click.IntRange(min=0),
            )(func)
        return func

    return wrapper


def nodes_per_instance_options(group: Optional[OptionGroup] = None) -> Callable:
    """
    Purpose:
        Custom option decorator for the nodes-per-instance options.
    Args:
        group: Optional option group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @nodes_per_instance_options()
        def foo(android_arm64_clients_per_instance, android_x86_64_clients_per_instance, **kwargs):
            pass
        ```
    """

    if not group:
        group = OptionGroup("nodes_per_instance", name="Nodes-per-Instance Options")

    def wrapper(func):
        for platform, gpu, arch, node_type in aws_topology_utils.NODE_COMBOS:
            func = group.option(
                f"--{platform}{'-gpu' if gpu else ''}-{arch}-{node_type}s-per-instance",
                default=0,
                help=f"How many {platform}{' GPU-enabled' if gpu else ''} {arch} {node_type}s per instance",
                type=click.IntRange(min=0),
            )(func)
        return func

    return wrapper


def node_resource_constraint_options(group: Optional[OptionGroup] = None) -> Callable:
    """
    Purpose:
        Custom option decorator for the node resource constraint options.
    Args:
        group: Optional option group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @node_resource_constraint_options()
        def foo(ram_per_android_client, cpus_per_android_client, **kwargs):
            foo
        ```
    """

    if not group:
        group = OptionGroup(
            "node_resource_constraints", name="Node Resource Constraint Options"
        )

    def wrapper(func):
        # The default values here for CPU and RAM per node were determined by
        # running `docker stats` on deployments with multiple perfomer comms
        # solutions and a performer Network Manager solution at scale, and leaving some
        # room for future growth.
        func = group.option(
            "--gpu-overcommit",
            default=0.0,
            help="Fraction of GPUs to overcommit (share) between nodes on an instance",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--gpus-per-linux-server",
            default=1.0,
            help="How many GPUs (fractional) to allocate per Linux server node",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--gpus-per-linux-client",
            default=1.0,
            help="How many GPUs (fractional) to allocate per Linux client node",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--cpu-overcommit",
            default=0.0,
            help="Fraction of CPUs to overcommit (share) between nodes on an instance",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--cpus-per-linux-server",
            default=1.0,
            help="How many CPUs (fractional) to allocate per Linux server node",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--cpus-per-linux-client",
            default=1.0,
            help="How many CPUs (fractional) to allocate per Linux client node",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--cpus-per-android-client",
            default=1.0,
            help="How many CPUs (fractional) to allocate per Android client node",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--ram-overcommit",
            default=0.0,
            help="Fraction of RAM to overcommit (share) between nodes on an instance",
            required=False,
            show_default=True,
            type=click.FloatRange(min=0.0),
        )(func)
        func = group.option(
            "--ram-per-linux-server",
            default=4096,
            help="How much RAM (in MB) to allocate per Linux server node",
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(func)
        func = group.option(
            "--ram-per-linux-client",
            default=4096,
            help="How much RAM (in MB) to allocate per Linux client node",
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(func)
        func = group.option(
            "--ram-per-android-client",
            default=4096,
            help="How much RAM (in MB) to allocate per Android client node",
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(func)

        return func

    return wrapper

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
    Utilities for AWS mode resource requirements and node scheduling

    Due to the nature of the algorithms throughout this module, many operations
    are repeated for each platform, architecture, with/without GPUs, or client vs
    server. So there is a recurring pattern used throughout this file as follows.

    Data structures contain individual platform/arch/gpu/node-type specific
    attributes (e.g., `linux_gpu_arm64_server_count`). The data structure also
    provides a `get` method to access the attributes programmatically.

    Two global constants exist as lists of tuples to provide parameters for all
    possible instances and nodes. These can be iterated in order to perform logic
    across all valid combinations of parameters.

    For example:
    ```
    for platform, gpu, arch in INSTANCE_COMBOS:
        name = instance_type_names.get(platform, gpu, arch)
    ```
"""

# Python Library Imports
import json
import logging
import math
import os
import pprint
from dataclasses import dataclass, field
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Tuple

# Local Python Library Imports
from rib.utils import aws_utils, error_utils, rib_utils


logger = logging.getLogger(__name__)

RIB_CONFIG = rib_utils.load_race_global_configs()

# Allow overriding via env var as a low-level means of runtime tweaking,
# but we don't want these exposed as arguments.
MIN_MGMT_RESERVE_RAM_MB = int(os.environ.get("RIB_AWS_MIN_MGMT_RESERVE_RAM_MB", 200))
MAX_MGMT_RESERVE_RAM_MB = int(os.environ.get("RIB_AWS_MAX_MGMT_RESERVE_RAM_MB", 1024))
MGMT_RESERVE_RAM_PERCENT = float(
    os.environ.get("RIB_AWS_MGMT_RESERVE_RAM_PERCENT", 0.05)
)

# List of instance parameters to be used with data structure `get` methods
# The tuples contain: platform, has GPU, architecture.
# (no particular order)
INSTANCE_COMBOS: List[Tuple[str, bool, str]] = [
    ("android", False, "arm64"),
    ("android", False, "x86_64"),
    ("linux", True, "arm64"),
    ("linux", True, "x86_64"),
    ("linux", False, "arm64"),
    ("linux", False, "x86_64"),
]

# List of node parameters to be used with data structure `get` methods, sorted
# in architecture-independent descending order of most resource intensive to least
# (android > gpu > linux, server > client)
NODE_COMBOS: List[Tuple[str, bool, str, str]] = [
    # arm64
    ("android", False, "arm64", "client"),
    ("linux", True, "arm64", "server"),
    ("linux", True, "arm64", "client"),
    ("linux", False, "arm64", "server"),
    ("linux", False, "arm64", "client"),
    # x86_64
    ("android", False, "x86_64", "client"),
    ("linux", True, "x86_64", "server"),
    ("linux", True, "x86_64", "client"),
    ("linux", False, "x86_64", "server"),
    ("linux", False, "x86_64", "client"),
]


###
# Utilities
###


def _gpu(gpu: bool) -> str:
    """Returns GPU portion of attribute name if True"""
    return "_gpu" if gpu else ""


@dataclass
class InstanceCounts:
    """EC2 instance counts"""

    android_arm64_instances: int = field(default=0)
    android_x86_64_instances: int = field(default=0)
    linux_gpu_arm64_instances: int = field(default=0)
    linux_gpu_x86_64_instances: int = field(default=0)
    linux_arm64_instances: int = field(default=0)
    linux_x86_64_instances: int = field(default=0)

    def get(self, platform: str, gpu: bool, arch: str) -> int:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_instances")

    def set(self, platform: str, gpu: bool, arch: str, val: int) -> None:
        """Set parameterized attribute (see note at top of file)"""
        setattr(self, f"{platform}{_gpu(gpu)}_{arch}_instances", val)

    @property
    def total(self) -> int:
        """Get total count of all instances"""
        total_count = 0
        for platform, gpu, arch in INSTANCE_COMBOS:
            total_count += self.get(platform, gpu, arch)
        return total_count


@dataclass
class NodeCounts:
    """RACE node counts"""

    android_arm64_clients: int = field(default=0)
    android_x86_64_clients: int = field(default=0)
    linux_gpu_arm64_clients: int = field(default=0)
    linux_gpu_x86_64_clients: int = field(default=0)
    linux_arm64_clients: int = field(default=0)
    linux_x86_64_clients: int = field(default=0)
    linux_gpu_arm64_servers: int = field(default=0)
    linux_gpu_x86_64_servers: int = field(default=0)
    linux_arm64_servers: int = field(default=0)
    linux_x86_64_servers: int = field(default=0)

    def get(self, platform: str, gpu: bool, arch: str, node_type: str) -> int:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_{node_type}s")

    def set(
        self, platform: str, gpu: bool, arch: str, node_type: str, val: int
    ) -> None:
        """Set parameterized attribute (see note at top of file)"""
        setattr(self, f"{platform}{_gpu(gpu)}_{arch}_{node_type}s", val)

    def incr(self, platform: str, gpu: bool, arch: str, node_type: str) -> None:
        """Increment parameterized attribute (see note at top of file)"""
        val = self.get(platform, gpu, arch, node_type)
        self.set(platform, gpu, arch, node_type, val + 1)


###
# AWS topology
###


class NodeInstanceCapacity(BaseModel):
    """Counts of nodes that can run on a particular instance"""

    android_client_count: int = 0
    linux_gpu_client_count: int = 0
    linux_gpu_server_count: int = 0
    linux_client_count: int = 0
    linux_server_count: int = 0

    def __str__(self):
        return (
            f"{self.android_client_count} Android clients, "
            f"{self.linux_gpu_client_count} Linux GPU clients, "
            f"{self.linux_gpu_server_count} Linux GPU servers, "
            f"{self.linux_client_count} Linux clients, "
            f"{self.linux_server_count} Linux servers"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NodeInstanceCapacity):
            return False
        if not other.android_client_count == self.android_client_count:
            return False
        if not other.linux_gpu_client_count == self.linux_gpu_client_count:
            return False
        if not other.linux_gpu_server_count == self.linux_gpu_server_count:
            return False
        if not other.linux_client_count == self.linux_client_count:
            return False
        if not other.linux_server_count == self.linux_server_count:
            return False
        return True

    def get(self, platform: str, gpu: bool, node_type: str) -> int:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{node_type}_count")

    def incr(self, platform: str, gpu: bool, node_type: str) -> None:
        """Increment parameterized attribute (see note at top of file)"""
        val = self.get(platform, gpu, node_type)
        setattr(self, f"{platform}{_gpu(gpu)}_{node_type}_count", val + 1)

    def total_count(self) -> int:
        """Get combined node count across all types"""
        return (
            self.android_client_count
            + self.linux_gpu_client_count
            + self.linux_gpu_server_count
            + self.linux_client_count
            + self.linux_server_count
        )


class NodeInstanceTopology(BaseModel):
    """AWS host instances and the node capacity on each instance"""

    android_x86_64_instances: List[NodeInstanceCapacity] = []
    android_arm64_instances: List[NodeInstanceCapacity] = []
    linux_gpu_x86_64_instances: List[NodeInstanceCapacity] = []
    linux_gpu_arm64_instances: List[NodeInstanceCapacity] = []
    linux_x86_64_instances: List[NodeInstanceCapacity] = []
    linux_arm64_instances: List[NodeInstanceCapacity] = []

    def get(self, platform: str, gpu: bool, arch: str) -> List[NodeInstanceCapacity]:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_instances")


def read_topology_from_file(filename: str) -> NodeInstanceTopology:
    """
    Purpose:
        Reads the topology from a file of the given name
    Args:
        filename: Name of the input file
    Returns:
        AWS env topology from the file
    """
    try:
        return NodeInstanceTopology.parse_file(filename)
    except Exception as err:
        raise error_utils.RIB722(filename, str(err)) from err


def write_topology_to_file(topology: NodeInstanceTopology, out: str) -> None:
    """
    Purpose:
        Writes the given topology to a file of the given name
    Args:
        topology: AWS env topology to be written
        out: Name of the output file
    Returns:
        N/A
    """
    with open(out, "w") as outfile:
        json.dump(topology.dict(), outfile, indent=2, sort_keys=True)


def is_topology_compatible_with(
    topology: NodeInstanceTopology,
    max_instance_counts: InstanceCounts,
    min_node_counts: NodeCounts,
) -> bool:
    """
    Purpose:
        Verifies if the given topology is compatible with the given instance and node counts:
            * The topology must require no more than the specified number of instances
            * The topology must define at least the specified number of nodes
    Args:
        topology: AWS env topology to be validated
        max_instance_counts: Maximum number of instances the topology may contain
        min_node_counts: Minimum number of RACE nodes the topology must contain
    Return:
        True if topology contains no more than the specified instance counts and at least the
            specified node counts
    """
    for platform, gpu, arch in INSTANCE_COMBOS:
        # If the topology requires more instances than are given, it's not compatible
        needed_count = len(topology.get(platform, gpu, arch))
        actual_count = max_instance_counts.get(platform, gpu, arch)
        if needed_count > actual_count:
            logger.warning(
                f"Topology requires {needed_count} {platform}{' GPU' if gpu else ''} {arch} "
                f"instances but only {actual_count} available"
            )
            return False

    # Get cumulative node capacity across all instances in the topology
    total_capacity = NodeCounts()

    for instance in (
        topology.android_arm64_instances
        + topology.linux_gpu_arm64_instances
        + topology.linux_arm64_instances
    ):
        total_capacity.android_arm64_clients += instance.android_client_count
        total_capacity.linux_gpu_arm64_clients += instance.linux_gpu_client_count
        total_capacity.linux_arm64_clients += instance.linux_client_count
        total_capacity.linux_gpu_arm64_servers += instance.linux_gpu_server_count
        total_capacity.linux_arm64_servers += instance.linux_server_count

    for instance in (
        topology.android_x86_64_instances
        + topology.linux_gpu_x86_64_instances
        + topology.linux_x86_64_instances
    ):
        total_capacity.android_x86_64_clients += instance.android_client_count
        total_capacity.linux_gpu_x86_64_clients += instance.linux_gpu_client_count
        total_capacity.linux_x86_64_clients += instance.linux_client_count
        total_capacity.linux_gpu_x86_64_servers += instance.linux_gpu_server_count
        total_capacity.linux_x86_64_servers += instance.linux_server_count

    for platform, gpu, arch, node_type in NODE_COMBOS:
        # If more nodes are required than the topology has capacity for, it's not compatible
        needed_count = min_node_counts.get(platform, gpu, arch, node_type)
        actual_count = total_capacity.get(platform, gpu, arch, node_type)
        if actual_count < needed_count:
            logger.warning(
                f"Need {needed_count} {platform}{' GPU' if gpu else ''} {arch} {node_type}s "
                f"but only {actual_count} available in the topology"
            )
            return False

    return True


def instance_counts_from_topology(topology: NodeInstanceTopology) -> InstanceCounts:
    """
    Purpose:
        Extract the EC2 instance counts as defined in the given topology
    Args:
        topology: Node instance topology
    Returns:
        Counts of all instances defined in the topology
    """

    instance_counts = InstanceCounts()

    for platform, gpu, arch in INSTANCE_COMBOS:
        instance_counts.set(platform, gpu, arch, len(topology.get(platform, gpu, arch)))

    return instance_counts


def get_node_counts_from_range_config(range_config: Dict[str, Any]) -> NodeCounts:
    """
    Purpose:
        Extract node counts from the given range config
    Args:
        range_config: Range configuration definition
    Returns:
        Node counts
    """

    node_counts = NodeCounts()

    for node in range_config.get("range", {}).get("RACE_nodes", []):
        # Don't include bridged nodes in node counts because they aren't part of a topology
        arch = node.get("architecture", "x86_64")
        if arch == "auto":
            continue
        node_counts.incr(
            platform=node.get("platform", "linux"),
            gpu=node.get("gpu", False),
            arch="arm64" if arch == "arm64-v8a" else arch,
            node_type=node.get("type", "client"),
        )

    return node_counts


###
# Topology generation by instance counts
###


def _validate_instance_count_for_nodes(
    name: str, node_count: int, instance_count: int
) -> None:
    """Ensure at least one instance specified if any nodes were specified"""
    if node_count and not instance_count:
        raise error_utils.RIB721(
            f"{name} nodes requested, but no {name} instances specified",
            f"Re-run the command with at least one {name} instance",
        )


def _validate_multiple_instances_for_nodes(
    name: str, client_count: int, server_count: int, instance_count: int
) -> None:
    """Ensure at least two instances specified if both clients and servers were specified"""
    if client_count and server_count and instance_count == 1:
        raise error_utils.RIB721(
            f"Non-colocated {name} clients and servers requested, but only one {name} instance specified",
            f"Re-run the command with more than one {name} instance",
        )


def _calc_client_count(
    instance_index: int, instance_count: int, client_count: int
) -> int:
    """
    Calculate the number of clients to host on a particular instance out of all applicable instances
    """
    # instance indices below this index will have more nodes than instances above it
    switching_index = client_count % instance_count
    round_func = math.ceil if instance_index < switching_index else math.floor
    return round_func(client_count / instance_count)


def _calc_server_count(
    instance_index: int, instance_count: int, server_count: int
) -> int:
    """
    Calculate the number of servers to host on a particular instance out of all applicable instances
    """
    # instance indices below this index will have less nodes than instances above it
    switching_index = instance_count - server_count % instance_count
    round_func = math.floor if instance_index < switching_index else math.ceil
    return round_func(server_count / instance_count)


def _create_instance_capacities_from_node_counts(
    instance_count: int,
    android_client_count: int = 0,
    linux_gpu_client_count: int = 0,
    linux_gpu_server_count: int = 0,
    linux_client_count: int = 0,
    linux_server_count: int = 0,
) -> List[NodeInstanceCapacity]:
    """
    Create a list of node capacities with the specified count, spreading the given node
    counts across the instances
    """
    instances = []
    if instance_count > 0:
        for index in range(instance_count):
            instances.append(
                NodeInstanceCapacity(
                    android_client_count=_calc_client_count(
                        index, instance_count, android_client_count
                    ),
                    linux_gpu_client_count=_calc_client_count(
                        index, instance_count, linux_gpu_client_count
                    ),
                    linux_client_count=_calc_client_count(
                        index, instance_count, linux_client_count
                    ),
                    linux_gpu_server_count=_calc_server_count(
                        index, instance_count, linux_gpu_server_count
                    ),
                    linux_server_count=_calc_server_count(
                        index, instance_count, linux_server_count
                    ),
                )
            )

    return instances


def _split_by_client_ratio(
    instance_count: int, client_count: int, server_count: int
) -> Tuple[int, int]:
    """
    Calculate the number of instances to host clients vs servers, according to the ratio
    of clients to servers
    """
    if client_count + server_count == 0:
        return (0, 0)
    client_instance_count = math.floor(
        instance_count * client_count / (client_count + server_count)
    )
    if client_instance_count == 0 and client_count > 0:
        client_instance_count = 1
    return (client_instance_count, instance_count - client_instance_count)


def create_topology_from_instance_counts(
    instance_counts: InstanceCounts,
    node_counts: NodeCounts,
    colocate_clients_and_servers: bool,
) -> NodeInstanceTopology:
    """
    Purpose:
        Create a topology using a fixed instance count.

        If colocation of clients and servers is allowed, they will be evenly distributed
        across all instances capable of hosting them. Colocation of Linux nodes on Android
        instances, or non-GPU Linux nodes on GPU instances, is not supported.

    Args:
        instance_counts: Number of EC2 instance hosts to use in the topology
        node_counts: Number of RACE nodes to use in the topology
        colocate_clients_and_servers: Whether to colocate clients and servers on the same host

    Returns:
        Node instance topology
    """
    # Verify required instances have been specified
    for arch in ["arm64", "x86_64"]:
        _validate_instance_count_for_nodes(
            f"Android {arch}",
            node_counts.get("android", False, arch, "client"),
            instance_counts.get("android", False, arch),
        )

    for gpu in [True, False]:
        for arch in ["arm64", "x86_64"]:
            _validate_instance_count_for_nodes(
                f"Linux{' GPU' if gpu else ''} {arch}",
                (
                    node_counts.get("linux", gpu, arch, "client")
                    + node_counts.get("linux", gpu, arch, "server")
                ),
                instance_counts.get("linux", gpu, arch),
            )

    topology = NodeInstanceTopology()
    topology.android_arm64_instances = _create_instance_capacities_from_node_counts(
        instance_counts.android_arm64_instances,
        android_client_count=node_counts.android_arm64_clients,
    )
    topology.android_x86_64_instances = _create_instance_capacities_from_node_counts(
        instance_counts.android_x86_64_instances,
        android_client_count=node_counts.android_x86_64_clients,
    )

    if colocate_clients_and_servers:
        # When colocated, evenly spread clients and servers onto the same instances
        topology.linux_gpu_arm64_instances = (
            _create_instance_capacities_from_node_counts(
                instance_counts.linux_gpu_arm64_instances,
                linux_gpu_client_count=node_counts.linux_gpu_arm64_clients,
                linux_gpu_server_count=node_counts.linux_gpu_arm64_servers,
            )
        )
        topology.linux_gpu_x86_64_instances = (
            _create_instance_capacities_from_node_counts(
                instance_counts.linux_gpu_x86_64_instances,
                linux_gpu_client_count=node_counts.linux_gpu_x86_64_clients,
                linux_gpu_server_count=node_counts.linux_gpu_x86_64_servers,
            )
        )
        topology.linux_arm64_instances = _create_instance_capacities_from_node_counts(
            instance_counts.linux_arm64_instances,
            linux_client_count=node_counts.linux_arm64_clients,
            linux_server_count=node_counts.linux_arm64_servers,
        )
        topology.linux_x86_64_instances = _create_instance_capacities_from_node_counts(
            instance_counts.linux_x86_64_instances,
            linux_client_count=node_counts.linux_x86_64_clients,
            linux_server_count=node_counts.linux_x86_64_servers,
        )

    else:
        # Validate required instances have been specified
        for gpu in [True, False]:
            for arch in ["arm64", "x86_64"]:
                _validate_multiple_instances_for_nodes(
                    f"Linux{' GPU' if gpu else ''} {arch}",
                    node_counts.get("linux", gpu, arch, "client"),
                    node_counts.get("linux", gpu, arch, "server"),
                    instance_counts.get("linux", gpu, arch),
                )

        # Determine number of instances to host clients vs servers
        (
            linux_gpu_arm64_client_instance_count,
            linux_gpu_arm64_server_instance_count,
        ) = _split_by_client_ratio(
            instance_counts.linux_gpu_arm64_instances,
            node_counts.linux_gpu_arm64_clients,
            node_counts.linux_gpu_arm64_servers,
        )
        (
            linux_gpu_x86_64_client_instance_count,
            linux_gpu_x86_64_server_instance_count,
        ) = _split_by_client_ratio(
            instance_counts.linux_gpu_x86_64_instances,
            node_counts.linux_gpu_x86_64_clients,
            node_counts.linux_gpu_x86_64_servers,
        )
        (
            linux_arm64_client_instance_count,
            linux_arm64_server_instance_count,
        ) = _split_by_client_ratio(
            instance_counts.linux_arm64_instances,
            node_counts.linux_arm64_clients,
            node_counts.linux_arm64_servers,
        )
        (
            linux_x86_64_client_instance_count,
            linux_x86_64_server_instance_count,
        ) = _split_by_client_ratio(
            instance_counts.linux_x86_64_instances,
            node_counts.linux_x86_64_clients,
            node_counts.linux_x86_64_servers,
        )

        # Spread clients and servers onto separate instances
        topology.linux_gpu_arm64_instances = (
            _create_instance_capacities_from_node_counts(
                linux_gpu_arm64_client_instance_count,
                linux_gpu_client_count=node_counts.linux_gpu_arm64_clients,
            )
            + _create_instance_capacities_from_node_counts(
                linux_gpu_arm64_server_instance_count,
                linux_gpu_server_count=node_counts.linux_gpu_arm64_servers,
            )
        )
        topology.linux_gpu_x86_64_instances = (
            _create_instance_capacities_from_node_counts(
                linux_gpu_x86_64_client_instance_count,
                linux_gpu_client_count=node_counts.linux_gpu_x86_64_clients,
            )
            + _create_instance_capacities_from_node_counts(
                linux_gpu_x86_64_server_instance_count,
                linux_gpu_server_count=node_counts.linux_gpu_x86_64_servers,
            )
        )
        topology.linux_arm64_instances = _create_instance_capacities_from_node_counts(
            linux_arm64_client_instance_count,
            linux_client_count=node_counts.linux_arm64_clients,
        ) + _create_instance_capacities_from_node_counts(
            linux_arm64_server_instance_count,
            linux_server_count=node_counts.linux_arm64_servers,
        )
        topology.linux_x86_64_instances = _create_instance_capacities_from_node_counts(
            linux_x86_64_client_instance_count,
            linux_client_count=node_counts.linux_x86_64_clients,
        ) + _create_instance_capacities_from_node_counts(
            linux_x86_64_server_instance_count,
            linux_server_count=node_counts.linux_x86_64_servers,
        )

    return topology


###
# Topology generation by nodes-per-instance parameters
###


def _calculate_node_counts_from_instances_and_nodes_per_instance(
    nodes_per_instance: NodeCounts,
    instance_counts: InstanceCounts,
) -> NodeCounts:
    """
    Calculate the total node counts resulting from instance counts and nodes-per-instance
    """
    node_counts = NodeCounts()

    for platform, gpu, arch, node_type in NODE_COMBOS:
        count = instance_counts.get(platform, gpu, arch) * nodes_per_instance.get(
            platform, gpu, arch, node_type
        )
        node_counts.set(platform, gpu, arch, node_type, count)

    return node_counts


def _calculate_instance_counts_from_nodes_and_nodes_per_instance(
    nodes_per_instance: NodeCounts,
    node_counts: NodeCounts,
    colocate_clients_and_servers: bool,
) -> InstanceCounts:
    """
    Calculate the number of instances required to host the given node counts using
    nodes-per-instance parameters
    """

    instance_counts = InstanceCounts()

    for arch in ["arm64", "x86_64"]:
        clients_per_instance = nodes_per_instance.get("android", False, arch, "client")
        if clients_per_instance:
            count = math.ceil(
                node_counts.get("android", False, arch, "client") / clients_per_instance
            )
            instance_counts.set("android", False, arch, count)

    for gpu in [True, False]:
        for arch in ["arm64", "x86_64"]:
            clients_per_instance = nodes_per_instance.get("linux", gpu, arch, "client")
            if clients_per_instance:
                client_count = math.ceil(
                    node_counts.get("linux", gpu, arch, "client") / clients_per_instance
                )
            else:
                client_count = 0

            servers_per_instance = nodes_per_instance.get("linux", gpu, arch, "server")
            if servers_per_instance:
                server_count = math.ceil(
                    node_counts.get("linux", gpu, arch, "server") / servers_per_instance
                )
            else:
                server_count = 0

            if colocate_clients_and_servers:
                instance_counts.set("linux", gpu, arch, max(client_count, server_count))
            else:
                instance_counts.set("linux", gpu, arch, client_count + server_count)

    return instance_counts


def create_topology_from_nodes_per_instance(
    nodes_per_instance: NodeCounts,
    colocate_clients_and_servers: bool,
    instance_counts: Optional[InstanceCounts] = None,
    node_counts: Optional[NodeCounts] = None,
) -> NodeInstanceTopology:
    if not instance_counts and not node_counts:
        raise error_utils.RIB721(
            "Neither node counts nor instance counts were provided",
            "Specify either node counts or instance counts",
        )
    if instance_counts and node_counts:
        raise error_utils.RIB721(
            "Both node counts and instance counts were provided",
            "Specify either node counts or instance counts",
        )

    # If instance counts were provided but not node counts, calculate the resulting node counts
    if not node_counts:
        if not colocate_clients_and_servers:
            # We cannot determine the total number of clients and servers without knowing how
            # many of the instances are hosting clients vs servers
            raise error_utils.RIB721(
                "Cannot determine node counts from non-colocated nodes-per-instance",
                "Enable colocation of clients and servers or specify instance counts instead",
            )

        node_counts = _calculate_node_counts_from_instances_and_nodes_per_instance(
            nodes_per_instance=nodes_per_instance,
            instance_counts=instance_counts,
        )

    # Else if node counts were provided but not instance counts, calculate how many instances
    # are needed
    if not instance_counts:
        instance_counts = _calculate_instance_counts_from_nodes_and_nodes_per_instance(
            nodes_per_instance=nodes_per_instance,
            node_counts=node_counts,
            colocate_clients_and_servers=colocate_clients_and_servers,
        )

    return create_topology_from_instance_counts(
        instance_counts=instance_counts,
        node_counts=node_counts,
        colocate_clients_and_servers=colocate_clients_and_servers,
    )


###
# Instance type utilities
###


@dataclass
class InstanceTypeNames:
    """Instance type names"""

    android_x86_64_instance_type_name: str = field(default=None)
    android_arm64_instance_type_name: str = field(default=None)
    linux_gpu_x86_64_instance_type_name: str = field(default=None)
    linux_gpu_arm64_instance_type_name: str = field(default=None)
    linux_x86_64_instance_type_name: str = field(default=None)
    linux_arm64_instance_type_name: str = field(default=None)
    # Optional instance types (not used as part of topology creation)
    cluster_manager_instance_type_name: str = field(default=None)
    service_host_instance_type_name: str = field(default=None)

    def get(self, platform: str, gpu: bool, arch: str) -> str:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_instance_type_name")

    def set(self, platform: str, gpu: bool, arch: str, val: str) -> None:
        """set parameterized attribute (see note at top of file)"""
        setattr(self, f"{platform}{_gpu(gpu)}_{arch}_instance_type_name", val)


@dataclass
class InstanceEbsSizes:
    """Instance EBS sizes (in GB)"""

    android_instance_ebs_size_gb: int = field(default=0)
    linux_gpu_instance_ebs_size_gb: int = field(default=0)
    linux_instance_ebs_size_gb: int = field(default=0)
    cluster_manager_instance_ebs_size_gb: int = field(default=0)
    service_host_instance_ebs_size_gb: int = field(default=0)

    def get(self, platform: str, gpu: bool) -> int:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_instance_ebs_size_gb")

    def set(self, platform: str, gpu: bool, val: str) -> None:
        """set parameterized attribute (see note at top of file)"""
        setattr(self, f"{platform}{_gpu(gpu)}_instance_ebs_size_gb", val)


@dataclass
class InstanceTypes:
    """Instance type details"""

    android_x86_64_instance_type: aws_utils.Ec2InstanceTypeDetails = field(default=None)
    android_arm64_instance_type: aws_utils.Ec2InstanceTypeDetails = field(default=None)
    linux_gpu_x86_64_instance_type: aws_utils.Ec2InstanceTypeDetails = field(
        default=None
    )
    linux_gpu_arm64_instance_type: aws_utils.Ec2InstanceTypeDetails = field(
        default=None
    )
    linux_x86_64_instance_type: aws_utils.Ec2InstanceTypeDetails = field(default=None)
    linux_arm64_instance_type: aws_utils.Ec2InstanceTypeDetails = field(default=None)

    def get(
        self, platform: str, gpu: bool, arch: str
    ) -> aws_utils.Ec2InstanceTypeDetails:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_instance_type")

    def set(
        self, platform: str, gpu: bool, arch: str, val: aws_utils.Ec2InstanceTypeDetails
    ) -> None:
        """set parameterized attribute (see note at top of file)"""
        setattr(self, f"{platform}{_gpu(gpu)}_{arch}_instance_type", val)


def _validate_instance_type_is_metal(
    flag: str,
    instance_type_details: aws_utils.Ec2InstanceTypeDetails,
) -> None:
    if not instance_type_details.is_metal:
        raise error_utils.RIB719(
            flag,
            instance_type_details.name,
            "Must be a metal instance type",
        )


def _validate_instance_type_has_gpus(
    flag: str,
    instance_type_details: aws_utils.Ec2InstanceTypeDetails,
) -> None:
    if not instance_type_details.gpus:
        raise error_utils.RIB719(
            flag,
            instance_type_details.name,
            "Must be an instance type with GPUs (e.g., G3, G4, P3, or P4)"
            if instance_type_details.arch == "x86_64"
            else "Must be an instance type with GPUs (e.g., G5g)",
        )


def _validate_instance_type_arch(
    flag: str,
    instance_type_details: aws_utils.Ec2InstanceTypeDetails,
    required_arch: str,
) -> None:
    if not instance_type_details.arch == required_arch:
        raise error_utils.RIB719(
            flag,
            instance_type_details.name,
            "Cannot be a Graviton (ARM) instance type"
            if required_arch == "x86_64"
            else "Must be a Graviton (ARM) instance type",
        )


def get_instance_type_details(
    instance_type_names: InstanceTypeNames, instance_counts: InstanceCounts = None
) -> InstanceTypes:
    """
    Purpose:
        Get details about the specified instance types, ensuring compatibility between
        the instance type capabilities and the intended use of the instance type
    Args:
        instance_type_names: Names of the EC2 instance types
    Returns:
        Instance type details
    """
    session = aws_utils.connect_aws_session_with_profile()

    instance_names = []

    # If we are not given any instance counts validate all instance combos
    # else only check an instance combo if it had a non-zero count
    if not instance_counts or instance_counts.android_x86_64_instances > 0:
        instance_names.append(instance_type_names.android_x86_64_instance_type_name)
    if not instance_counts or instance_counts.android_arm64_instances > 0:
        instance_names.append(instance_type_names.android_arm64_instance_type_name)
    if not instance_counts or instance_counts.linux_gpu_x86_64_instances > 0:
        instance_names.append(instance_type_names.linux_gpu_x86_64_instance_type_name)
    if not instance_counts or instance_counts.linux_gpu_arm64_instances > 0:
        instance_names.append(instance_type_names.linux_gpu_arm64_instance_type_name)
    if not instance_counts or instance_counts.linux_x86_64_instances > 0:
        instance_names.append(instance_type_names.linux_x86_64_instance_type_name)
    if not instance_counts or instance_counts.linux_arm64_instances > 0:
        instance_names.append(instance_type_names.linux_arm64_instance_type_name)

    all_details = aws_utils.get_ec2_instance_type_details(
        session,
        list(set(instance_names)),
    )

    logger.trace(f"Instance type details =\n{pprint.pformat(all_details)}")

    instance_types = InstanceTypes()

    for platform, gpu, arch in INSTANCE_COMBOS:
        instance_type = instance_type_names.get(platform, gpu, arch)
        if instance_type not in all_details:
            continue

        details = all_details[instance_type]

        _validate_instance_type_arch(
            f"--{platform}-{arch[:3]}{'-gpu' if gpu else ''}-instance-type",
            details,
            arch,
        )
        if platform == "android":
            _validate_instance_type_is_metal(
                f"--android-{arch[:3]}-instance-type",
                details,
            )
        if gpu:
            _validate_instance_type_has_gpus(
                f"--{platform}-{arch[:3]}-gpu-instance-type",
                details,
            )

        instance_types.set(platform, gpu, arch, details)

    return instance_types


###
# Topology generation by node resource requirements
###


@dataclass
class NodeResourceReqs:
    """RAM and CPU requirements for a single RACE node type"""

    ram_per_node: int = field(default=0)
    ram_overcommit: float = field(default=0)
    cpus_per_node: float = field(default=0)
    cpu_overcommit: float = field(default=0)
    gpus_per_node: float = field(default=0)
    gpu_overcommit: float = field(default=0)

    @property
    def guaranteed_cpus(self) -> float:
        """Number of guaranteed CPUs (fractional) for the node"""
        return self.cpus_per_node * (1 - self.cpu_overcommit)

    @property
    def overcommitted_cpus(self) -> float:
        """Number of overcommitted (shared) CPUs (fractional) for the node"""
        return self.cpus_per_node * self.cpu_overcommit

    @property
    def guaranteed_gpus(self) -> float:
        """Number of guaranteed GPUs (fractional) for the node"""
        return self.gpus_per_node * (1 - self.gpu_overcommit)

    @property
    def overcommitted_gpus(self) -> float:
        """Number of overcommitted (shared) GPUs (fractional) for the node"""
        return self.gpus_per_node * self.gpu_overcommit

    @property
    def guaranteed_ram(self) -> int:
        """Amount of guaranteed RAM (in MB) for the node"""
        return self.ram_per_node * (1 - self.ram_overcommit)

    @property
    def overcommitted_ram(self) -> int:
        """Amount of overcommitted (shared) RAM (in MB) for the node"""
        return round(self.ram_per_node * self.ram_overcommit)


@dataclass
class NodeResourceConstraints:
    """RAM and CPU requirements for RACE nodes"""

    ram_per_android_client: int
    ram_per_linux_client: int
    ram_per_linux_server: int
    ram_overcommit: float
    cpus_per_android_client: float
    cpus_per_linux_client: float
    cpus_per_linux_server: float
    cpu_overcommit: float
    gpus_per_linux_client: float
    gpus_per_linux_server: float
    gpu_overcommit: float

    def get(self, platform: str, gpu: bool, node_type: str) -> NodeResourceReqs:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{node_type}")

    @property
    def android_client(self) -> NodeResourceReqs:
        """Resource requirements for Android client nodes"""
        return NodeResourceReqs(
            ram_per_node=self.ram_per_android_client,
            ram_overcommit=self.ram_overcommit,
            cpus_per_node=self.cpus_per_android_client,
            cpu_overcommit=self.cpu_overcommit,
            gpus_per_node=0,
            gpu_overcommit=0,
        )

    @property
    def linux_client(self) -> NodeResourceReqs:
        """Resource requirements for Linux client nodes"""
        return NodeResourceReqs(
            ram_per_node=self.ram_per_linux_client,
            ram_overcommit=self.ram_overcommit,
            cpus_per_node=self.cpus_per_linux_client,
            cpu_overcommit=self.cpu_overcommit,
            gpus_per_node=0,
            gpu_overcommit=0,
        )

    @property
    def linux_gpu_client(self) -> NodeResourceReqs:
        """Resource requirements for Linux GPU client nodes"""
        return NodeResourceReqs(
            ram_per_node=self.ram_per_linux_client,
            ram_overcommit=self.ram_overcommit,
            cpus_per_node=self.cpus_per_linux_client,
            cpu_overcommit=self.cpu_overcommit,
            gpus_per_node=self.gpus_per_linux_client,
            gpu_overcommit=self.gpu_overcommit,
        )

    @property
    def linux_server(self) -> NodeResourceReqs:
        """Resource requirements for Linux server nodes"""
        return NodeResourceReqs(
            ram_per_node=self.ram_per_linux_server,
            ram_overcommit=self.ram_overcommit,
            cpus_per_node=self.cpus_per_linux_server,
            cpu_overcommit=self.cpu_overcommit,
            gpus_per_node=0,
            gpu_overcommit=0,
        )

    @property
    def linux_gpu_server(self) -> NodeResourceReqs:
        """Resource requirements for Linux GPU server nodes"""
        return NodeResourceReqs(
            ram_per_node=self.ram_per_linux_server,
            ram_overcommit=self.ram_overcommit,
            cpus_per_node=self.cpus_per_linux_server,
            cpu_overcommit=self.cpu_overcommit,
            gpus_per_node=self.gpus_per_linux_server,
            gpu_overcommit=self.gpu_overcommit,
        )


@dataclass
class RaceNode:
    """A RACE node that has been assigned to a host instance"""

    persona: str
    requirements: NodeResourceReqs
    architecture: str
    node_type: str
    platform: str
    requires_metal: bool
    requires_gpus: bool


class HostInstance:
    """A single host EC2 instance and its assigned nodes"""

    def __init__(
        self,
        details: aws_utils.Ec2InstanceTypeDetails,
        node_type: Optional[str] = None,
        only_requires_gpus: Optional[bool] = True,
        platform: Optional[str] = None,
    ):
        """Initalizes the host instance"""

        self.details = details
        self.race_nodes: List[RaceNode] = []
        self.node_type = node_type
        self.only_requires_gpus = only_requires_gpus
        self.platform = platform

        self.mgmt_overhead_reserve_ram = min(
            MAX_MGMT_RESERVE_RAM_MB,
            max(MIN_MGMT_RESERVE_RAM_MB, details.ram_mb * MGMT_RESERVE_RAM_PERCENT),
        )

        self.guaranteed_ram = 0
        self.overcommitted_ram = 0
        self.guaranteed_cpus = 0
        self.overcommitted_cpus = 0
        self.guaranteed_gpus = 0
        self.overcommitted_gpus = 0

    @property
    def capacity(self) -> NodeInstanceCapacity:
        """Available capacity for nodes to reside on this host"""
        cap = NodeInstanceCapacity()

        for node in self.race_nodes:
            cap.incr(node.platform, node.requires_gpus, node.node_type)

        return cap

    def can_host(self, node: RaceNode) -> bool:
        """Checks if this instance is capable of hosting the given RACE node"""
        # Instance architecture must match node architecture
        if node.architecture != self.details.arch:
            return False
        # If node requires metal instances, check if this instance is metal
        if node.requires_metal and not self.details.is_metal:
            return False
        # If node requires GPUs, check if this instance has any GPUs
        if node.requires_gpus and not self.details.gpus:
            return False
        # If this instance can only host GPU-requiring nodes, check that the node requires GPUs
        if self.only_requires_gpus and not node.requires_gpus:
            return False
        # If this instance can only host certain node types, check that they match
        if self.node_type and self.node_type != node.node_type:
            return False
        # If this instance can only host certain platforms, check that they match
        if self.platform and self.platform != node.platform:
            return False
        # Check if there are enough remaining GPUs
        if (
            self.guaranteed_gpus
            + node.requirements.guaranteed_gpus
            + max(self.overcommitted_gpus, node.requirements.overcommitted_gpus)
        ) > self.details.gpus:
            return False
        # Check if there is enough remaining RAM
        if (
            self.guaranteed_ram
            + node.requirements.guaranteed_ram
            + max(self.overcommitted_ram, node.requirements.overcommitted_ram)
            + self.mgmt_overhead_reserve_ram
        ) > self.details.ram_mb:
            return False
        # Check if there is enough remaining CPU
        if (
            self.guaranteed_cpus
            + node.requirements.guaranteed_cpus
            + max(self.overcommitted_cpus, node.requirements.overcommitted_cpus)
        ) > self.details.cpus:
            return False

        return True

    def add(self, node: RaceNode) -> None:
        """Adds the given RACE node to this instance"""
        self.race_nodes.append(node)
        self.guaranteed_ram += node.requirements.guaranteed_ram
        self.overcommitted_ram = max(
            self.overcommitted_ram, node.requirements.overcommitted_ram
        )
        self.guaranteed_cpus += node.requirements.guaranteed_cpus
        self.overcommitted_cpus = max(
            self.overcommitted_cpus, node.requirements.overcommitted_cpus
        )
        self.guaranteed_gpus += node.requirements.guaranteed_gpus
        self.overcommitted_gpus = max(
            self.overcommitted_gpus, node.requirements.overcommitted_gpus
        )

    def add_if_able_to_host(self, node: RaceNode) -> bool:
        """Add the given RACE node to this instance if it is capable of hosting it"""
        if not self.can_host(node):
            return False

        # Otherwise it fits, so add it
        self.add(node)
        return True


@dataclass
class HostInstanceTopology:
    """Topology of host instances and the nodes they are hosting"""

    android_x86_64_instances: List[HostInstance] = field(default_factory=list)
    android_arm64_instances: List[HostInstance] = field(default_factory=list)
    linux_gpu_x86_64_instances: List[HostInstance] = field(default_factory=list)
    linux_gpu_arm64_instances: List[HostInstance] = field(default_factory=list)
    linux_x86_64_instances: List[HostInstance] = field(default_factory=list)
    linux_arm64_instances: List[HostInstance] = field(default_factory=list)

    def get(self, platform: str, gpu: bool, arch: str) -> List[HostInstance]:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_instances")

    @property
    def instance_topology(self) -> NodeInstanceTopology:
        topology = NodeInstanceTopology()
        topology.android_arm64_instances = [
            x.capacity for x in self.android_arm64_instances
        ]
        topology.android_x86_64_instances = [
            x.capacity for x in self.android_x86_64_instances
        ]
        topology.linux_gpu_arm64_instances = [
            x.capacity for x in self.linux_gpu_arm64_instances
        ]
        topology.linux_gpu_x86_64_instances = [
            x.capacity for x in self.linux_gpu_x86_64_instances
        ]
        topology.linux_arm64_instances = [
            x.capacity for x in self.linux_arm64_instances
        ]
        topology.linux_x86_64_instances = [
            x.capacity for x in self.linux_x86_64_instances
        ]
        return topology


class HostInstanceFactory:
    """Factory for creating new host instances and tracking how many have been created"""

    def __init__(self, instance_types: InstanceTypes):
        """Initializes the factory"""
        self.instance_types = instance_types
        self.instances: List[HostInstance] = []
        self.topology = HostInstanceTopology()

    def create_instance_for_node(
        self, node: RaceNode, allow_colocation: bool
    ) -> HostInstance:
        """
        Creates a new host instance suitable for hosting the given RACE node, optionally able to
        colocate with RACE nodes of other types or platforms
        """
        instance_type_details = self.instance_types.get(
            node.platform, node.requires_gpus, node.architecture
        )
        topology_list = self.topology.get(
            node.platform, node.requires_gpus, node.architecture
        )
        instance = HostInstance(
            details=instance_type_details,
            node_type=None if allow_colocation else node.node_type,
            only_requires_gpus=(
                False if not node.requires_gpus or allow_colocation else True
            ),
            platform=None if allow_colocation else node.platform,
        )
        self.instances.append(instance)
        topology_list.append(instance)
        return instance


def _create_nodes_with_reqs(
    count: int,
    requirements: NodeResourceReqs,
    platform: str,
    node_type: str,
    architecture: str,
    requires_metal: bool,
    requires_gpus: bool,
) -> List[RaceNode]:
    """Create a list of RACE nodes with the given properties"""
    nodes = []
    for _ in range(count):
        nodes.append(
            RaceNode(
                persona="",
                requirements=requirements,
                architecture=architecture,
                node_type=node_type,
                platform=platform,
                requires_metal=requires_metal,
                requires_gpus=requires_gpus,
            )
        )
    return nodes


def _assign_nodes(
    nodes: List[RaceNode], factory: HostInstanceFactory, allow_colocation: bool
):
    """
    Assign nodes in the given list to host instances of the given factory, using the
    fast-fit-descending bin packing algorithm
    """
    for node in nodes:
        for instance in factory.instances:
            if instance.add_if_able_to_host(node):
                break
        else:
            new_instance = factory.create_instance_for_node(node, allow_colocation)
            if not new_instance.add_if_able_to_host(node):
                raise error_utils.RIB721(
                    msg=(
                        f"Instance type {new_instance.details.name} is incapable of hosting "
                        f"{node.architecture} {node.platform} {node.node_type} nodes "
                        "due to node resource requirements"
                    ),
                    suggestion="Reduce the node resource requirements or choose a larger instance type",
                )


def create_topology_from_node_resource_requirements(
    allow_colocation: bool,
    instance_type_names: InstanceTypeNames,
    node_resource_constraints: NodeResourceConstraints,
    node_counts: NodeCounts,
) -> HostInstanceTopology:
    reqs = node_resource_constraints
    instance_types = get_instance_type_details(instance_type_names)
    factory = HostInstanceFactory(instance_types)

    # Use first-fit-descending (FFD) bin packing algorithm, using node assignment order of
    # android first, then gpu servers, gpu clients, linux servers, then lastly linux clients
    # (arch doesn't matter in the order, since you can't mix them anyway)
    for platform, gpu, arch, node_type in NODE_COMBOS:
        count = node_counts.get(platform, gpu, arch, node_type)
        reqs = node_resource_constraints.get(platform, gpu, node_type)
        metal = platform == "android"
        _assign_nodes(
            _create_nodes_with_reqs(count, reqs, platform, node_type, arch, metal, gpu),
            factory,
            allow_colocation,
        )

    return factory.topology


###
# Node instance distribution
###


@dataclass
class Personas:
    """Lists of personas by node type"""

    android_x86_64_client_personas: List[str] = field(default_factory=list)
    android_arm64_client_personas: List[str] = field(default_factory=list)
    linux_gpu_x86_64_client_personas: List[str] = field(default_factory=list)
    linux_gpu_arm64_client_personas: List[str] = field(default_factory=list)
    linux_x86_64_client_personas: List[str] = field(default_factory=list)
    linux_arm64_client_personas: List[str] = field(default_factory=list)
    linux_gpu_x86_64_server_personas: List[str] = field(default_factory=list)
    linux_gpu_arm64_server_personas: List[str] = field(default_factory=list)
    linux_x86_64_server_personas: List[str] = field(default_factory=list)
    linux_arm64_server_personas: List[str] = field(default_factory=list)

    def get(self, platform: str, gpu: bool, arch: str, node_type: str) -> List[str]:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_{node_type}_personas")


class NodeInstanceManifest(BaseModel):
    """Manifest of nodes that can run on a particular instance"""

    android_clients: List[str] = []
    linux_gpu_clients: List[str] = []
    linux_clients: List[str] = []
    linux_gpu_servers: List[str] = []
    linux_servers: List[str] = []

    def get(self, platform: str, gpu: bool, node_type: str) -> List[str]:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{node_type}s")


class NodeInstanceDistribution(BaseModel):
    """Distribution of nodes across instances"""

    android_x86_64_instances: List[NodeInstanceManifest] = []
    android_arm64_instances: List[NodeInstanceManifest] = []
    linux_gpu_x86_64_instances: List[NodeInstanceManifest] = []
    linux_gpu_arm64_instances: List[NodeInstanceManifest] = []
    linux_x86_64_instances: List[NodeInstanceManifest] = []
    linux_arm64_instances: List[NodeInstanceManifest] = []

    def get(self, platform: str, gpu: bool, arch: str) -> List[NodeInstanceManifest]:
        """Get parameterized attribute (see note at top of file)"""
        return getattr(self, f"{platform}{_gpu(gpu)}_{arch}_instances")


class PopulatedHost:
    def __init__(self, capacity: NodeInstanceCapacity, manifest: NodeInstanceManifest):
        self.capacity = capacity
        self.manifest = manifest
        self.assigned = NodeInstanceCapacity()

    def add_node(self, persona: str, platform: str, gpu: bool, node_type: str) -> None:
        self.assigned.incr(platform, gpu, node_type)
        self.manifest.get(platform, gpu, node_type).append(persona)


def read_distribution_from_file(filename: str) -> NodeInstanceDistribution:
    """
    Purpose:
        Reads the distribution from a file of the given name
    Args:
        filename: Name of the input file
    Returns:
        AWS node instance distribution from the file
    """
    try:
        return NodeInstanceDistribution.parse_file(filename)
    except Exception as err:
        raise error_utils.RIB722(filename, str(err)) from err


def write_distribution_to_file(
    distribution: NodeInstanceDistribution, out: str
) -> None:
    """
    Purpose:
        Writes the given distribution to a file of the given name
    Args:
        distribution: AWS node instance distribution to be written
        out: Name of the output file
    Returns:
        N/A
    """
    with open(out, "w") as outfile:
        json.dump(distribution.dict(), outfile, indent=2, sort_keys=True)


def distribute_personas_to_instances(
    personas: Personas,
    topology: NodeInstanceTopology,
) -> NodeInstanceDistribution:
    """
    Purpose:
        Uses the given topology as a guide to distribute the given personas across host instances
    Args:
        personas: RACE node personas to be distributed
        topology: Node instance topology to guide the distribution
    Returns:
        Node instance distribution
    """
    distribution = NodeInstanceDistribution()
    hosts: Dict[str, List[PopulatedHost]] = {}

    for platform, gpu, arch in INSTANCE_COMBOS:
        hosts.setdefault(arch, [])
        for capacity in topology.get(platform, gpu, arch):
            manifest = NodeInstanceManifest()
            hosts[arch].append(PopulatedHost(capacity, manifest))
            distribution.get(platform, gpu, arch).append(manifest)

    # Use best-fit-descending (BFD) bin packing algorithm, using node assignment order of
    # android first, then gpu servers, gpu clients, linux servers, then lastly linux clients
    # (arch doesn't matter in the order, since you can't mix them anyway)
    for platform, gpu, arch, node_type in NODE_COMBOS:
        for persona in personas.get(platform, gpu, arch, node_type):
            best = None
            for host in hosts[arch]:
                total_capacity = host.capacity.get(platform, gpu, node_type)
                used_capacity = host.assigned.get(platform, gpu, node_type)
                if total_capacity and used_capacity < total_capacity:
                    if best is None:
                        best = host
                    elif host.assigned.total_count() < best.assigned.total_count():
                        best = host
            if not best:
                # This shouldn't be possible to hit if the topology was properly validated
                # as being compatible with the number of nodes being distributed
                raise error_utils.RIB721(f"No available hosts for {persona}")
            best.add_node(persona, platform, gpu, node_type)

    return distribution

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

""" Purpose:
    Tests for aws_topology_utils.py
"""

# Python Library Imports
import pytest
from typing import List, Union
from unittest import mock

# Local Python Library Imports
from rib.utils import aws_utils, error_utils, aws_topology_utils
from rib.utils.aws_topology_utils import (
    InstanceCounts,
    InstanceTypeNames,
    NodeCounts,
    NodeInstanceCapacity,
    NodeInstanceDistribution,
    NodeInstanceManifest,
    NodeInstanceTopology,
    NodeResourceConstraints,
    Personas,
)


###
# Fixtures
###


DEFAULT_EC2_DETAILS = {
    "c5.metal": aws_utils.Ec2InstanceTypeDetails(
        arch="x86_64",
        cpus=96,
        gpus=0,
        is_metal=True,
        name="c5.metal",
        ram_mb=48 * 1024,
    ),
    "c6g.metal": aws_utils.Ec2InstanceTypeDetails(
        arch="arm64",
        cpus=64,
        gpus=0,
        is_metal=True,
        name="c6g.metal",
        ram_mb=36 * 1024,
    ),
    "p3.2xlarge": aws_utils.Ec2InstanceTypeDetails(
        arch="x86_64",
        cpus=8,
        gpus=1,
        is_metal=False,
        name="p3.2xlarge",
        ram_mb=24 * 1024,
    ),
    "g5g.2xlarge": aws_utils.Ec2InstanceTypeDetails(
        arch="arm64",
        cpus=8,
        gpus=1,
        is_metal=False,
        name="g5g.2xlarge",
        ram_mb=16 * 1024,
    ),
    "t3a.2xlarge": aws_utils.Ec2InstanceTypeDetails(
        arch="x86_64",
        cpus=8,
        gpus=0,
        is_metal=False,
        name="t3a.2xlarge",
        ram_mb=16 * 1024,
    ),
    "t4g.xlarge": aws_utils.Ec2InstanceTypeDetails(
        arch="arm64",
        cpus=4,
        gpus=0,
        is_metal=False,
        name="t4g.xlarge",
        ram_mb=16 * 1024,
    ),
}


@pytest.fixture(autouse=True)
def mock_aws_utils():
    with mock.patch("rib.utils.aws_utils.connect_aws_session_with_profile") as _:
        with mock.patch(
            "rib.utils.aws_utils.get_ec2_instance_type_details"
        ) as get_details:
            get_details.return_value = DEFAULT_EC2_DETAILS
            yield get_details


@pytest.fixture
def instance_type_names() -> InstanceTypeNames:
    return InstanceTypeNames(
        android_x86_64_instance_type_name="c5.metal",
        android_arm64_instance_type_name="c6g.metal",
        linux_gpu_x86_64_instance_type_name="p3.2xlarge",
        linux_gpu_arm64_instance_type_name="g5g.2xlarge",
        linux_x86_64_instance_type_name="t3a.2xlarge",
        linux_arm64_instance_type_name="t4g.xlarge",
    )


@pytest.fixture
def node_resource_constraints() -> NodeResourceConstraints:
    return NodeResourceConstraints(
        ram_per_android_client=8192,
        ram_per_linux_client=4096,
        ram_per_linux_server=6144,
        ram_overcommit=0.0,
        cpus_per_android_client=1,
        cpus_per_linux_client=1,
        cpus_per_linux_server=1,
        cpu_overcommit=0.0,
        gpus_per_linux_client=0.0,
        gpus_per_linux_server=0.0,
        gpu_overcommit=0.0,
    )


###
# Testing helpers
###


def assert_topology_has_instances(
    actual: NodeInstanceTopology,
    android_arm64_instances: List[NodeInstanceCapacity] = [],
    android_x86_64_instances: List[NodeInstanceCapacity] = [],
    linux_gpu_arm64_instances: List[NodeInstanceCapacity] = [],
    linux_gpu_x86_64_instances: List[NodeInstanceCapacity] = [],
    linux_arm64_instances: List[NodeInstanceCapacity] = [],
    linux_x86_64_instances: List[NodeInstanceCapacity] = [],
):
    assert actual.android_x86_64_instances == android_x86_64_instances
    assert actual.android_arm64_instances == android_arm64_instances
    assert actual.linux_gpu_x86_64_instances == linux_gpu_x86_64_instances
    assert actual.linux_gpu_arm64_instances == linux_gpu_arm64_instances
    assert actual.linux_x86_64_instances == linux_x86_64_instances
    assert actual.linux_arm64_instances == linux_arm64_instances


def race_clients(*indices) -> List[str]:
    personas = []
    for index in indices:
        personas.append(f"race-client-{str(index).zfill(5)}")
    return personas


def race_servers(*indices) -> List[str]:
    personas = []
    for index in indices:
        personas.append(f"race-server-{str(index).zfill(5)}")
    return personas


def assert_distribution_has_manifests(
    actual: NodeInstanceDistribution,
    android_arm64_instances: List[NodeInstanceManifest] = [],
    android_x86_64_instances: List[NodeInstanceManifest] = [],
    linux_gpu_arm64_instances: List[NodeInstanceManifest] = [],
    linux_gpu_x86_64_instances: List[NodeInstanceManifest] = [],
    linux_arm64_instances: List[NodeInstanceManifest] = [],
    linux_x86_64_instances: List[NodeInstanceManifest] = [],
):
    assert actual.android_arm64_instances == android_arm64_instances
    assert actual.android_x86_64_instances == android_x86_64_instances
    assert actual.linux_gpu_arm64_instances == linux_gpu_arm64_instances
    assert actual.linux_gpu_x86_64_instances == linux_gpu_x86_64_instances
    assert actual.linux_arm64_instances == linux_arm64_instances
    assert actual.linux_x86_64_instances == linux_x86_64_instances


########################
# is_topology_compatible_with
########################


@pytest.mark.parametrize(
    "topology_instance_count,max_instance_count,expected",
    [
        (3, 3, True),
        (3, 2, False),
        (3, 4, True),
    ],
)
def test_is_topology_compatible_with_varying_instance_counts(
    topology_instance_count, max_instance_count, expected
):
    # Run test against each possible instance type
    for platform, gpu, arch in aws_topology_utils.INSTANCE_COMBOS:
        topology = NodeInstanceTopology()
        for _ in range(topology_instance_count):
            topology.get(platform, gpu, arch).append(NodeInstanceCapacity())

        max_instance_counts = InstanceCounts()
        max_instance_counts.set(platform, gpu, arch, max_instance_count)

        assert (
            aws_topology_utils.is_topology_compatible_with(
                topology, max_instance_counts, NodeCounts()
            )
            == expected
        )


@pytest.mark.parametrize(
    "topology_node_count,min_node_count,expected",
    [
        (3, 3, True),
        (3, 2, True),
        (3, 4, False),
    ],
)
def test_is_topology_compatible_with_varying_node_counts(
    topology_node_count, min_node_count, expected
):
    # Run test against each possible node type
    for platform, gpu, arch, node_type in aws_topology_utils.NODE_COMBOS:
        # Use a topology with one node per instance
        topology = NodeInstanceTopology()
        for _ in range(topology_node_count):
            capacity = NodeInstanceCapacity()
            capacity.incr(platform, gpu, node_type)
            topology.get(platform, gpu, arch).append(capacity)

        max_instance_counts = InstanceCounts()
        max_instance_counts.set(platform, gpu, arch, topology_node_count)

        min_node_counts = NodeCounts()
        min_node_counts.set(platform, gpu, arch, node_type, min_node_count)

        assert (
            aws_topology_utils.is_topology_compatible_with(
                topology, max_instance_counts, min_node_counts
            )
            == expected
        )


########################
# create_topology_from_instance_counts
########################


###
# Input validation
###


@pytest.mark.parametrize(
    "platform,gpu,arch,node_type,expected",
    [
        ("android", False, "arm64", "client", r".*no Android arm64 instances.*"),
        ("android", False, "x86_64", "client", r".*no Android x86_64 instances.*"),
        ("linux", True, "arm64", "server", r".*no Linux GPU arm64 instances.*"),
        ("linux", True, "arm64", "client", r".*no Linux GPU arm64 instances.*"),
        ("linux", True, "x86_64", "server", r".*no Linux GPU x86_64 instances.*"),
        ("linux", True, "x86_64", "client", r".*no Linux GPU x86_64 instances.*"),
        ("linux", False, "arm64", "server", r".*no Linux arm64 instances.*"),
        ("linux", False, "arm64", "client", r".*no Linux arm64 instances.*"),
        ("linux", False, "x86_64", "server", r".*no Linux x86_64 instances.*"),
        ("linux", False, "x86_64", "client", r".*no Linux x86_64 instances.*"),
    ],
)
def test_create_topology_from_instance_counts_rejects_missing_required_instance_types(
    platform, gpu, arch, node_type, expected
):
    instance_counts = InstanceCounts()
    node_counts = NodeCounts()
    node_counts.set(platform, gpu, arch, node_type, 1)
    with pytest.raises(error_utils.RIB721, match=expected):
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        )


@pytest.mark.parametrize(
    "gpu,arch,expected",
    [
        (True, "arm64", r".*only one Linux GPU arm64 instance.*"),
        (True, "x86_64", r".*only one Linux GPU x86_64 instance.*"),
        (False, "arm64", r".*only one Linux arm64 instance.*"),
        (False, "x86_64", r".*only one Linux x86_64 instance.*"),
    ],
)
def test_create_topology_from_instance_counts_rejects_missing_required_multiple_instance_types(
    gpu, arch, expected
):
    instance_counts = InstanceCounts()
    instance_counts.set("linux", gpu, arch, 1)
    node_counts = NodeCounts()
    node_counts.set("linux", gpu, arch, "client", 1)
    node_counts.set("linux", gpu, arch, "server", 1)
    with pytest.raises(error_utils.RIB721, match=expected):
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        )


###
# Android ARM clients
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [2, 2, 1]),
        (3, 7, [3, 2, 2]),
        (3, 8, [3, 3, 2]),
    ],
)
def test_create_topology_from_instance_counts_with_android_arm64_clients(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.android_arm64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.android_arm64_clients = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


###
# Android x86 clients
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [2, 2, 1]),
        (3, 7, [3, 2, 2]),
        (3, 8, [3, 3, 2]),
    ],
)
def test_create_topology_from_instance_counts_with_android_x86_64_clients(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.android_x86_64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.android_x86_64_clients = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


###
# Linux ARM clients
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [2, 2, 1]),
        (3, 7, [3, 2, 2]),
        (3, 8, [3, 3, 2]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_arm64_clients(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_arm64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_arm64_clients = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


###
# linux x86 clients
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [2, 2, 1]),
        (3, 7, [3, 2, 2]),
        (3, 8, [3, 3, 2]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_x86_64_clients(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_x86_64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_x86_64_clients = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


###
# Linux GPU ARM clients
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [2, 2, 1]),
        (3, 7, [3, 2, 2]),
        (3, 8, [3, 3, 2]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_gpu_arm64_clients(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_gpu_arm64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_gpu_arm64_clients = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


###
# Linux GPU x86 clients
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [2, 2, 1]),
        (3, 7, [3, 2, 2]),
        (3, 8, [3, 3, 2]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_gpu_x86_64_clients(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_gpu_x86_64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_gpu_x86_64_clients = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


###
# Linux ARM servers
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [1, 2, 2]),
        (3, 7, [2, 2, 3]),
        (3, 8, [2, 3, 3]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_arm64_servers(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_arm64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_arm64_servers = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


###
# linux x86 servers
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [1, 2, 2]),
        (3, 7, [2, 2, 3]),
        (3, 8, [2, 3, 3]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_x86_64_servers(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_x86_64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_x86_64_servers = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


###
# Linux GPU ARM servers
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [1, 2, 2]),
        (3, 7, [2, 2, 3]),
        (3, 8, [2, 3, 3]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_gpu_arm64_servers(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_gpu_arm64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_gpu_arm64_servers = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


###
# Linux GPU x86 servers
###


@pytest.mark.parametrize(
    "instance_count,node_count,expected",
    [
        (2, 2, [1, 1]),
        (2, 6, [3, 3]),
        (3, 6, [2, 2, 2]),
        (3, 5, [1, 2, 2]),
        (3, 7, [2, 2, 3]),
        (3, 8, [2, 3, 3]),
    ],
)
def test_create_topology_from_instance_counts_with_linux_gpu_x86_64_servers(
    instance_count, node_count, expected
):
    instance_counts = InstanceCounts()
    instance_counts.linux_gpu_x86_64_instances = instance_count
    node_counts = NodeCounts()
    node_counts.linux_gpu_x86_64_servers = node_count
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=instance_counts,
            node_counts=node_counts,
            colocate_clients_and_servers=False,
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


###
# Mixed ARM
###


def test_create_topology_from_instance_counts_with_arm64_nodes_and_no_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=InstanceCounts(
                android_arm64_instances=2,
                linux_gpu_arm64_instances=3,
                linux_arm64_instances=3,
            ),
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_gpu_arm64_clients=1,
                linux_gpu_arm64_servers=10,
                linux_arm64_clients=4,
                linux_arm64_servers=4,
            ),
            colocate_clients_and_servers=False,
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=5),
            NodeInstanceCapacity(linux_gpu_server_count=5),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
        ],
    )


def test_create_topology_from_instance_counts_with_arm64_nodes_and_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=InstanceCounts(
                android_arm64_instances=2,
                linux_gpu_arm64_instances=3,
                linux_arm64_instances=3,
            ),
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_gpu_arm64_clients=1,
                linux_gpu_arm64_servers=10,
                linux_arm64_clients=4,
                linux_arm64_servers=4,
            ),
            colocate_clients_and_servers=True,
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1, linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=4),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=2),
        ],
    )


###
# Mixed x86
###


def test_create_topology_from_instance_counts_with_x86_64_nodes_and_no_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=InstanceCounts(
                android_x86_64_instances=2,
                linux_gpu_x86_64_instances=3,
                linux_x86_64_instances=3,
            ),
            node_counts=NodeCounts(
                android_x86_64_clients=5,
                linux_gpu_x86_64_clients=1,
                linux_gpu_x86_64_servers=10,
                linux_x86_64_clients=4,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=False,
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=5),
            NodeInstanceCapacity(linux_gpu_server_count=5),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
        ],
    )


def test_create_topology_from_instance_counts_with_x86_64_nodes_and_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=InstanceCounts(
                android_x86_64_instances=2,
                linux_gpu_x86_64_instances=3,
                linux_x86_64_instances=3,
            ),
            node_counts=NodeCounts(
                android_x86_64_clients=5,
                linux_gpu_x86_64_clients=1,
                linux_gpu_x86_64_servers=10,
                linux_x86_64_clients=4,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=True,
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1, linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=4),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=2),
        ],
    )


###
# Mixed architectures
###


def test_create_topology_from_instance_counts_with_mixed_arch_and_no_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=InstanceCounts(
                android_arm64_instances=2,
                android_x86_64_instances=2,
                linux_gpu_arm64_instances=3,
                linux_gpu_x86_64_instances=3,
                linux_arm64_instances=3,
                linux_x86_64_instances=3,
            ),
            node_counts=NodeCounts(
                android_arm64_clients=5,
                android_x86_64_clients=5,
                linux_gpu_arm64_clients=1,
                linux_gpu_x86_64_clients=1,
                linux_gpu_arm64_servers=10,
                linux_gpu_x86_64_servers=10,
                linux_arm64_clients=4,
                linux_x86_64_clients=4,
                linux_arm64_servers=4,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=False,
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=5),
            NodeInstanceCapacity(linux_gpu_server_count=5),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=5),
            NodeInstanceCapacity(linux_gpu_server_count=5),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
        ],
    )


def test_create_topology_from_instance_counts_with_mixed_arch_and_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_instance_counts(
            instance_counts=InstanceCounts(
                android_arm64_instances=2,
                android_x86_64_instances=2,
                linux_gpu_arm64_instances=3,
                linux_gpu_x86_64_instances=3,
                linux_arm64_instances=3,
                linux_x86_64_instances=3,
            ),
            node_counts=NodeCounts(
                android_arm64_clients=5,
                android_x86_64_clients=5,
                linux_gpu_arm64_clients=1,
                linux_gpu_x86_64_clients=1,
                linux_gpu_arm64_servers=10,
                linux_gpu_x86_64_servers=10,
                linux_arm64_clients=4,
                linux_x86_64_clients=4,
                linux_arm64_servers=4,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=True,
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1, linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=4),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1, linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=4),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=1, linux_server_count=2),
        ],
    )


########################
# create_topology_from_nodes_per_instance
########################


###
# Input validation
###


def test_create_topology_from_nodes_per_instance_rejects_no_count_provided():
    with pytest.raises(
        error_utils.RIB721, match=r".*Neither node counts nor instance counts"
    ):
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(),
            colocate_clients_and_servers=False,
        )


def test_create_topology_from_nodes_per_instance_rejects_both_counts_provided():
    with pytest.raises(
        error_utils.RIB721, match=r".*Both node counts and instance counts"
    ):
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(),
            colocate_clients_and_servers=False,
            instance_counts=InstanceCounts(),
            node_counts=NodeCounts(),
        )


def test_create_topology_from_nodes_per_instance_rejects_instance_counts_with_colocation():
    with pytest.raises(error_utils.RIB721, match=r".*non-colocated nodes-per-instance"):
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(),
            colocate_clients_and_servers=False,
            instance_counts=InstanceCounts(),
        )


###
# Android ARM clients
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_android_arm64_clients_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                android_arm64_instances=instance_count,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [2, 1]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_android_arm64_clients_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                android_arm64_clients=node_count,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


###
# Android x86 clients
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_android_x86_64_clients_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_x86_64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                android_x86_64_instances=instance_count,
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [2, 1]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_android_x86_64_clients_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_x86_64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                android_x86_64_clients=node_count,
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


###
# Linux ARM clients
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_arm64_clients_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_arm64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_arm64_instances=instance_count,
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [2, 1]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_arm64_clients_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_arm64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_arm64_clients=node_count,
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


###
# Linux x86 clients
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_x86_64_clients_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_x86_64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_x86_64_instances=instance_count,
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [2, 1]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_x86_64_clients_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_x86_64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_x86_64_clients=node_count,
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


###
# GPU ARM clients
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_arm64_clients_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_arm64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_gpu_arm64_instances=instance_count,
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [2, 1]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_arm64_clients_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_arm64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_gpu_arm64_clients=node_count,
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


###
# GPU x86 clients
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_x86_64_clients_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_x86_64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_gpu_x86_64_instances=instance_count,
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [2, 1]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_x86_64_clients_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_x86_64_clients=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_gpu_x86_64_clients=node_count,
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


###
# Linux ARM servers
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_arm64_servers_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_arm64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_arm64_instances=instance_count,
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [1, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_arm64_servers_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_arm64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_arm64_servers=node_count,
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


###
# Linux x86 servers
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_x86_64_servers_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_x86_64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_x86_64_instances=instance_count,
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [1, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_x86_64_servers_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_x86_64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_x86_64_servers=node_count,
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


###
# GPU ARM servers
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_arm64_servers_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_arm64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_gpu_arm64_instances=instance_count,
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [1, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_arm64_servers_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_arm64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_gpu_arm64_servers=node_count,
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


###
# GPU x86 servers
###


@pytest.mark.parametrize(
    "nodes_per_instance,instance_count,expected",
    [
        (3, 2, [3, 3]),
        (2, 3, [2, 2, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_x86_64_servers_and_instance_count(
    nodes_per_instance, instance_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_x86_64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                linux_gpu_x86_64_instances=instance_count,
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


@pytest.mark.parametrize(
    "nodes_per_instance,node_count,expected",
    [
        (3, 6, [3, 3]),
        (2, 3, [1, 2]),
    ],
)
def test_create_topology_from_nodes_per_instance_with_linux_gpu_x86_64_servers_and_node_count(
    nodes_per_instance, node_count, expected
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                linux_gpu_x86_64_servers=nodes_per_instance,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                linux_gpu_x86_64_servers=node_count,
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


###
# Mixed ARM
###


def test_create_topology_from_nodes_per_instance_with_arm64_nodes_and_instance_count():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=3,
                linux_gpu_arm64_clients=3,
                linux_gpu_arm64_servers=2,
                linux_arm64_clients=3,
                linux_arm64_servers=4,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                android_arm64_instances=3,
                linux_gpu_arm64_instances=3,
                linux_arm64_instances=3,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
        ],
    )


def test_create_topology_from_nodes_per_instance_with_arm64_nodes_and_node_count_with_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=3,
                linux_gpu_arm64_clients=3,
                linux_gpu_arm64_servers=2,
                linux_arm64_clients=3,
                linux_arm64_servers=4,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                android_arm64_clients=8,
                linux_gpu_arm64_clients=6,
                linux_gpu_arm64_servers=5,
                linux_arm64_clients=7,
                linux_arm64_servers=3,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
        ],
    )


def test_create_topology_from_nodes_per_instance_with_arm64_nodes_and_node_count_with_no_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=3,
                linux_gpu_arm64_clients=3,
                linux_gpu_arm64_servers=2,
                linux_arm64_clients=3,
                linux_arm64_servers=4,
            ),
            colocate_clients_and_servers=False,
            node_counts=NodeCounts(
                android_arm64_clients=8,
                linux_gpu_arm64_clients=6,
                linux_gpu_arm64_servers=5,
                linux_arm64_clients=7,
                linux_arm64_servers=3,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
        ],
        # This does not produce the expected 3 client instances and 1 server instance because
        # of the way the ratio of client instances to server instances is calculated. This may
        # be acceptable for now because the user can manually modify the resulting topology.
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_server_count=2),
        ],
    )


###
# Mixed x86
###


def test_create_topology_from_nodes_per_instance_with_x86_64_nodes_and_instance_count():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_x86_64_clients=3,
                linux_gpu_x86_64_clients=3,
                linux_gpu_x86_64_servers=2,
                linux_x86_64_clients=3,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                android_x86_64_instances=3,
                linux_gpu_x86_64_instances=3,
                linux_x86_64_instances=3,
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
        ],
    )


def test_create_topology_from_nodes_per_instance_with_x86_64_nodes_and_node_count_with_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_x86_64_clients=3,
                linux_gpu_x86_64_clients=3,
                linux_gpu_x86_64_servers=2,
                linux_x86_64_clients=3,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                android_x86_64_clients=8,
                linux_gpu_x86_64_clients=6,
                linux_gpu_x86_64_servers=5,
                linux_x86_64_clients=7,
                linux_x86_64_servers=3,
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
        ],
    )


def test_create_topology_from_nodes_per_instance_with_x86_64_nodes_and_node_count_with_no_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_x86_64_clients=3,
                linux_gpu_x86_64_clients=3,
                linux_gpu_x86_64_servers=2,
                linux_x86_64_clients=3,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=False,
            node_counts=NodeCounts(
                android_x86_64_clients=8,
                linux_gpu_x86_64_clients=6,
                linux_gpu_x86_64_servers=5,
                linux_x86_64_clients=7,
                linux_x86_64_servers=3,
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
        ],
        # This does not produce the expected 3 client instances and 1 server instance because
        # of the way the ratio of client instances to server instances is calculated. This may
        # be acceptable for now because the user can manually modify the resulting topology.
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_server_count=2),
        ],
    )


###
# Mixed architecture
###


def test_create_topology_from_nodes_per_instance_with_mixed_arch_and_instance_count():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=3,
                linux_gpu_arm64_clients=3,
                linux_gpu_arm64_servers=2,
                linux_arm64_clients=3,
                linux_arm64_servers=4,
                android_x86_64_clients=3,
                linux_gpu_x86_64_clients=3,
                linux_gpu_x86_64_servers=2,
                linux_x86_64_clients=3,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=True,
            instance_counts=InstanceCounts(
                android_arm64_instances=3,
                linux_gpu_arm64_instances=3,
                linux_arm64_instances=3,
                android_x86_64_instances=3,
                linux_gpu_x86_64_instances=3,
                linux_x86_64_instances=3,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3, linux_gpu_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=4),
        ],
    )


def test_create_topology_from_nodes_per_instance_with_mixed_arch_and_node_count_with_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=3,
                linux_gpu_arm64_clients=3,
                linux_gpu_arm64_servers=2,
                linux_arm64_clients=3,
                linux_arm64_servers=4,
                android_x86_64_clients=3,
                linux_gpu_x86_64_clients=3,
                linux_gpu_x86_64_servers=2,
                linux_x86_64_clients=3,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=True,
            node_counts=NodeCounts(
                android_arm64_clients=8,
                linux_gpu_arm64_clients=6,
                linux_gpu_arm64_servers=5,
                linux_arm64_clients=7,
                linux_arm64_servers=3,
                android_x86_64_clients=8,
                linux_gpu_x86_64_clients=6,
                linux_gpu_x86_64_servers=5,
                linux_x86_64_clients=7,
                linux_x86_64_servers=3,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_gpu_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=3, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=2, linux_server_count=1),
        ],
    )


def test_create_topology_from_nodes_per_instance_with_mixed_arch_and_node_count_with_no_colocation():
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_nodes_per_instance(
            nodes_per_instance=NodeCounts(
                android_arm64_clients=3,
                linux_gpu_arm64_clients=3,
                linux_gpu_arm64_servers=2,
                linux_arm64_clients=3,
                linux_arm64_servers=4,
                android_x86_64_clients=3,
                linux_gpu_x86_64_clients=3,
                linux_gpu_x86_64_servers=2,
                linux_x86_64_clients=3,
                linux_x86_64_servers=4,
            ),
            colocate_clients_and_servers=False,
            node_counts=NodeCounts(
                android_arm64_clients=8,
                linux_gpu_arm64_clients=6,
                linux_gpu_arm64_servers=5,
                linux_arm64_clients=7,
                linux_arm64_servers=3,
                android_x86_64_clients=8,
                linux_gpu_x86_64_clients=6,
                linux_gpu_x86_64_servers=5,
                linux_x86_64_clients=7,
                linux_x86_64_servers=3,
            ),
        ),
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_server_count=2),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=3),
            NodeInstanceCapacity(android_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=4),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_server_count=2),
        ],
    )


########################
# create_topology_from_node_resource_requirements tests
########################


###
# Input validation
###


@pytest.mark.parametrize(
    "platform,gpu,arch,name,expected",
    [
        ("android", False, "arm64", "t4g.xlarge", r".*Must be a metal instance.*"),
        ("android", False, "x86_64", "t3a.2xlarge", r".*Must be a metal instance.*"),
        ("android", False, "arm64", "c5.metal", r".*Must be a Graviton.*"),
        ("android", False, "x86_64", "c6g.metal", r".*Cannot be a Graviton.*"),
        (
            "linux",
            True,
            "arm64",
            "t4g.xlarge",
            r".*Must be an instance type with GPUs.*",
        ),
        (
            "linux",
            True,
            "x86_64",
            "t3a.2xlarge",
            r".*Must be an instance type with GPUs.*",
        ),
        ("linux", True, "arm64", "p3.2xlarge", r".*Must be a Graviton.*"),
        ("linux", True, "x86_64", "g5g.2xlarge", r".*Cannot be a Graviton.*"),
        ("linux", True, "arm64", "t3a.2xlarge", r".*Must be a Graviton.*"),
        ("linux", True, "x86_64", "t4g.xlarge", r".*Cannot be a Graviton.*"),
    ],
)
def test_create_topology_from_node_resource_requirements_rejects_invalid_instance_types(
    platform, gpu, arch, name, expected, instance_type_names, node_resource_constraints
):
    instance_type_names.set(platform, gpu, arch, name)
    with pytest.raises(error_utils.RIB719, match=expected):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(),
        )


###
# Android ARM clients
###


@pytest.mark.parametrize(
    "ram_per_client,ram_overcommit,cpus_per_client,cpu_overcommit,expected",
    [
        (8192, 0.0, 1, 0.0, [4, 1]),  # base
        (8192, 0.5, 1, 0.0, [5]),  # RAM overcommit
        (8192, 0.0, 30, 0.0, [2, 2, 1]),  # CPU constraints
        (8192, 0.0, 30, 0.5, [3, 2]),  # CPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_android_arm64_clients(
    ram_per_client,
    ram_overcommit,
    cpus_per_client,
    cpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_android_client = ram_per_client
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_android_client = cpus_per_client
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(android_arm64_clients=5),
        ).instance_topology,
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


###
# Android x86 clients
###


@pytest.mark.parametrize(
    "ram_per_client,ram_overcommit,cpus_per_client,cpu_overcommit,expected",
    [
        (8192, 0.0, 1, 0.0, [5]),  # base
        (12288, 0.0, 1, 0.0, [3, 2]),  # Add'l RAM constraints
        (12288, 0.5, 1, 0.0, [5]),  # RAM overcommit
        (8192, 0.0, 30, 0.0, [3, 2]),  # CPU constraints
        (8192, 0.0, 30, 0.5, [5]),  # CPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_android_x86_64_clients(
    ram_per_client,
    ram_overcommit,
    cpus_per_client,
    cpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_android_client = ram_per_client
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_android_client = cpus_per_client
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(android_x86_64_clients=5),
        ).instance_topology,
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=x) for x in expected
        ],
    )


###
# Linux ARM clients
###


@pytest.mark.parametrize(
    "ram_per_client,ram_overcommit,cpus_per_client,cpu_overcommit,expected",
    [
        (4096, 0.0, 1, 0.0, [3, 2]),  # base
        (4096, 0.5, 1, 0.0, [4, 1]),  # RAM overcommit
        (4096, 0.0, 2, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 2, 0.5, [3, 2]),  # CPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_arm64_clients(
    ram_per_client,
    ram_overcommit,
    cpus_per_client,
    cpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_client = ram_per_client
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_client = cpus_per_client
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_arm64_clients=5),
        ).instance_topology,
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


###
# Linux x86 clients
###


@pytest.mark.parametrize(
    "ram_per_client,ram_overcommit,cpus_per_client,cpu_overcommit,expected",
    [
        (4096, 0.0, 1, 0.0, [3, 2]),  # base
        (4096, 0.5, 1, 0.0, [5]),  # RAM overcommit
        (4096, 0.0, 3, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 3, 0.5, [3, 2]),  # CPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_x86_64_clients(
    ram_per_client,
    ram_overcommit,
    cpus_per_client,
    cpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_client = ram_per_client
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_client = cpus_per_client
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_x86_64_clients=5),
        ).instance_topology,
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=x) for x in expected
        ],
    )


###
# GPU ARM clients
###


@pytest.mark.parametrize(
    "ram_per_client,ram_overcommit,cpus_per_client,cpu_overcommit,gpus_per_client,gpu_overcommit,expected",
    [
        (4096, 0.0, 1, 0.0, 0.0, 0.0, [3, 2]),  # base
        (8192, 0.5, 1, 0.0, 0.0, 0.0, [2, 2, 1]),  # RAM overcommit
        (4096, 0.0, 3, 0.0, 0.0, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 3, 0.5, 0.0, 0.0, [3, 2]),  # CPU overcommit
        (4096, 0.0, 1, 0.0, 0.5, 0.0, [2, 2, 1]),  # GPU constraints
        (4096, 0.0, 1, 0.0, 0.5, 0.5, [3, 2]),  # GPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_gpu_arm64_clients(
    ram_per_client,
    ram_overcommit,
    cpus_per_client,
    cpu_overcommit,
    gpus_per_client,
    gpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_client = ram_per_client
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_client = cpus_per_client
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    node_resource_constraints.gpus_per_linux_client = gpus_per_client
    node_resource_constraints.gpu_overcommit = gpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_gpu_arm64_clients=5),
        ).instance_topology,
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


###
# GPU x86 clients
###


@pytest.mark.parametrize(
    "ram_per_client,ram_overcommit,cpus_per_client,cpu_overcommit,gpus_per_client,gpu_overcommit,expected",
    [
        (4096, 0.0, 1, 0.0, 0.0, 0.0, [5]),  # base
        (8192, 0.0, 1, 0.0, 0.0, 0.0, [2, 2, 1]),  # Add'l RAM constraints
        (8192, 0.5, 1, 0.0, 0.0, 0.0, [4, 1]),  # RAM overcommit
        (4096, 0.0, 3, 0.0, 0.0, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 3, 0.5, 0.0, 0.0, [4, 1]),  # CPU overcommit
        (4096, 0.0, 1, 0.0, 0.5, 0.0, [2, 2, 1]),  # GPU constraints
        (4096, 0.0, 1, 0.0, 0.5, 0.5, [3, 2]),  # GPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_gpu_x86_64_clients(
    ram_per_client,
    ram_overcommit,
    cpus_per_client,
    cpu_overcommit,
    gpus_per_client,
    gpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_client = ram_per_client
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_client = cpus_per_client
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    node_resource_constraints.gpus_per_linux_client = gpus_per_client
    node_resource_constraints.gpu_overcommit = gpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_gpu_x86_64_clients=5),
        ).instance_topology,
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=x) for x in expected
        ],
    )


###
# Linux ARM servers
###


@pytest.mark.parametrize(
    "ram_per_server,ram_overcommit,cpus_per_server,cpu_overcommit,expected",
    [
        (6144, 0.0, 1, 0.0, [2, 2, 1]),  # base
        (6144, 0.5, 1, 0.0, [4, 1]),  # RAM overcommit
        (4096, 0.0, 2, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 2, 0.5, [3, 2]),  # CPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_arm64_servers(
    ram_per_server,
    ram_overcommit,
    cpus_per_server,
    cpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_server = ram_per_server
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_server = cpus_per_server
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_arm64_servers=5),
        ).instance_topology,
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


###
# Linux x86 servers
###


@pytest.mark.parametrize(
    "ram_per_server,ram_overcommit,cpus_per_server,cpu_overcommit,expected",
    [
        (6144, 0.0, 1, 0.0, [2, 2, 1]),  # base
        (6144, 0.5, 1, 0.0, [4, 1]),  # RAM overcommit
        (4096, 0.0, 3, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 3, 0.5, [3, 2]),  # CPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_x86_64_servers(
    ram_per_server,
    ram_overcommit,
    cpus_per_server,
    cpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_server = ram_per_server
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_server = cpus_per_server
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_x86_64_servers=5),
        ).instance_topology,
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=x) for x in expected
        ],
    )


###
# GPU ARM servers
###


@pytest.mark.parametrize(
    "ram_per_server,ram_overcommit,cpus_per_server,cpu_overcommit,gpus_per_server,gpu_overcommit,expected",
    [
        (6144, 0.0, 1, 0.0, 0.0, 0.0, [2, 2, 1]),  # base
        (8192, 0.0, 1, 0.0, 0.0, 0.0, [1, 1, 1, 1, 1]),  # Add'l RAM overcommit
        (8192, 0.5, 1, 0.0, 0.0, 0.0, [2, 2, 1]),  # RAM overcommit
        (4096, 0.0, 3, 0.0, 0.0, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 3, 0.5, 0.0, 0.0, [3, 2]),  # CPU overcommit
        (4096, 0.0, 1, 0.0, 0.5, 0.0, [2, 2, 1]),  # GPU constraints
        (4096, 0.0, 1, 0.0, 0.5, 0.5, [3, 2]),  # GPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_gpu_arm64_servers(
    ram_per_server,
    ram_overcommit,
    cpus_per_server,
    cpu_overcommit,
    gpus_per_server,
    gpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_server = ram_per_server
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_server = cpus_per_server
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    node_resource_constraints.gpus_per_linux_server = gpus_per_server
    node_resource_constraints.gpu_overcommit = gpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_gpu_arm64_servers=5),
        ).instance_topology,
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


###
# GPU x86 servers
###


@pytest.mark.parametrize(
    "ram_per_server,ram_overcommit,cpus_per_server,cpu_overcommit,gpus_per_server,gpu_overcommit,expected",
    [
        (6144, 0.0, 1, 0.0, 0.0, 0.0, [3, 2]),  # base
        (8192, 0.0, 1, 0.0, 0.0, 0.0, [2, 2, 1]),  # Add'l RAM overcommit
        (8192, 0.5, 1, 0.0, 0.0, 0.0, [4, 1]),  # RAM overcommit
        (4096, 0.0, 3, 0.0, 0.0, 0.0, [2, 2, 1]),  # CPU constraints
        (4096, 0.0, 3, 0.5, 0.0, 0.0, [4, 1]),  # CPU overcommit
        (4096, 0.0, 1, 0.0, 0.5, 0.0, [2, 2, 1]),  # GPU constraints
        (4096, 0.0, 1, 0.0, 0.5, 0.5, [3, 2]),  # GPU overcommit
    ],
)
def test_create_topology_from_node_resource_requirements_with_linux_gpu_x86_64_servers(
    ram_per_server,
    ram_overcommit,
    cpus_per_server,
    cpu_overcommit,
    gpus_per_server,
    gpu_overcommit,
    expected,
    instance_type_names,
    node_resource_constraints,
):
    node_resource_constraints.ram_per_linux_server = ram_per_server
    node_resource_constraints.ram_overcommit = ram_overcommit
    node_resource_constraints.cpus_per_linux_server = cpus_per_server
    node_resource_constraints.cpu_overcommit = cpu_overcommit
    node_resource_constraints.gpus_per_linux_server = gpus_per_server
    node_resource_constraints.gpu_overcommit = gpu_overcommit
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(linux_gpu_x86_64_servers=5),
        ).instance_topology,
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=x) for x in expected
        ],
    )


###
# Mixed ARM
###


def test_create_topology_from_node_resource_requirements_with_arm64_nodes_and_no_colocation(
    instance_type_names, node_resource_constraints
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_arm64_clients=5,
                linux_gpu_arm64_clients=5,
                linux_arm64_servers=5,
                linux_gpu_arm64_servers=5,
            ),
        ).instance_topology,
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=4),
            NodeInstanceCapacity(android_client_count=1),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_client_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_client_count=2),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_arm64_nodes_and_colocation(
    instance_type_names, node_resource_constraints
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=True,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_arm64_clients=5,
                linux_gpu_arm64_clients=5,
                linux_arm64_servers=5,
                linux_gpu_arm64_servers=5,
            ),
        ).instance_topology,
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=4),
            NodeInstanceCapacity(android_client_count=1, linux_server_count=4),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=1, linux_gpu_client_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=1, linux_client_count=2),
            NodeInstanceCapacity(linux_client_count=3),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_arm64_nodes_and_colocation_and_ram_overcommit(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.ram_overcommit = 0.1
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=True,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_arm64_clients=5,
                linux_gpu_arm64_clients=5,
                linux_arm64_servers=5,
                linux_gpu_arm64_servers=5,
            ),
        ).instance_topology,
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=4, linux_server_count=1),
            NodeInstanceCapacity(
                android_client_count=1, linux_server_count=4, linux_client_count=1
            ),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=2, linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2, linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=1, linux_gpu_client_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=1, linux_client_count=3),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=1),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_arm64_insufficient_android_resources(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.ram_per_android_client = 64 * 1024
    with pytest.raises(error_utils.RIB721, match=r".*incapable of hosting.*"):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_arm64_clients=5,
            ),
        )


def test_create_topology_from_node_resource_requirements_with_arm64_insufficient_gpu_resources(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.gpus_per_linux_client = 2
    with pytest.raises(error_utils.RIB721, match=r".*incapable of hosting.*"):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                linux_gpu_arm64_clients=5,
            ),
        )


def test_create_topology_from_node_resource_requirements_with_arm64_insufficient_linux_resources(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.cpus_per_linux_client = 12
    with pytest.raises(error_utils.RIB721, match=r".*incapable of hosting.*"):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                linux_arm64_clients=5,
            ),
        )


###
# Mixed x86
###


def test_create_topology_from_node_resource_requirements_with_x86_nodes_and_no_colocation(
    instance_type_names, node_resource_constraints
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_x86_64_clients=5,
                linux_x86_64_clients=5,
                linux_gpu_x86_64_clients=5,
                linux_x86_64_servers=5,
                linux_gpu_x86_64_servers=5,
            ),
        ).instance_topology,
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=5),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=5),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_client_count=2),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_x86_nodes_and_colocation(
    instance_type_names, node_resource_constraints
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=True,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_x86_64_clients=5,
                linux_x86_64_clients=5,
                linux_gpu_x86_64_clients=5,
                linux_x86_64_servers=5,
                linux_gpu_x86_64_servers=5,
            ),
        ).instance_topology,
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=5, linux_server_count=1),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=3, linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2, linux_gpu_client_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_server_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_client_count=2),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_x86_nodes_and_colocation_and_ram_overcommit(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.ram_overcommit = 0.1
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=True,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_x86_64_clients=5,
                linux_x86_64_clients=5,
                linux_gpu_x86_64_clients=5,
                linux_x86_64_servers=5,
                linux_gpu_x86_64_servers=5,
            ),
        ).instance_topology,
        android_x86_64_instances=[
            NodeInstanceCapacity(
                android_client_count=5, linux_server_count=1, linux_client_count=1
            ),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=4),
            NodeInstanceCapacity(linux_gpu_server_count=1, linux_gpu_client_count=4),
            NodeInstanceCapacity(linux_gpu_client_count=1, linux_server_count=3),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=1, linux_client_count=2),
            NodeInstanceCapacity(linux_client_count=2),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_x86_64_and_insufficient_android_resources(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.ram_per_android_client = 64 * 1024
    with pytest.raises(error_utils.RIB721, match=r".*incapable of hosting.*"):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_x86_64_clients=5,
            ),
        )


def test_create_topology_from_node_resource_requirements_with_x86_64_and_insufficient_gpu_resources(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.gpus_per_linux_client = 2
    with pytest.raises(error_utils.RIB721, match=r".*incapable of hosting.*"):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                linux_gpu_x86_64_clients=5,
            ),
        )


def test_create_topology_from_node_resource_requirements_with_x86_64_and_insufficient_linux_resources(
    instance_type_names, node_resource_constraints
):
    node_resource_constraints.cpus_per_linux_client = 12
    with pytest.raises(error_utils.RIB721, match=r".*incapable of hosting.*"):
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                linux_x86_64_clients=5,
            ),
        )


###
# Mixed architectures
###


def test_create_topology_from_node_resource_requirements_with_mixed_arch_and_no_colocation(
    instance_type_names, node_resource_constraints
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=False,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_arm64_clients=5,
                linux_gpu_arm64_clients=5,
                linux_arm64_servers=5,
                linux_gpu_arm64_servers=5,
                android_x86_64_clients=5,
                linux_x86_64_clients=5,
                linux_gpu_x86_64_clients=5,
                linux_x86_64_servers=5,
                linux_gpu_x86_64_servers=5,
            ),
        ).instance_topology,
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=4),
            NodeInstanceCapacity(android_client_count=1),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=5),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=1),
            NodeInstanceCapacity(linux_gpu_client_count=3),
            NodeInstanceCapacity(linux_gpu_client_count=2),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=3),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=5),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_client_count=2),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_server_count=1),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_client_count=2),
        ],
    )


def test_create_topology_from_node_resource_requirements_with_mixed_arch_and_colocation(
    instance_type_names, node_resource_constraints
):
    assert_topology_has_instances(
        aws_topology_utils.create_topology_from_node_resource_requirements(
            allow_colocation=True,
            instance_type_names=instance_type_names,
            node_resource_constraints=node_resource_constraints,
            node_counts=NodeCounts(
                android_arm64_clients=5,
                linux_arm64_clients=5,
                linux_gpu_arm64_clients=5,
                linux_arm64_servers=5,
                linux_gpu_arm64_servers=5,
                android_x86_64_clients=5,
                linux_x86_64_clients=5,
                linux_gpu_x86_64_clients=5,
                linux_x86_64_servers=5,
                linux_gpu_x86_64_servers=5,
            ),
        ).instance_topology,
        android_arm64_instances=[
            NodeInstanceCapacity(android_client_count=4),
            NodeInstanceCapacity(android_client_count=1, linux_server_count=4),
        ],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=5, linux_server_count=1),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=2),
            NodeInstanceCapacity(linux_gpu_server_count=1, linux_gpu_client_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=3),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_server_count=3, linux_gpu_client_count=1),
            NodeInstanceCapacity(linux_gpu_server_count=2, linux_gpu_client_count=2),
            NodeInstanceCapacity(linux_gpu_client_count=2, linux_server_count=2),
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_server_count=1, linux_client_count=2),
            NodeInstanceCapacity(linux_client_count=3),
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_server_count=2),
            NodeInstanceCapacity(linux_client_count=3),
            NodeInstanceCapacity(linux_client_count=2),
        ],
    )


########################
# distribute_personas_to_instances
########################


###
# Android ARM clients
###


def test_distribute_personas_to_instances_with_android_arm64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_android_arm64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                android_arm64_instances=[NodeInstanceCapacity(android_client_count=3)],
            ),
        )


def test_distribute_personas_to_instances_with_android_arm64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                android_arm64_instances=[
                    NodeInstanceCapacity(android_client_count=3),
                    NodeInstanceCapacity(android_client_count=3),
                ],
            ),
        ),
        android_arm64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(android_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_android_arm64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                android_arm64_instances=[
                    NodeInstanceCapacity(android_client_count=2),
                    NodeInstanceCapacity(android_client_count=4),
                ],
            ),
        ),
        android_arm64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3)),
            NodeInstanceManifest(android_clients=race_clients(2, 4, 5)),
        ],
    )


###
# Android x86 clients
###


def test_distribute_personas_to_instances_with_android_x86_64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_android_x86_64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                android_x86_64_instances=[NodeInstanceCapacity(android_client_count=3)],
            ),
        )


def test_distribute_personas_to_instances_with_android_x86_64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                android_x86_64_instances=[
                    NodeInstanceCapacity(android_client_count=3),
                    NodeInstanceCapacity(android_client_count=3),
                ],
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(android_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_android_x86_64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                android_x86_64_instances=[
                    NodeInstanceCapacity(android_client_count=2),
                    NodeInstanceCapacity(android_client_count=4),
                ],
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3)),
            NodeInstanceManifest(android_clients=race_clients(2, 4, 5)),
        ],
    )


###
# GPU ARM clients
###


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3)
                ],
            ),
        )


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                ],
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=2),
                    NodeInstanceCapacity(linux_gpu_client_count=4),
                ],
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4, 5)),
        ],
    )


###
# GPU x86 clients
###


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3)
                ],
            ),
        )


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                ],
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=2),
                    NodeInstanceCapacity(linux_gpu_client_count=4),
                ],
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4, 5)),
        ],
    )


###
# Linux ARM clients
###


def test_distribute_personas_to_instances_with_linux_arm64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_arm64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_arm64_instances=[NodeInstanceCapacity(client_count=3)],
            ),
        )


def test_distribute_personas_to_instances_with_linux_arm64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_arm64_instances=[
                    NodeInstanceCapacity(linux_client_count=3),
                    NodeInstanceCapacity(linux_client_count=3),
                ],
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_arm64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_arm64_instances=[
                    NodeInstanceCapacity(linux_client_count=2),
                    NodeInstanceCapacity(linux_client_count=4),
                ],
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4, 5)),
        ],
    )


###
# Linux x86 clients
###


def test_distribute_personas_to_instances_with_linux_x86_64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_x86_64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_x86_64_instances=[NodeInstanceCapacity(client_count=3)],
            ),
        )


def test_distribute_personas_to_instances_with_linux_x86_64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_x86_64_instances=[
                    NodeInstanceCapacity(linux_client_count=3),
                    NodeInstanceCapacity(linux_client_count=3),
                ],
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_x86_64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_x86_64_instances=[
                    NodeInstanceCapacity(linux_client_count=2),
                    NodeInstanceCapacity(linux_client_count=4),
                ],
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4, 5)),
        ],
    )


###
# GPU ARM servers
###


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3)
                ],
            ),
        )


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                ],
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_gpu_arm64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=2),
                    NodeInstanceCapacity(linux_gpu_client_count=4),
                ],
            ),
        ),
        linux_gpu_arm64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4, 5)),
        ],
    )


###
# GPU x86 servers
###


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3)
                ],
            ),
        )


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                    NodeInstanceCapacity(linux_gpu_client_count=3),
                ],
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_gpu_x86_64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_gpu_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=2),
                    NodeInstanceCapacity(linux_gpu_client_count=4),
                ],
            ),
        ),
        linux_gpu_x86_64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_gpu_clients=race_clients(2, 4, 5)),
        ],
    )


###
# Linux ARM servers
###


def test_distribute_personas_to_instances_with_linux_arm64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_arm64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_arm64_instances=[NodeInstanceCapacity(linux_client_count=3)],
            ),
        )


def test_distribute_personas_to_instances_with_linux_arm64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_arm64_instances=[
                    NodeInstanceCapacity(linux_client_count=3),
                    NodeInstanceCapacity(linux_client_count=3),
                ],
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_arm64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_arm64_instances=[
                    NodeInstanceCapacity(linux_client_count=2),
                    NodeInstanceCapacity(linux_client_count=4),
                ],
            ),
        ),
        linux_arm64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4, 5)),
        ],
    )


###
# Linux x86 servers
###


def test_distribute_personas_to_instances_with_linux_x86_64_clients_but_no_instances():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(),
        )


def test_distribute_personas_to_instances_with_linux_x86_64_clients_but_insufficient_slots():
    with pytest.raises(error_utils.RIB721, match=r".*No available hosts.*"):
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_x86_64_instances=[NodeInstanceCapacity(linux_client_count=3)],
            ),
        )


def test_distribute_personas_to_instances_with_linux_x86_64_clients_evenly_spread():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_x86_64_instances=[
                    NodeInstanceCapacity(linux_client_count=3),
                    NodeInstanceCapacity(linux_client_count=3),
                ],
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4)),
        ],
    )


def test_distribute_personas_to_instances_with_linux_x86_64_clients_topology_driven():
    assert_distribution_has_manifests(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                linux_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
            ),
            topology=NodeInstanceTopology(
                linux_x86_64_instances=[
                    NodeInstanceCapacity(linux_client_count=2),
                    NodeInstanceCapacity(linux_client_count=4),
                ],
            ),
        ),
        linux_x86_64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(1, 3)),
            NodeInstanceManifest(linux_clients=race_clients(2, 4, 5)),
        ],
    )


###
# Mixed ARM
###


def test_distribute_personas_to_instances_with_mixed_arm64():
    assert_topology_has_instances(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
                linux_gpu_arm64_client_personas=race_clients(6, 7, 8, 9, 10),
                linux_arm64_client_personas=race_clients(11, 12, 13, 14, 15),
                linux_gpu_arm64_server_personas=race_servers(1, 2, 3, 4, 5),
                linux_arm64_server_personas=race_servers(6, 7, 8, 9, 10),
            ),
            topology=NodeInstanceTopology(
                android_arm64_instances=[
                    NodeInstanceCapacity(android_client_count=3),
                    NodeInstanceCapacity(android_client_count=3),
                ],
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=6),
                    NodeInstanceCapacity(linux_gpu_server_count=6),
                ],
                linux_arm64_instances=[
                    NodeInstanceCapacity(linux_client_count=3, linux_server_count=3),
                    NodeInstanceCapacity(linux_client_count=3, linux_server_count=3),
                ],
            ),
        ),
        android_arm64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(android_clients=race_clients(2, 4)),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(6, 7, 8, 9, 10)),
            NodeInstanceManifest(linux_gpu_servers=race_servers(1, 2, 3, 4, 5)),
        ],
        linux_arm64_instances=[
            NodeInstanceManifest(
                linux_clients=race_clients(12, 14), linux_servers=race_servers(6, 8, 10)
            ),
            NodeInstanceManifest(
                linux_clients=race_clients(11, 13, 15), linux_servers=race_servers(7, 9)
            ),
        ],
    )


###
# Mixed x86
###


def test_distribute_personas_to_instances_with_mixed_x86_64():
    assert_topology_has_instances(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_x86_64_client_personas=race_clients(1, 2, 3, 4, 5),
                linux_gpu_x86_64_client_personas=race_clients(6, 7, 8, 9, 10),
                linux_x86_64_client_personas=race_clients(11, 12, 13, 14, 15),
                linux_gpu_x86_64_server_personas=race_servers(1, 2, 3, 4, 5),
                linux_x86_64_server_personas=race_servers(6, 7, 8, 9, 10),
            ),
            topology=NodeInstanceTopology(
                android_x86_64_instances=[
                    NodeInstanceCapacity(android_client_count=3),
                    NodeInstanceCapacity(android_client_count=3),
                ],
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=6),
                    NodeInstanceCapacity(linux_gpu_server_count=6),
                ],
                linux_x86_64_instances=[
                    NodeInstanceCapacity(linux_client_count=3, linux_server_count=3),
                    NodeInstanceCapacity(linux_client_count=3, linux_server_count=3),
                ],
            ),
        ),
        android_x86_64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(android_clients=race_clients(2, 4)),
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(6, 7, 8, 9, 10)),
            NodeInstanceManifest(linux_gpu_servers=race_servers(1, 2, 3, 4, 5)),
        ],
        linux_x86_64_instances=[
            NodeInstanceManifest(
                linux_clients=race_clients(12, 14), linux_servers=race_servers(6, 8, 10)
            ),
            NodeInstanceManifest(
                linux_clients=race_clients(11, 13, 15), linux_servers=race_servers(7, 9)
            ),
        ],
    )


###
# Mixed architecture
###


def test_distribute_personas_to_instances_with_mixed_arch():
    assert_topology_has_instances(
        aws_topology_utils.distribute_personas_to_instances(
            personas=Personas(
                android_arm64_client_personas=race_clients(1, 2, 3, 4, 5),
                linux_gpu_arm64_client_personas=race_clients(6, 7, 8, 9, 10),
                linux_arm64_client_personas=race_clients(11, 12, 13, 14, 15),
                linux_gpu_arm64_server_personas=race_servers(1, 2, 3, 4, 5),
                linux_arm64_server_personas=race_servers(6, 7, 8, 9, 10),
                android_x86_64_client_personas=race_clients(16, 17, 18, 19, 20),
                linux_gpu_x86_64_client_personas=race_clients(21, 22, 23, 24, 25),
                linux_x86_64_client_personas=race_clients(26, 27, 28, 29, 30),
                linux_gpu_x86_64_server_personas=race_servers(11, 12, 13, 14, 15),
                linux_x86_64_server_personas=race_servers(16, 17, 18, 19, 20),
            ),
            topology=NodeInstanceTopology(
                android_arm64_instances=[
                    NodeInstanceCapacity(android_client_count=3),
                    NodeInstanceCapacity(android_client_count=3),
                ],
                linux_gpu_arm64_instances=[
                    NodeInstanceCapacity(linux_gpu_client_count=6),
                    NodeInstanceCapacity(linux_gpu_server_count=6),
                ],
                linux_arm64_instances=[
                    NodeInstanceCapacity(linux_client_count=3, linux_server_count=3),
                    NodeInstanceCapacity(linux_client_count=3, linux_server_count=3),
                ],
                android_x86_64_instances=[
                    NodeInstanceCapacity(android_client_count=5),
                ],
                linux_gpu_x86_64_instances=[
                    NodeInstanceCapacity(
                        linux_gpu_client_count=2,
                        linux_gpu_server_count=1,
                        linux_server_count=1,
                    ),
                    NodeInstanceCapacity(
                        linux_gpu_client_count=1, linux_gpu_server_count=2
                    ),
                    NodeInstanceCapacity(
                        linux_gpu_client_count=2, linux_gpu_server_count=2
                    ),
                ],
                linux_x86_64_instances=[
                    NodeInstanceCapacity(linux_client_count=5),
                    NodeInstanceCapacity(linux_server_count=2),
                    NodeInstanceCapacity(linux_server_count=2),
                ],
            ),
        ),
        android_arm64_instances=[
            NodeInstanceManifest(android_clients=race_clients(1, 3, 5)),
            NodeInstanceManifest(android_clients=race_clients(2, 4)),
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceManifest(linux_gpu_clients=race_clients(6, 7, 8, 9, 10)),
            NodeInstanceManifest(linux_gpu_servers=race_servers(1, 2, 3, 4, 5)),
        ],
        linux_arm64_instances=[
            NodeInstanceManifest(
                linux_clients=race_clients(12, 14), linux_servers=race_servers(6, 8, 10)
            ),
            NodeInstanceManifest(
                linux_clients=race_clients(11, 13, 15), linux_servers=race_servers(7, 9)
            ),
        ],
        android_x86_64_instances=[
            NodeInstanceManifest(android_clients=race_clients(16, 17, 18, 19, 20))
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceManifest(
                linux_gpu_clients=race_clients(21, 22),
                linux_gpu_servers=race_servers(11),
                linux_servers=race_servers(20),
            ),
            NodeInstanceManifest(
                linux_gpu_clients=race_clients(23),
                linux_gpu_servers=race_servers(12, 14),
            ),
            NodeInstanceManifest(
                linux_gpu_clients=race_clients(24, 25),
                linux_gpu_servers=race_servers(13, 15),
            ),
        ],
        linux_x86_64_instances=[
            NodeInstanceManifest(linux_clients=race_clients(26, 27, 28, 29, 30)),
            NodeInstanceManifest(linux_servers=race_servers(16, 18)),
            NodeInstanceManifest(linux_servers=race_servers(17, 19)),
        ],
    )

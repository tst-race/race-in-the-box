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
        Test File for rib_aws_deployment_status.py
"""

# Python Library Imports
from copy import deepcopy
import requests
import pytest
from unittest.mock import MagicMock, patch, create_autospec

# Local Library Imports
from rib.aws_env.rib_aws_env_status import ContainerRuntimeInfo, Ec2InstanceRuntimeInfo
from rib.deployment.rib_aws_deployment import RibAwsDeployment
from rib.deployment.rib_deployment_config import AwsDeploymentConfig
from rib.deployment.status.rib_aws_deployment_status import RibAwsDeploymentStatus
from rib.utils import race_node_utils, status_utils
from rib.utils.aws_topology_utils import NodeInstanceDistribution, NodeInstanceManifest
from rib.utils.status_utils import (
    ContainerStatus,
    ParentStatus,
    ServiceStatus,
    StatusReport,
)
from rib.deployment.tests.mock_deployment_configs.aws_3x3_default_config import (
    aws_3x3_default_config_dict,
)

###
# Mocks
###


@pytest.fixture()
def example_3x3_aws_deployment_config() -> AwsDeploymentConfig:
    """3x3 local deployment config"""
    return deepcopy(aws_3x3_default_config_dict)


@pytest.fixture
def deployment(example_3x3_aws_deployment_config):
    deployment = MagicMock()
    deployment.aux_services = RibAwsDeployment.aux_services + ["rib-bastion"]
    deployment.verify_deployment_is_active = MagicMock()
    deployment._race_node_interface = create_autospec(race_node_utils.RaceNodeInterface)
    deployment.config = example_3x3_aws_deployment_config
    return deployment


@pytest.fixture
def status(deployment):
    status = RibAwsDeploymentStatus(deployment)
    status._orig_verify_deployment_is_active = status.verify_deployment_is_active
    return status


###
# Tests
###


###
# get_container_status_report
###


@patch(
    "rib.utils.aws_topology_utils.read_distribution_from_file",
    MagicMock(return_value=NodeInstanceDistribution()),
)
def test_get_container_status_report_no_node_roles(status):
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.get_runtime_info = MagicMock(return_value={})
    assert status.get_container_status_report() == StatusReport(
        status=ParentStatus.ALL_DOWN,
        children={
            "cluster-manager": StatusReport(status=ParentStatus.ALL_DOWN, children={})
        },
    )


@patch(
    "rib.utils.aws_topology_utils.read_distribution_from_file",
    MagicMock(
        return_value=NodeInstanceDistribution(
            android_arm64_instances=[NodeInstanceManifest()],
            android_x86_64_instances=[NodeInstanceManifest()],
            linux_gpu_arm64_instances=[NodeInstanceManifest()],
            linux_gpu_x86_64_instances=[NodeInstanceManifest()],
            linux_arm64_instances=[NodeInstanceManifest()],
            linux_x86_64_instances=[NodeInstanceManifest()],
        )
    ),
)
def test_get_container_status_report_all_node_roles(status):
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.get_runtime_info = MagicMock(return_value={})
    assert status.get_container_status_report() == StatusReport(
        status=ParentStatus.ALL_DOWN,
        children={
            "cluster-manager": StatusReport(status=ParentStatus.ALL_DOWN, children={}),
            "android-arm64-node-host": StatusReport(
                status=ParentStatus.ALL_DOWN,
                children={
                    "missing-instance-0": StatusReport(status=ParentStatus.ALL_DOWN)
                },
            ),
            "android-x86-64-node-host": StatusReport(
                status=ParentStatus.ALL_DOWN,
                children={
                    "missing-instance-0": StatusReport(status=ParentStatus.ALL_DOWN)
                },
            ),
            "linux-gpu-arm64-node-host": StatusReport(
                status=ParentStatus.ALL_DOWN,
                children={
                    "missing-instance-0": StatusReport(status=ParentStatus.ALL_DOWN)
                },
            ),
            "linux-gpu-x86-64-node-host": StatusReport(
                status=ParentStatus.ALL_DOWN,
                children={
                    "missing-instance-0": StatusReport(status=ParentStatus.ALL_DOWN)
                },
            ),
            "linux-arm64-node-host": StatusReport(
                status=ParentStatus.ALL_DOWN,
                children={
                    "missing-instance-0": StatusReport(status=ParentStatus.ALL_DOWN)
                },
            ),
            "linux-x86-64-node-host": StatusReport(
                status=ParentStatus.ALL_DOWN,
                children={
                    "missing-instance-0": StatusReport(status=ParentStatus.ALL_DOWN)
                },
            ),
        },
    )


###
# _create_cluster_manager_role_container_status_report
###


def test__create_cluster_manager_role_container_status_report(
    status,
):
    status._create_cluster_manager_container_status_report = MagicMock(
        return_value=StatusReport(status=ParentStatus.ALL_RUNNING)
    )
    assert status._create_cluster_manager_role_container_status_report(
        instances=[Ec2InstanceRuntimeInfo(public_dns="hostname-C")]
    ) == StatusReport(
        status=ParentStatus.ALL_RUNNING,
        children={"hostname-C": StatusReport(status=ParentStatus.ALL_RUNNING)},
    )


###
# _create_cluster_manager_container_status_report
###


def test__create_cluster_manager_container_status_report(
    status,
):
    status.deployment.aux_services.append("bogus-service")
    assert status._create_cluster_manager_container_status_report(
        instance=Ec2InstanceRuntimeInfo(
            containers={
                "/bastion_rib-bastion.1.yndqvqp3ywi65yrv2qbft31kh": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 20 minutes",
                ),
                "/opentracing_elasticsearch.1.16tv9udg6cxyyz6ghwsnpwwe3": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 20 minutes (healthy)",
                ),
                "/opentracing_graph_renderer.1.16tv9udg6cxyyz6ghwsnpwwe3": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 20 minutes (healthy)",
                ),
                "/opentracing_jaeger-collector.1.zqdizu2d4xnmfiu1ildqyzhrw": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 19 minutes",
                ),
                "/opentracing_jaeger-query.1.i3hgpjoqrnx46mrq2zuz74ywh": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 19 minutes",
                ),
                "/opentracing_kibana.1.p00imkqziptoe8bhlwpxlw8o5": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 20 minutes (healthy)",
                ),
                "/orchestration_rib-file-server.1.sx47mctfm126p0fg2cyczu0w1": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 19 minutes",
                ),
                "/orchestration_rib-redis.1.pxo69yhmdemdajg3lumlh4er5": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 19 minutes (healthy)",
                ),
                "/vpn_openvpn.1.xxxxxxxxxxxxxxxxxxxxxxxxx": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 19 minutes (healthy)",
                ),
                "/vpn_dnsproxy.1.xxxxxxxxxxxxxxxxxxxxxxxxx": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 19 minutes (healthy)",
                ),
            }
        )
    ) == StatusReport(
        status=ParentStatus.SOME_RUNNING,
        children={
            "rib-bastion": StatusReport(status=ContainerStatus.RUNNING),
            "dnsproxy": StatusReport(status=ContainerStatus.RUNNING),
            "elasticsearch": StatusReport(status=ContainerStatus.RUNNING),
            "graph_renderer": StatusReport(status=ContainerStatus.RUNNING),
            "jaeger-collector": StatusReport(status=ContainerStatus.RUNNING),
            "jaeger-query": StatusReport(status=ContainerStatus.RUNNING),
            "kibana": StatusReport(status=ContainerStatus.RUNNING),
            "openvpn": StatusReport(status=ContainerStatus.RUNNING),
            "rib-file-server": StatusReport(status=ContainerStatus.RUNNING),
            "rib-redis": StatusReport(status=ContainerStatus.RUNNING),
            "bogus-service": StatusReport(status=ContainerStatus.NOT_PRESENT),
        },
    )


def test__create_cluster_manager_container_status_report_different_deployment(
    status,
):
    assert status._create_cluster_manager_container_status_report(
        instance=Ec2InstanceRuntimeInfo(
            containers={
                "/bastion_rib-bastion.1.yndqvqp3ywi65yrv2qbft31kh": ContainerRuntimeInfo(
                    deployment_name="other_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 20 minutes",
                ),
                "/opentracing_elasticsearch.1.16tv9udg6cxyyz6ghwsnpwwe3": ContainerRuntimeInfo(
                    deployment_name="other_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 20 minutes (healthy)",
                ),
            }
        )
    ) == StatusReport(
        status=ParentStatus.ALL_DOWN,
        children={
            "rib-bastion": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "dnsproxy": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "elasticsearch": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "graph_renderer": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "jaeger-collector": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "jaeger-query": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "kibana": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "openvpn": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "rib-file-server": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "rib-redis": StatusReport(status=ContainerStatus.NOT_PRESENT),
        },
    )


###
# _create_node_host_role_container_status_report
###


@patch(
    "rib.deployment.status.rib_aws_deployment_status.RibAwsDeploymentStatus._create_node_host_container_status_report"
)
def test__create_node_host_role_container_status_report(
    create_host_status_report, status
):
    create_host_status_report.side_effect = [
        StatusReport(status=ParentStatus.ALL_RUNNING),
        StatusReport(status=ParentStatus.SOME_RUNNING),
    ]

    assert status._create_node_host_role_container_status_report(
        instances=[
            Ec2InstanceRuntimeInfo(public_dns="hostname-B"),
            Ec2InstanceRuntimeInfo(public_dns="hostname-A"),
        ],
        manifests=[NodeInstanceManifest(), NodeInstanceManifest()],
    ) == StatusReport(
        status=ParentStatus.SOME_RUNNING,
        children={
            "hostname-A": StatusReport(status=ParentStatus.ALL_RUNNING),
            "hostname-B": StatusReport(status=ParentStatus.SOME_RUNNING),
        },
    )


###
# _create_node_host_container_status_report
###


def test__create_node_host_container_status_report(status):
    assert status._create_node_host_container_status_report(
        instance=Ec2InstanceRuntimeInfo(
            containers={
                "/race_nodes_race-client-00001_1": ContainerRuntimeInfo(
                    deployment_name="example_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 2 minutes (healthy)",
                )
            }
        ),
        manifest=NodeInstanceManifest(
            android_clients=["race-client-00001"],
            linux_gpu_clients=["race-client-00002"],
            linux_clients=["race-client-00003"],
            linux_gpu_servers=["race-server-00001"],
            linux_servers=["race-server-00002"],
        ),
    ) == StatusReport(
        status=ParentStatus.SOME_RUNNING,
        children={
            "race-client-00001": StatusReport(status=ContainerStatus.RUNNING),
            "race-client-00002": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-client-00003": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-server-00001": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-server-00002": StatusReport(status=ContainerStatus.NOT_PRESENT),
        },
    )


def test__create_node_host_container_status_report_different_deployment(
    status,
):
    assert status._create_node_host_container_status_report(
        instance=Ec2InstanceRuntimeInfo(
            containers={
                "/race_nodes_race-client-00001_1": ContainerRuntimeInfo(
                    deployment_name="other_3x3_aws_deployment_obj",
                    state="running",
                    status="Up 2 minutes (healthy)",
                )
            }
        ),
        manifest=NodeInstanceManifest(
            android_clients=["race-client-00001"],
            linux_gpu_clients=["race-client-00002"],
            linux_clients=["race-client-00003"],
            linux_gpu_servers=["race-server-00001"],
            linux_servers=["race-server-00002"],
        ),
    ) == StatusReport(
        status=ParentStatus.ALL_DOWN,
        children={
            "race-client-00001": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-client-00002": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-client-00003": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-server-00001": StatusReport(status=ContainerStatus.NOT_PRESENT),
            "race-server-00002": StatusReport(status=ContainerStatus.NOT_PRESENT),
        },
    )


###
# _get_rib_services_status_report
###


def create_response(status_code: int) -> requests.Response:
    """
    Create a requests response object (because they don't have an __init__ that initializes
    anything)
    """
    response = requests.Response()
    response.status_code = status_code
    return response


@patch("requests.get", MagicMock(return_value=create_response(status_code=200)))
@patch("rib.utils.redis_utils.create_redis_client", MagicMock(return_value=MagicMock()))
def test__get_rib_services_status_report_all_running(status):
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.get_cluster_manager_ip = MagicMock(
        return_value="11.22.33.44"
    )
    assert status._get_rib_services_status_report() == status_utils.StatusReport(
        status=ParentStatus.ALL_RUNNING,
        children={
            "ElasticSearch": StatusReport(status=ServiceStatus.RUNNING),
            "Kibana": StatusReport(status=ServiceStatus.RUNNING),
            "Jaeger UI": StatusReport(status=ServiceStatus.RUNNING),
            "File Server": StatusReport(status=ServiceStatus.RUNNING),
            "Redis": StatusReport(status=ServiceStatus.RUNNING),
        },
    )


@patch(
    "requests.get",
    MagicMock(
        side_effect=[
            create_response(status_code=404),
            create_response(status_code=200),
            create_response(status_code=404),
            create_response(status_code=200),
        ]
    ),
)
@patch("rib.utils.redis_utils.create_redis_client", MagicMock(return_value=None))
def test__get_rib_services_status_report_some_running(
    status,
):
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.get_cluster_manager_ip = MagicMock(
        return_value="11.22.33.44"
    )
    assert status._get_rib_services_status_report() == StatusReport(
        status=ParentStatus.SOME_RUNNING,
        children={
            "ElasticSearch": StatusReport(
                status=ServiceStatus.NOT_RUNNING,
                reason="HTTP status code 404",
            ),
            "Kibana": StatusReport(status=ServiceStatus.RUNNING),
            "Jaeger UI": StatusReport(
                status=ServiceStatus.NOT_RUNNING,
                reason="HTTP status code 404",
            ),
            "File Server": StatusReport(status=ServiceStatus.RUNNING),
            "Redis": StatusReport(status=ServiceStatus.NOT_RUNNING),
        },
    )


def test__get_rib_services_status_report_no_cluster_manager(
    status,
):
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.get_cluster_manager_ip = MagicMock(return_value=None)
    assert status._get_rib_services_status_report() == StatusReport(
        status=ParentStatus.ALL_DOWN
    )


###
# _get_external_services_status_report
###


def test__get_external_services_status_report_all_running(
    status,
):
    status.deployment._external_services = {
        "PluginId1": "script-path",
        "PluginId2": "script-path",
    }
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.run_remote_command = MagicMock(
        return_value={"service-host": {"hostname-D": {"success": True}}}
    )
    assert status._get_external_services_status_report() == StatusReport(
        status=ParentStatus.ALL_RUNNING,
        children={
            "PluginId1": StatusReport(status=ServiceStatus.RUNNING),
            "PluginId2": StatusReport(status=ServiceStatus.RUNNING),
        },
    )


def test__get_external_services_status_report_no_service_host(
    status,
):
    status.deployment._external_services = {
        "PluginId1": "script-path",
        "PluginId2": "script-path",
    }
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.run_remote_command = MagicMock(return_value={})
    assert status._get_external_services_status_report() == StatusReport(
        status=ParentStatus.ALL_DOWN,
        children={
            "PluginId1": StatusReport(status=ServiceStatus.NOT_RUNNING),
            "PluginId2": StatusReport(status=ServiceStatus.NOT_RUNNING),
        },
    )


def test__get_external_services_status_report_all_down(
    status,
):
    status.deployment._external_services = {
        "PluginId1": "script-path",
        "PluginId2": "script-path",
    }
    status.deployment._aws_env = MagicMock()
    status.deployment._aws_env.run_remote_command = MagicMock(
        return_value={"service-host": {"hostname-D": {"success": False}}}
    )
    assert status._get_external_services_status_report() == StatusReport(
        status=ParentStatus.ALL_DOWN,
        children={
            "PluginId1": StatusReport(status=ServiceStatus.NOT_RUNNING),
            "PluginId2": StatusReport(status=ServiceStatus.NOT_RUNNING),
        },
    )

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
        Test File for rib_aws_deployment.py
"""

# Python Library Imports
from copy import deepcopy
import os
import pytest
import shutil
import tempfile
from unittest.mock import MagicMock
from unittest.mock import MagicMock, create_autospec
from rib.aws_env.rib_aws_env import RibAwsEnv

# Local Library Imports
from rib.deployment.rib_aws_deployment import RibAwsDeployment
from rib.deployment.rib_deployment_config import (
    AwsDeploymentConfig,
    DeploymentMetadata,
    ImageConfig,
    NodeConfig,
)
from rib.utils import plugin_utils, race_node_utils, ssh_utils
from rib.utils.aws_topology_utils import NodeInstanceManifest
from .mock_deployment_configs.aws_3x3_default_config import (
    aws_3x3_default_config_dict,
)


###
# Mocks
###


@pytest.fixture(autouse=True)
def mock_ssh_utils__run_ssh_command():
    """
    Purpose:
        Mocks/Monkeypatches the return value for `ssh_utils.run_ssh_command`. Sets
        return to str
    Args:
        N/A
    """

    ssh_utils.run_ssh_command = MagicMock()
    ssh_utils.run_ssh_command.return_value = (
        "ssh_utils.run_ssh_command stdout",
        "ssh_utils.run_ssh_command stderr",
    )


###
# Data Fixtures
###


@pytest.fixture
def rib_state_path() -> str:
    """Sets up a test RiB state path in a temporary location"""
    # Create the test directories
    test_state_path = os.path.join(tempfile.gettempdir(), "rib-unit-test-state-path")
    aws_deployments_dir = os.path.join(
        test_state_path, ".race", "rib", "deployments", "aws"
    )
    os.makedirs(aws_deployments_dir, exist_ok=True)
    # Save original values
    orig_mode_dir = RibAwsDeployment.pathsClass.dirs["mode"]
    orig_templates_dir = RibAwsDeployment.pathsClass.dirs["templates"]
    # Redirect AWS deployments to the test files
    RibAwsDeployment.pathsClass.dirs["mode"] = aws_deployments_dir
    # Go up 2 directories to get to the source templates dir
    RibAwsDeployment.pathsClass.dirs["templates"] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "artifacts",
        "deployments",
        "aws",
        "templates",
    )
    # Execute test
    yield test_state_path
    # Reset
    shutil.rmtree(test_state_path, ignore_errors=True)
    RibAwsDeployment.pathsClass.dirs["mode"] = orig_mode_dir
    RibAwsDeployment.pathsClass.dirs["templates"] = orig_templates_dir


@pytest.fixture
def aws_env() -> RibAwsEnv:
    mock_aws_env = create_autospec(RibAwsEnv)
    mock_aws_env.config = {
        "name": "test-aws-env",
        "remote_username": "test-remote-username",
    }
    return mock_aws_env


@pytest.fixture()
def example_3x3_aws_deployment_config() -> AwsDeploymentConfig:
    """3x3 local deployment config"""
    return AwsDeploymentConfig.parse_obj(aws_3x3_default_config_dict)


@pytest.fixture()
def complex_aws_deployment_config() -> AwsDeploymentConfig:
    """A complex AWS deployment config with a node in every possible state"""
    config = AwsDeploymentConfig.parse_obj(aws_3x3_default_config_dict)

    client_idx = 1
    config["images"] = [
        ImageConfig(
            tag="test-android-arm64-client-image",
            platform="android",
            architecture="arm64-v8a",
            node_type="client",
        ),
        ImageConfig(
            tag="test-android-x86_64-client-image",
            platform="android",
            architecture="x86_64",
            node_type="client",
        ),
        ImageConfig(
            tag="test-linux-arm64-client-image",
            platform="linux",
            architecture="arm64-v8a",
            node_type="client",
        ),
        ImageConfig(
            tag="test-linux-x86_64-client-image",
            platform="linux",
            architecture="x86_64",
            node_type="client",
        ),
        ImageConfig(
            tag="test-linux-arm64-server-image",
            platform="linux",
            architecture="arm64-v8a",
            node_type="server",
        ),
        ImageConfig(
            tag="test-linux-x86_64-server-image",
            platform="linux",
            architecture="x86_64",
            node_type="server",
        ),
    ]
    config["nodes"] = {}
    # Clients 1-4
    for genesis in (False, True):
        for bridge in (False, True):
            config["nodes"][f"race-client-{str(client_idx).zfill(5)}"] = NodeConfig(
                platform="android",
                architecture="arm64-v8a",
                node_type="client",
                genesis=genesis,
                bridge=bridge,
                gpu=False,
            )
            client_idx += 1

    # Clients 5-12
    for gpu in (False, True):
        for genesis in (False, True):
            for bridge in (False, True):
                config["nodes"][f"race-client-{str(client_idx).zfill(5)}"] = NodeConfig(
                    platform="linux",
                    architecture="x86_64",
                    node_type="client",
                    genesis=genesis,
                    bridge=bridge,
                    gpu=gpu,
                )
                client_idx += 1

    server_idx = 1
    # Servers 1-8
    for gpu in (False, True):
        for genesis in (False, True):
            for bridge in (False, True):
                config["nodes"][f"race-server-{str(server_idx).zfill(5)}"] = NodeConfig(
                    platform="linux",
                    architecture="x86_64",
                    node_type="server",
                    genesis=genesis,
                    bridge=bridge,
                    gpu=gpu,
                )
                server_idx += 1

    return config


@pytest.fixture
def deployment_metadata() -> DeploymentMetadata:
    """Deployment metadata"""
    cache_metadata = plugin_utils.KitCacheMetadata(
        source_type=plugin_utils.KitSourceType.LOCAL,
        source_uri="/race-core",
        auth=False,
        time="2023-05-12T10:31:05",
        cache_path="/cache",
        checksum="",
    )
    return DeploymentMetadata(
        rib_image={
            "digest": "rib-image-digest",
            "created": "rib-image-created",
        },
        create_command="test-create-command",
        create_date="2022-01-07T11:22:33",
        race_core_cache=cache_metadata,
        android_app_cache=cache_metadata,
        linux_app_cache=cache_metadata,
        node_daemon_cache=cache_metadata,
        network_manager_kit_cache=cache_metadata,
        comms_kits_cache={"test-comms-plugin": cache_metadata},
        artifact_manager_kits_cache={"test-artifact-manager-plugin": cache_metadata},
        last_config_gen_command=None,
        last_config_gen_time=None,
        last_up_command=None,
        last_up_time=None,
        last_start_command=None,
        last_start_time=None,
        last_stop_command=None,
        last_stop_time=None,
        last_down_command=None,
        last_down_time=None,
    )


@pytest.fixture()
def example_3x3_aws_deployment_obj(
    example_3x3_aws_deployment_config, deployment_metadata
):
    """
    Purpose:
        Fixture of an Example AWS RiB Deployment.

        Configured with 3 clients and 3 servers. This is the "default" config
        we use tely for testing in most cases
    Args:
        N/A
    Return:
        example_3x3_aws_deployment_obj (RibAwsDeployment Obj): Example configured
            3x3 aws deployment for testing
    """

    deployment = RibAwsDeployment(
        example_3x3_aws_deployment_config, deployment_metadata
    )
    deployment.status.verify_deployment_is_active = MagicMock()
    deployment._race_node_interface = create_autospec(race_node_utils.RaceNodeInterface)
    return deployment


@pytest.fixture()
def complex_aws_deployment(complex_aws_deployment_config, deployment_metadata, aws_env):
    deployment = RibAwsDeployment(complex_aws_deployment_config, deployment_metadata)
    deployment._aws_env = aws_env
    deployment.status.verify_deployment_is_active = MagicMock()
    deployment._race_node_interface = create_autospec(race_node_utils.RaceNodeInterface)
    return deployment


###
# Test AWS Deployment Methods
###


################################################################################
# __init__
################################################################################


def test___init__(example_3x3_aws_deployment_obj):
    """
    Purpose:
        Test the send_message method for AWS Deployments
    Args:
        example_3x3_aws_deployment_obj (RibAwsDeployment Obj): Example configured
            3x3 aws deployment for testing
    """

    # Assert Property Methods for Configs and Dirs
    assert example_3x3_aws_deployment_obj.config
    assert example_3x3_aws_deployment_obj.metadata

    # TODO More Testing


################################################################################
# Android client persona properties
################################################################################


def test_android_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.android_client_personas == [
        "race-client-00001",
        "race-client-00002",
        "race-client-00003",
        "race-client-00004",
    ]


def test_android_bootstrap_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.android_bootstrap_client_personas == [
        "race-client-00001",
        "race-client-00002",
    ]


def test_android_genesis_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.android_genesis_client_personas == [
        "race-client-00003",
        "race-client-00004",
    ]


def test_android_bridge_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.android_bridge_client_personas == [
        "race-client-00002",
        "race-client-00004",
    ]


################################################################################
# Linux client persona properties
################################################################################


def test_linux_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_client_personas == [
        "race-client-00005",
        "race-client-00006",
        "race-client-00007",
        "race-client-00008",
        "race-client-00009",
        "race-client-00010",
        "race-client-00011",
        "race-client-00012",
    ]


def test_linux_bootstrap_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_bootstrap_client_personas == [
        "race-client-00005",
        "race-client-00006",
        "race-client-00009",
        "race-client-00010",
    ]


def test_linux_genesis_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_genesis_client_personas == [
        "race-client-00007",
        "race-client-00008",
        "race-client-00011",
        "race-client-00012",
    ]


def test_linux_bridge_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_bridge_client_personas == [
        "race-client-00006",
        "race-client-00008",
        "race-client-00010",
        "race-client-00012",
    ]


def test_linux_gpu_client_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_gpu_client_personas == [
        "race-client-00009",
        "race-client-00010",
        "race-client-00011",
        "race-client-00012",
    ]


################################################################################
# Linux server persona properties
################################################################################


def test_linux_server_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_server_personas == [
        "race-server-00001",
        "race-server-00002",
        "race-server-00003",
        "race-server-00004",
        "race-server-00005",
        "race-server-00006",
        "race-server-00007",
        "race-server-00008",
    ]


def test_linux_bootstrap_server_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_bootstrap_server_personas == [
        "race-server-00001",
        "race-server-00002",
        "race-server-00005",
        "race-server-00006",
    ]


def test_linux_genesis_server_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_genesis_server_personas == [
        "race-server-00003",
        "race-server-00004",
        "race-server-00007",
        "race-server-00008",
    ]


def test_linux_bridge_server_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_bridge_server_personas == [
        "race-server-00002",
        "race-server-00004",
        "race-server-00006",
        "race-server-00008",
    ]


def test_linux_gpu_server_personas(complex_aws_deployment):
    assert complex_aws_deployment.linux_gpu_server_personas == [
        "race-server-00005",
        "race-server-00006",
        "race-server-00007",
        "race-server-00008",
    ]


################################################################################
# generate_android_node_docker_compose_data
################################################################################


@pytest.mark.usefixtures("rib_state_path")
def test_generate_android_arm64_node_docker_compose_data(complex_aws_deployment):
    docker_compose = complex_aws_deployment.generate_android_node_docker_compose_data(
        NodeInstanceManifest(
            # Clients 2 and 4 are bridged
            android_clients=["race-client-00001", "race-client-00003"]
        ),
        "arm64",
    )

    assert len(docker_compose["services"]) == 2

    client_1 = docker_compose["services"]["race-client-00001"]
    assert client_1["image"] == "test-android-arm64-client-image"
    assert client_1["environment"]["UNINSTALL_RACE"] == "yes"
    assert client_1["environment"]["CUTTLEFISH_INSTANCE"] == 1
    assert client_1["environment"]["STARTUP_DELAY"] == 0
    assert "5901:6444" in client_1["ports"]

    client_3 = docker_compose["services"]["race-client-00003"]
    assert client_3["image"] == "test-android-arm64-client-image"
    assert client_3["environment"]["UNINSTALL_RACE"] == "no"
    assert client_3["environment"]["CUTTLEFISH_INSTANCE"] == 2
    assert client_3["environment"]["STARTUP_DELAY"] == 0
    assert "5902:6445" in client_3["ports"]


@pytest.mark.usefixtures("rib_state_path")
def test_generate_android_x86_64_node_docker_compose_data(complex_aws_deployment):
    docker_compose = complex_aws_deployment.generate_android_node_docker_compose_data(
        NodeInstanceManifest(
            # Clients 2 and 4 are bridged
            android_clients=["race-client-00001", "race-client-00003"]
        ),
        "x86_64",
    )

    assert len(docker_compose["services"]) == 2

    client_1 = docker_compose["services"]["race-client-00001"]
    assert client_1["image"] == "test-android-x86_64-client-image"
    assert client_1["environment"]["UNINSTALL_RACE"] == "yes"
    assert "5901:5901" in client_1["ports"]

    client_3 = docker_compose["services"]["race-client-00003"]
    assert client_3["image"] == "test-android-x86_64-client-image"
    assert client_3["environment"]["UNINSTALL_RACE"] == "no"
    assert "5902:5901" in client_3["ports"]


################################################################################
# generate_gpu_node_docker_compose_data
################################################################################


@pytest.mark.usefixtures("rib_state_path")
def test_generate_gpu_arm64_node_docker_compose_data(complex_aws_deployment):
    docker_compose = complex_aws_deployment.generate_gpu_node_docker_compose_data(
        NodeInstanceManifest(
            # GPU clients are 9-12, 10 and 12 are bridged
            linux_gpu_clients=["race-client-00009", "race-client-00011"],
            # Include 1 co-located non-gpu client
            linux_clients=["race-client-00005"],
            # GPU servers are 5-8, 6 and 8 are bridged
            linux_gpu_servers=["race-server-00005", "race-server-00007"],
            # Include 1 co-located non-gpu server
            linux_servers=["race-server-00001"],
        ),
        "arm64",
    )

    assert len(docker_compose["services"]) == 6

    client_5 = docker_compose["services"]["race-client-00005"]
    assert client_5["image"] == "test-linux-arm64-client-image"
    assert "deploy" not in client_5

    client_9 = docker_compose["services"]["race-client-00009"]
    assert client_9["image"] == "test-linux-arm64-client-image"
    assert client_9["environment"]["UNINSTALL_RACE"] == "yes"
    assert "deploy" in client_9

    client_11 = docker_compose["services"]["race-client-00011"]
    assert client_11["image"] == "test-linux-arm64-client-image"
    assert client_11["environment"]["UNINSTALL_RACE"] == "no"
    assert "deploy" in client_11

    server_1 = docker_compose["services"]["race-server-00001"]
    assert server_1["image"] == "test-linux-arm64-server-image"
    assert "deploy" not in server_1

    server_5 = docker_compose["services"]["race-server-00005"]
    assert server_5["image"] == "test-linux-arm64-server-image"
    assert server_5["environment"]["UNINSTALL_RACE"] == "yes"
    assert "deploy" in server_5

    server_7 = docker_compose["services"]["race-server-00007"]
    assert server_7["image"] == "test-linux-arm64-server-image"
    assert server_7["environment"]["UNINSTALL_RACE"] == "no"
    assert "deploy" in server_7


@pytest.mark.usefixtures("rib_state_path")
def test_generate_gpu_x86_64_node_docker_compose_data(complex_aws_deployment):
    docker_compose = complex_aws_deployment.generate_gpu_node_docker_compose_data(
        NodeInstanceManifest(
            # GPU clients are 9-12, 10 and 12 are bridged
            linux_gpu_clients=["race-client-00009", "race-client-00011"],
            # Include 1 co-located non-gpu client
            linux_clients=["race-client-00005"],
            # GPU servers are 5-8, 6 and 8 are bridged
            linux_gpu_servers=["race-server-00005", "race-server-00007"],
            # Include 1 co-located non-gpu server
            linux_servers=["race-server-00001"],
        ),
        "x86_64",
    )

    assert len(docker_compose["services"]) == 6

    client_5 = docker_compose["services"]["race-client-00005"]
    assert client_5["image"] == "test-linux-x86_64-client-image"
    assert "deploy" not in client_5

    client_9 = docker_compose["services"]["race-client-00009"]
    assert client_9["image"] == "test-linux-x86_64-client-image"
    assert client_9["environment"]["UNINSTALL_RACE"] == "yes"
    assert "deploy" in client_9

    client_11 = docker_compose["services"]["race-client-00011"]
    assert client_11["image"] == "test-linux-x86_64-client-image"
    assert client_11["environment"]["UNINSTALL_RACE"] == "no"
    assert "deploy" in client_11

    server_1 = docker_compose["services"]["race-server-00001"]
    assert server_1["image"] == "test-linux-x86_64-server-image"
    assert "deploy" not in server_1

    server_5 = docker_compose["services"]["race-server-00005"]
    assert server_5["image"] == "test-linux-x86_64-server-image"
    assert server_5["environment"]["UNINSTALL_RACE"] == "yes"
    assert "deploy" in server_5

    server_7 = docker_compose["services"]["race-server-00007"]
    assert server_7["image"] == "test-linux-x86_64-server-image"
    assert server_7["environment"]["UNINSTALL_RACE"] == "no"
    assert "deploy" in server_7


################################################################################
# generate_linux_node_docker_compose_data
################################################################################


@pytest.mark.usefixtures("rib_state_path")
def test_generate_linux_arm64_node_docker_compose_data(complex_aws_deployment):
    docker_compose = complex_aws_deployment.generate_linux_node_docker_compose_data(
        NodeInstanceManifest(
            # Clients 6 and 8 are bridged, 9-12 are GPU
            linux_clients=["race-client-00005", "race-client-00007"],
            # Servers 2 and 4 are bridged, 5-8 are GPU
            linux_servers=["race-server-00001", "race-server-00003"],
        ),
        "arm64",
    )

    assert len(docker_compose["services"]) == 4

    client_5 = docker_compose["services"]["race-client-00005"]
    assert client_5["image"] == "test-linux-arm64-client-image"
    assert client_5["environment"]["UNINSTALL_RACE"] == "yes"

    client_7 = docker_compose["services"]["race-client-00007"]
    assert client_7["image"] == "test-linux-arm64-client-image"
    assert client_7["environment"]["UNINSTALL_RACE"] == "no"

    server_1 = docker_compose["services"]["race-server-00001"]
    assert server_1["image"] == "test-linux-arm64-server-image"
    assert server_1["environment"]["UNINSTALL_RACE"] == "yes"

    server_3 = docker_compose["services"]["race-server-00003"]
    assert server_3["image"] == "test-linux-arm64-server-image"
    assert server_3["environment"]["UNINSTALL_RACE"] == "no"


@pytest.mark.usefixtures("rib_state_path")
def test_generate_linux_x86_64_node_docker_compose_data(complex_aws_deployment):
    docker_compose = complex_aws_deployment.generate_linux_node_docker_compose_data(
        NodeInstanceManifest(
            # Clients 6 and 8 are bridged, 9-12 are GPU
            linux_clients=["race-client-00005", "race-client-00007"],
            # Servers 2 and 4 are bridged, 5-8 are GPU
            linux_servers=["race-server-00001", "race-server-00003"],
        ),
        "x86_64",
    )

    assert len(docker_compose["services"]) == 4

    client_5 = docker_compose["services"]["race-client-00005"]
    assert client_5["image"] == "test-linux-x86_64-client-image"
    assert client_5["environment"]["UNINSTALL_RACE"] == "yes"

    client_7 = docker_compose["services"]["race-client-00007"]
    assert client_7["image"] == "test-linux-x86_64-client-image"
    assert client_7["environment"]["UNINSTALL_RACE"] == "no"

    server_1 = docker_compose["services"]["race-server-00001"]
    assert server_1["image"] == "test-linux-x86_64-server-image"
    assert server_1["environment"]["UNINSTALL_RACE"] == "yes"

    server_3 = docker_compose["services"]["race-server-00003"]
    assert server_3["image"] == "test-linux-x86_64-server-image"
    assert server_3["environment"]["UNINSTALL_RACE"] == "no"


def test_get_race_image_returns_correct_race_image(example_3x3_aws_deployment_obj):
    deployment = example_3x3_aws_deployment_obj
    assert (
        deployment.get_race_image("android", "x86_64", "client")
        == deployment.android_x86_64_client_image
    )
    assert (
        deployment.get_race_image("android", "arm64", "client")
        == deployment.android_arm64_v8a_client_image
    )
    assert (
        deployment.get_race_image("linux", "x86_64", "client")
        == deployment.linux_x86_64_client_image
    )
    assert (
        deployment.get_race_image("linux", "x86_64", "server")
        == deployment.linux_x86_64_server_image
    )
    assert (
        deployment.get_race_image("linux", "arm64", "client")
        == deployment.linux_arm64_v8a_client_image
    )
    assert (
        deployment.get_race_image("linux", "arm64", "server")
        == deployment.linux_arm64_v8a_server_image
    )


def test_get_race_image_raises_on_error(example_3x3_aws_deployment_obj):
    deployment = example_3x3_aws_deployment_obj
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("android", "x86_64", "clientt")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("android", "x86_64", "server")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("android", "arm64", "server")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("linux", "x86_64", "serverr")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("linux", "x86_64", "clientt")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("linux", "x86_6", "client")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("linux", "arm64", "clientt")
    with pytest.raises(KeyError) as err:
        deployment.get_race_image("some", "fake", "values")

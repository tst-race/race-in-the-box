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
        Test File for rib_local_deployment.py
"""

# Python Library Imports
import json
import logging
from pathlib import Path
from typing import Dict, Any
import pytest
import os
import tempfile
import shutil
from unittest import mock
from unittest.mock import MagicMock, create_autospec
from mock import patch

# Local Library Imports
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.rib_deployment_config import (
    DeploymentMetadata,
    LocalDeploymentConfig,
)
from rib.deployment.rib_local_deployment import RibLocalDeployment
from rib.utils import (
    error_utils,
    plugin_utils,
    race_node_utils,
)
from .mock_deployment_configs.local_3x3_default_config import (
    local_3x3_default_config_dict,
)


###
# Mocks
###


###
# Data Fixtures
###


@pytest.fixture()
def example_3x3_range_config() -> Dict[str, Any]:
    """
    Purpose:
        Fixture of an Example Range Config.

        Configured with 3 clients and 3 servers.
    Args:
        N/A
    Return:
        example_3x3_range_config_obj: range config
    """

    example_3x3_range_config = None

    with open(
        f"{os.path.dirname(os.path.realpath(__file__))}/"
        "mock_range_configs/3x3_stubs.json",
        "r",
    ) as read_config_obj:
        example_3x3_range_config = json.loads(read_config_obj.read())

    return example_3x3_range_config


@pytest.fixture()
def example_3x3_local_deployment_config() -> LocalDeploymentConfig:
    """3x3 local deployment config"""
    return LocalDeploymentConfig.parse_obj(local_3x3_default_config_dict)


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
def example_3x3_local_deployment_temp_filesystem_obj(
    example_3x3_local_deployment_config,
    deployment_metadata,
) -> RibLocalDeployment:
    """
    Purpose:
        Fixture of an Example Local RiB Deployment with a temp filesystem.

        Configured with 3 clients and 3 servers, this fixture can be used for most tests
        but is meant specifically for tests related to copying/moving files
    Args:
        N/A
    Return:
        example_3x3_local_deployment_temp_filesystem_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    # Copy the test files
    src = os.path.join(os.path.dirname(os.path.realpath(__file__)), "rib_state_path")
    temp_docker_rib_state_path = os.path.join(
        tempfile.gettempdir(), "rib-unit-test-state-path"
    )
    shutil.rmtree(temp_docker_rib_state_path, ignore_errors=True)
    shutil.copytree(src, temp_docker_rib_state_path)

    # Change global paths to temp path
    original_plugins_cache_dir = plugin_utils.CACHE_DIR
    plugin_utils.CACHE_DIR = f"{temp_docker_rib_state_path}/.race/rib/plugins-cache/"

    # Change deployment dirs to temp path
    original_mode_dir = RibLocalDeployment.pathsClass.dirs["mode"]
    RibLocalDeployment.pathsClass.dirs[
        "mode"
    ] = f"{temp_docker_rib_state_path}/deployments/local"
    orig_docker_rib_state_path = RibLocalDeployment.rib_config.DOCKER_RIB_STATE_PATH
    for key, path in RibLocalDeployment.rib_config.RIB_PATHS["docker"].items():
        if type(path) is str and orig_docker_rib_state_path in path:
            RibLocalDeployment.rib_config.RIB_PATHS["docker"][key] = path.replace(
                orig_docker_rib_state_path, temp_docker_rib_state_path
            )

    deployment = RibLocalDeployment(
        config=example_3x3_local_deployment_config,
        metadata=deployment_metadata,
    )
    deployment.paths.dirs["templates"] = f"{temp_docker_rib_state_path}/templates"
    deployment._race_node_interface = create_autospec(race_node_utils.RaceNodeInterface)

    # Make temp dirs
    os.makedirs(RibLocalDeployment.pathsClass.dirs["mode"])
    deployment.create_directories()

    # Execute test
    yield deployment

    # Reset
    shutil.rmtree(temp_docker_rib_state_path, ignore_errors=True)
    plugin_utils.CACHE_DIR = original_plugins_cache_dir
    RibLocalDeployment.pathsClass.dirs["mode"] = original_mode_dir
    for key, path in RibLocalDeployment.rib_config.RIB_PATHS["docker"].items():
        if type(path) is str and temp_docker_rib_state_path in path:
            RibLocalDeployment.rib_config.RIB_PATHS["docker"][key] = path.replace(
                temp_docker_rib_state_path, orig_docker_rib_state_path
            )


@pytest.fixture()
def example_3x3_local_deployment_obj(
    example_3x3_local_deployment_config,
    deployment_metadata,
) -> RibLocalDeployment:
    """
    Purpose:
        Fixture of an Example Local RiB Deployment.

        Configured with 3 clients and 3 servers. This is the "default" config
        we use locally for testing in most cases
    Args:
        N/A
    Return:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    # Make sure deployment dirs resolve to root user, regardless of current user
    # when tests are run
    fixed_docker_rib_state_path = "/root/.race/rib"
    RibLocalDeployment.pathsClass.dirs[
        "mode"
    ] = f"{fixed_docker_rib_state_path}/deployments/local"
    orig_docker_rib_state_path = RibLocalDeployment.rib_config.DOCKER_RIB_STATE_PATH
    for key, path in RibLocalDeployment.rib_config.RIB_PATHS["docker"].items():
        if type(path) is str and orig_docker_rib_state_path in path:
            RibLocalDeployment.rib_config.RIB_PATHS["docker"][key] = path.replace(
                orig_docker_rib_state_path, fixed_docker_rib_state_path
            )

    deployment = RibLocalDeployment(
        config=example_3x3_local_deployment_config,
        metadata=deployment_metadata,
    )
    deployment.status.verify_deployment_is_active = MagicMock()
    deployment._race_node_interface = create_autospec(race_node_utils.RaceNodeInterface)
    return deployment


###
# Test Local Deployment Methods
###


################################################################################
# __init__
################################################################################


def test___init__(example_3x3_local_deployment_obj):
    """
    Purpose:
        Test the send_message method for local Deployments
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    # Assert Property Methods for Configs and Dirs
    assert example_3x3_local_deployment_obj.config
    assert example_3x3_local_deployment_obj.metadata
    # TODO More Testing


################################################################################
# validate_sender_recipient
################################################################################


def test_validate_sender_recipient_non_existant_recipient(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        Test that `deployment.validate_sender_recipient` throws the correct
        exception and message when a recipient does not exist
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307, match=r".*Recipient is not a valid node.*"):
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-client-00001", "race-client-00004", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_non_existant_sender(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        Test that `deployment.validate_sender_recipient` throws the correct
        exception and message when a sender does not exist
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307, match=r".*Sender is not a valid node.*"):
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-client-00004", "race-client-00001", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_client_to_client_non_comms(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        sending from client to client fails with is-network_manager-bypass = True
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307) as error:
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-client-00001", "race-client-00002", is_network_manager_bypass=True
        )


def test_validate_sender_recipient_client_to_server_comms(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        sending from client to server fails with is-network_manager-bypass = False
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307) as error:
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-client-00001", "race-server-00001", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_server_to_server_comms(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        sending from client to server fails with is-network_manager-bypass = False
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307) as error:
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-server-00001", "race-server-00002", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_server_to_client_comms(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        sending from client to server fails with is-network_manager-bypass = False
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307) as error:
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-server-00001", "race-client-00001", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_self(example_3x3_local_deployment_obj):
    """
    Purpose:
        Test that `deployment.validate_sender_recipient` throws the correct
        exception and message when sending to self
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB307, match=r".*Cannot send to self.*"):
        example_3x3_local_deployment_obj.validate_sender_recipient(
            "race-client-00001", "race-client-00001", is_network_manager_bypass=False
        )


################################################################################
# get_recipient_sender_mapping
################################################################################


# TODO


################################################################################
# get_available_recipients_by_sender
################################################################################


def test_get_available_recipients_by_sender_client_comms_mode(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        Test the `deployment.get_available_recipients_by_sender` works
            with a client in is-network_manager-bypass
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    available_recipients = (
        example_3x3_local_deployment_obj.get_available_recipients_by_sender(
            "race-client-00001", is_network_manager_bypass=True
        )
    )

    assert sorted(
        ["race-server-00001", "race-server-00002", "race-server-00003"]
    ) == sorted(available_recipients)


def test_get_available_recipients_by_sender_client(example_3x3_local_deployment_obj):
    """
    Purpose:
        Test the `deployment.get_available_recipients_by_sender` works
            with a client (not is-network_manager-bypass)
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    available_recipients = (
        example_3x3_local_deployment_obj.get_available_recipients_by_sender(
            "race-client-00001", is_network_manager_bypass=False
        )
    )

    assert sorted(["race-client-00002", "race-client-00003"]) == sorted(
        available_recipients
    )


def test_get_available_recipients_by_sender_server_comms_mode(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        Test the `deployment.get_available_recipients_by_sender` works
            with a server in is-network_manager-bypass
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    available_recipients = (
        example_3x3_local_deployment_obj.get_available_recipients_by_sender(
            "race-server-00001", is_network_manager_bypass=True
        )
    )

    assert sorted(
        [
            "race-client-00001",
            "race-client-00002",
            "race-client-00003",
            "race-server-00002",
            "race-server-00003",
        ]
    ) == sorted(available_recipients)


def test_get_available_recipients_by_sender_server(example_3x3_local_deployment_obj):
    """
    Purpose:
        Test the `deployment.get_available_recipients_by_sender` works
            with a server (not is-network_manager-bypass)
    Args:
        example_3x3_local_deployment_obj (RibLocalDeployment Obj): Example configured
            3x3 local deployment for testing
    """

    available_recipients = (
        example_3x3_local_deployment_obj.get_available_recipients_by_sender(
            "race-server-00001", is_network_manager_bypass=False
        )
    )

    assert [] == available_recipients


################################################################################
# generate_docker_compose_data
################################################################################


def test_generate_docker_compose_data_has_expected_keys(
    example_3x3_local_deployment_obj,
) -> None:
    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = f"{rb_path}/../../deployments/local"
    example_3x3_local_deployment_obj.paths.dirs[
        "templates"
    ] = f"{artifact_path}/deployments/local/templates"

    docker_compose_data = (
        example_3x3_local_deployment_obj.generate_docker_compose_data()
    )

    assert "networks" in docker_compose_data
    assert "services" in docker_compose_data
    assert "version" in docker_compose_data
    assert "x-logging" in docker_compose_data


def test_generate_docker_compose_data_includes_all_nodes(
    example_3x3_local_deployment_obj,
) -> None:
    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = \
    #     f"{rb_path}/../../deployments/local"
    example_3x3_local_deployment_obj.paths.dirs[
        "templates"
    ] = f"{artifact_path}/deployments/local/templates"
    docker_compose_data = (
        example_3x3_local_deployment_obj.generate_docker_compose_data()
    )

    for persona in local_3x3_default_config_dict["nodes"].keys():
        assert persona in docker_compose_data["services"].keys()


def test_generate_docker_compose_data_includes_deployment_name_as_label_in_all_services(
    example_3x3_local_deployment_config,
    deployment_metadata,
) -> None:
    """Check that each service in the generated docker compose has a label containing
    the deployment name.
    """

    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    deployment = RibLocalDeployment(
        config=example_3x3_local_deployment_config,
        metadata=deployment_metadata,
    )

    # Hack to set this path of the rib state directory on the host.
    deployment.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = f"{rb_path}/../../deployments/local"
    deployment.paths.dirs["templates"] = f"{artifact_path}/deployments/local/templates"

    docker_compose_data = deployment.generate_docker_compose_data()

    LABELS_KEY = "labels"
    for service_name, service in docker_compose_data["services"].items():
        assert LABELS_KEY in service.keys(), f"Failed for {service_name}"
        assert (
            "${DEPLOYMENT_NAME}"
            == service[LABELS_KEY][
                RibLocalDeployment.DEPLOYMENT_NAME_CONTAINER_LABEL_KEY
            ]
        ), f"Failed for {service_name}"


def test_generate_docker_compose_data_sets_volume_mounts_for_nodes_no_plugins(
    example_3x3_local_deployment_obj,
) -> None:
    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = f"{rb_path}/../../deployments/local"
    example_3x3_local_deployment_obj.paths.dirs[
        "templates"
    ] = f"{artifact_path}/deployments/local/templates"

    docker_compose_data = example_3x3_local_deployment_obj.generate_docker_compose_data(
        mount_plugins=False
    )

    for service_name, service in docker_compose_data["services"].items():
        # Ignore services that are not nodes.
        if not service_name.startswith("race-server-") and not service_name.startswith(
            "race-client-0000"
        ):
            continue

        NUM_EXPECTED_VOLUMES = 3
        node_type = "server" if "server" in service_name else "client"
        assert (
            len(service["volumes"]) == NUM_EXPECTED_VOLUMES
        ), f"Expected {NUM_EXPECTED_VOLUMES} volume mounts for {node_type} {service_name}, but found {len(service['volumes'])}. Did you add/remove a volume? If so, please update this test value."
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/logs/{service_name}/:/log"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/artifact-manager/:/usr/local/lib/race/artifact-manager"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/core:/usr/local/lib/race/core"
            in service["volumes"]
        )


def test_generate_docker_compose_data_sets_volume_mounts_for_nodes_with_plugins(
    example_3x3_local_deployment_obj,
) -> None:
    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = f"{rb_path}/../../deployments/local"
    example_3x3_local_deployment_obj.paths.dirs[
        "templates"
    ] = f"{artifact_path}/deployments/local/templates"

    docker_compose_data = example_3x3_local_deployment_obj.generate_docker_compose_data(
        mount_plugins=True
    )

    for service_name, service in docker_compose_data["services"].items():
        # Ignore services that are not nodes.
        if not service_name.startswith("race-server-") and not service_name.startswith(
            "race-client-0000"
        ):
            continue

        NUM_EXPECTED_VOLUMES = 5
        node_type = "server" if "server" in service_name else "client"
        assert (
            len(service["volumes"]) == NUM_EXPECTED_VOLUMES
        ), f"Expected {NUM_EXPECTED_VOLUMES} volume mounts for {node_type} {service_name}, but found {len(service['volumes'])}. Did you add/remove a volume? If so, please update this test value."
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/logs/{service_name}/:/log"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/network-manager/:/usr/local/lib/race/network-manager"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/comms/:/usr/local/lib/race/comms"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/artifact-manager/:/usr/local/lib/race/artifact-manager"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/core:/usr/local/lib/race/core"
            in service["volumes"]
        )


def test_generate_docker_compose_data_sets_volume_mount_for_tmpfs(
    example_3x3_local_deployment_obj,
) -> None:
    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = f"{rb_path}/../../deployments/local"
    example_3x3_local_deployment_obj.paths.dirs[
        "templates"
    ] = f"{artifact_path}/deployments/local/templates"

    # Enable tmpfs.
    TMPFS_SIZE = 1
    example_3x3_local_deployment_obj.config["tmpfs_size"] = TMPFS_SIZE
    EXPECTED_TMPFS_VOLUME_MOUNT = {
        "type": "tmpfs",
        "target": "/tmpfs",
        "tmpfs": {"size": TMPFS_SIZE},
    }

    docker_compose_data = (
        example_3x3_local_deployment_obj.generate_docker_compose_data()
    )

    for service_name, service in docker_compose_data["services"].items():
        # Ignore services that are not nodes.
        if not service_name.startswith("race-server-") and not service_name.startswith(
            "race-client-0000"
        ):
            continue

        NUM_EXPECTED_VOLUMES = 4
        node_type = "server" if "server" in service_name else "client"
        assert (
            len(service["volumes"]) == NUM_EXPECTED_VOLUMES
        ), f"Expected {NUM_EXPECTED_VOLUMES} volume mounts for {node_type} {service_name}, but found {len(service['volumes'])}. Did you add/remove a volume? If so, please update this test value."
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/logs/{service_name}/:/log"
            in service["volumes"]
        )
        assert (
            f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-x86_64-{node_type}/core:/usr/local/lib/race/core"
            in service["volumes"]
        )
        assert EXPECTED_TMPFS_VOLUME_MOUNT in service["volumes"]


def test_generate_docker_compose_data_creates_services_for_android_clients(
    example_3x3_local_deployment_obj,
) -> None:
    artifact_path = f"{os.path.dirname(os.path.realpath(__file__))}/../../artifacts"

    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["host"][
        "rib_state"
    ] = "/my/fake/host/rib/state/path"

    # Hack to point to the deployment template files in this repo.
    # TODO: can these templates be in code instead of files?
    # example_3x3_local_deployment_obj.paths.dirs["mode"] = f"{rb_path}/../../deployments/local"
    example_3x3_local_deployment_obj.paths.dirs[
        "templates"
    ] = f"{artifact_path}/deployments/local/templates"

    example_3x3_local_deployment_obj.config["nodes"]["race-client-00001"][
        "platform"
    ] = "android"
    example_3x3_local_deployment_obj.config["nodes"]["race-client-00002"][
        "platform"
    ] = "android"

    docker_compose_data = (
        example_3x3_local_deployment_obj.generate_docker_compose_data()
    )

    client1 = docker_compose_data["services"]["race-client-00001"]
    assert len(client1["ports"]) == 1
    assert "35001:5901" in client1["ports"]
    assert "devices" not in client1
    assert "off" == client1["environment"]["HW_ACCEL"]

    client2 = docker_compose_data["services"]["race-client-00002"]
    assert len(client2["ports"]) == 1
    assert "35002:5901" in client2["ports"]
    assert "devices" not in client2
    assert "off" == client2["environment"]["HW_ACCEL"]

    client3 = docker_compose_data["services"]["race-client-00003"]
    assert "devices" not in client3
    assert "ports" not in client3
    assert "devices" not in client3
    assert "HW_ACCEL" not in client3["environment"]

    example_3x3_local_deployment_obj.config["android_container_acceleration"] = True
    docker_compose_data = (
        example_3x3_local_deployment_obj.generate_docker_compose_data()
    )

    client1 = docker_compose_data["services"]["race-client-00001"]
    assert len(client1["ports"]) == 1
    assert "35001:5901" in client1["ports"]
    assert "/dev/kvm:/dev/kvm" in client1["devices"]
    assert "on" == client1["environment"]["HW_ACCEL"]

    client2 = docker_compose_data["services"]["race-client-00002"]
    assert len(client2["ports"]) == 1
    assert "35002:5901" in client2["ports"]
    assert "/dev/kvm:/dev/kvm" in client2["devices"]
    assert "on" == client2["environment"]["HW_ACCEL"]

    client3 = docker_compose_data["services"]["race-client-00003"]
    assert "devices" not in client3
    assert "ports" not in client3
    assert "devices" not in client3
    assert "HW_ACCEL" not in client3["environment"]


################################################################################
# _generate_docker_compose_env_vars
################################################################################


def test__generate_docker_compose_env_vars(example_3x3_local_deployment_obj):
    # Hack to set this path of the rib state directory on the host.
    example_3x3_local_deployment_obj.rib_config.RIB_PATHS["portable"][
        "rib_state"
    ] = "${HOST_RIB_STATE_PATH}/"

    data = example_3x3_local_deployment_obj._generate_docker_compose_env_vars()

    RIB_STATE_PATH = example_3x3_local_deployment_obj.rib_config.RIB_PATHS["portable"][
        "rib_state"
    ]
    DEPLOYMENT_HOST_DIR = f"{RIB_STATE_PATH}/deployments/local/{example_3x3_local_deployment_obj.config['name']}"

    assert type(data) is dict
    assert data["DEPLOYMENT_NAME"] == example_3x3_local_deployment_obj.config["name"]


################################################################################
# validate_global_configs
################################################################################


def test_validate_global_configs_raises_when_missing_directory(
    example_3x3_local_deployment_obj: RibLocalDeployment,
) -> None:
    """
    Purpose:
        Verify that validate_global_configs raises an error when directory does not exist
    Args:
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    with pytest.raises(error_utils.RIB329, match=r".*a/config/directory is missing.*"):
        example_3x3_local_deployment_obj.validate_global_configs("a/config/directory")


def test_validate_global_configs_raises_when_missing_file(
    example_3x3_local_deployment_obj: RibLocalDeployment,
) -> None:
    """
    Purpose:
        Verify that validate_global_configs raises an error when directory is missing a required file
    Args:
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    with tempfile.TemporaryDirectory() as configs_dir:
        example_3x3_local_deployment_obj.paths.dirs["race_configs"] = configs_dir
        global_configs_dir_path = Path(configs_dir, "global")
        global_configs_dir_path.mkdir()
        global_android_configs_dir_path = Path(global_configs_dir_path, "android")
        global_android_configs_dir_path.mkdir()
        global_linux_configs_dir_path = Path(global_configs_dir_path, "linux")
        global_linux_configs_dir_path.mkdir()

        Path(global_android_configs_dir_path, "race.json").touch()
        # Path(global_linux_configs_dir_path, "race.json").touch()
        with pytest.raises(error_utils.RIB329, match=r".*: linux/race\.json\n"):
            example_3x3_local_deployment_obj.validate_global_configs(
                global_configs_dir_path
            )

    with tempfile.TemporaryDirectory() as configs_dir:
        example_3x3_local_deployment_obj.paths.dirs["race_configs"] = configs_dir
        global_configs_dir_path = Path(configs_dir, "global")
        global_configs_dir_path.mkdir()
        global_android_configs_dir_path = Path(global_configs_dir_path, "android")
        global_android_configs_dir_path.mkdir()
        global_linux_configs_dir_path = Path(global_configs_dir_path, "linux")
        global_linux_configs_dir_path.mkdir()

        # Path(global_android_configs_dir_path, "race.json").touch()
        Path(global_linux_configs_dir_path, "race.json").touch()
        with pytest.raises(error_utils.RIB329, match=r".*: android/race\.json\n"):
            example_3x3_local_deployment_obj.validate_global_configs(
                global_configs_dir_path
            )


def test_validate_global_configs_raises_when_invalid_json(
    example_3x3_local_deployment_obj: RibLocalDeployment,
) -> None:
    """
    Purpose:
        Verify that validate_global_configs raises an error a JSON file contains invalid content
    Args:
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """
    with tempfile.TemporaryDirectory() as configs_dir:
        example_3x3_local_deployment_obj.paths.dirs["race_configs"] = configs_dir
        global_configs_dir_path = Path(configs_dir, "global")
        global_configs_dir_path.mkdir()
        global_android_configs_dir_path = Path(global_configs_dir_path, "android")
        global_android_configs_dir_path.mkdir()
        global_linux_configs_dir_path = Path(global_configs_dir_path, "linux")
        global_linux_configs_dir_path.mkdir()

        with open(Path(global_android_configs_dir_path, "race.json"), "w") as out:
            out.write(
                """
            {
                "plugins": [],
            },
            """
            )
        with open(Path(global_linux_configs_dir_path, "race.json"), "w") as out:
            out.write(
                """
            {
                why: "doesn't json actually use JavaScript notation?",
            },
            """
            )
        with pytest.raises(error_utils.RIB006, match=r"race\.json"):
            example_3x3_local_deployment_obj.validate_global_configs(
                global_configs_dir_path
            )

    with tempfile.TemporaryDirectory() as configs_dir:
        example_3x3_local_deployment_obj.paths.dirs["race_configs"] = configs_dir
        global_configs_dir_path = Path(configs_dir, "global")
        global_configs_dir_path.mkdir()
        global_android_configs_dir_path = Path(global_configs_dir_path, "android")
        global_android_configs_dir_path.mkdir()
        global_linux_configs_dir_path = Path(global_configs_dir_path, "linux")
        global_linux_configs_dir_path.mkdir()

        with open(Path(global_android_configs_dir_path, "race.json"), "w") as out:
            out.write(
                """
            {
                why: "doesn't json actually use JavaScript notation?",
            },
            """
            )
        with open(Path(global_linux_configs_dir_path, "race.json"), "w") as out:
            out.write(
                """
            {
                "plugins": [],
            },
            """
            )
        with pytest.raises(error_utils.RIB006, match=r"race\.json"):
            example_3x3_local_deployment_obj.validate_global_configs(
                global_configs_dir_path
            )


def test_validate_global_configs_succeeds_when_all_files_exist(
    example_3x3_local_deployment_obj: RibLocalDeployment,
) -> None:
    """
    Purpose:
        Verify that validate_global_configs succeeds when directory contains all required files
    Args:
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    with tempfile.TemporaryDirectory() as configs_dir:
        example_3x3_local_deployment_obj.paths.dirs["race_configs"] = configs_dir
        global_configs_dir_path = Path(configs_dir, "global")
        global_configs_dir_path.mkdir()
        global_android_configs_dir_path = Path(global_configs_dir_path, "android")
        global_android_configs_dir_path.mkdir()
        global_linux_configs_dir_path = Path(global_configs_dir_path, "linux")
        global_linux_configs_dir_path.mkdir()

        with open(Path(global_android_configs_dir_path, "race.json"), "w") as out:
            out.write('{"plugins": []}')
        with open(
            Path(global_android_configs_dir_path, "jaeger-config.yml"), "w"
        ) as out:
            out.write("key: value\n")
        with open(Path(global_linux_configs_dir_path, "race.json"), "w") as out:
            out.write('{"plugins": []}')
        with open(Path(global_linux_configs_dir_path, "jaeger-config.yml"), "w") as out:
            out.write("key: value\n")
        example_3x3_local_deployment_obj.validate_global_configs(
            global_configs_dir_path,
            require_global_config_plugins=False,
        )


def os_is_dir_side_effect_func(value):
    # if the path ends with the plugin name, this is a python plugin path
    # for 1.1.0 we're not unit testing python path. This should be added
    path = value.split("/")
    return path[-1] != "plugin-name"


@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment.copy_kit",
)
@patch("rib.utils.plugin_utils.download_race_core")
@patch("rib.utils.plugin_utils.download_kit")
@patch("os.path.isdir", MagicMock(return_value=True))
@patch("rib.utils.general_utils.remove_dir_file", MagicMock())
@patch("os.mkdir", MagicMock())
def test_get_plugins_copies_apps_into_deployment_when_bootstrapping(
    mock_get_plugin: MagicMock,
    mock_download_race_core: MagicMock,
    mock_download_kit: MagicMock,
    example_3x3_local_deployment_obj: RibLocalDeployment,
):
    example_3x3_local_deployment_obj.config["nodes"]["race-server-00001"][
        "genesis"
    ] = False

    example_3x3_local_deployment_obj.config.comms_kits = []
    example_3x3_local_deployment_obj.config.artifact_manager_kits = []

    example_registry_app = plugin_utils.KitConfig(
        name="RegistryApp",
        kit_type=plugin_utils.KitType.APP,
        source=plugin_utils.KitSource(
            raw="core=registry-app",
            source_type=plugin_utils.KitSourceType.CORE,
            asset="registry-app",
        ),
    )
    example_3x3_local_deployment_obj.config.registry_app = example_registry_app

    example_3x3_local_deployment_obj.get_plugins(plugin_utils.CacheStrategy.ALWAYS)

    assert mock_download_race_core.call_count == 1

    # 1 call for the network manager, 0 comms, 0 AMP, 0 Android App, 1 Linux Test App, 1 Registry App, 1 Node Daemon
    assert mock_download_kit.call_count == 4
    assert mock_get_plugin.call_count == 4


################################################################################
# Automatic Config Generation
################################################################################


@patch("rib.utils.subprocess_utils.run")
@patch("rib.utils.general_utils.write_data_to_file")
@patch("os.mkdir", MagicMock())
def test_generate_plugin_or_channel_configs_complete_with_minimum_loop(
    mock_write_data_to_file,
    mock_subprocess,
    example_3x3_local_deployment_obj,
    example_3x3_range_config,
) -> int:
    """
    Purpose:
        Test generate_plugin_or_channel_configs calls the network manager config gen, then calls config gen for each channel and then confirms again with network manager
    Args
        mock_load_file_into_memory: mocked call which is used to get status of config generation scripts
        mock_write_data_to_file: mock call to write_data_to_file which does nothing
        mock_subprocess: mocked subprocess call for testing
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    class MockGeneralUtils:
        first_call = True

        # return incomplete the first time network manager config gen is called but complete the second time
        def return_complete_if_fullfilled_requests_provided(*args, data_format):
            if "network-manager-config-gen-status.json" in args[0]:
                if not MockGeneralUtils.first_call:
                    return {"status": "complete", "reason": "success"}
                else:
                    MockGeneralUtils.first_call = False

            if "race-config.json" in args[0]:
                return example_3x3_range_config

            return {"status": "incomplete"}

    with patch(
        "rib.utils.general_utils.load_file_into_memory",
        side_effect=MockGeneralUtils.return_complete_if_fullfilled_requests_provided,
    ):
        RibDeployment.merge_fulfilled_requests = MagicMock()
        RibDeployment.get_deployment_channels_list = MagicMock()
        example_3x3_local_deployment_obj.generate_plugin_or_channel_configs(
            skip_config_tar=True
        )

    # Verify Calls
    assert mock_subprocess.call_count == 5


@patch("rib.utils.subprocess_utils.run")
def test_run_network_manager_config_gen_no_optional_flags(
    mock_subprocess, example_3x3_local_deployment_obj
) -> int:
    """
    Purpose:
        Test run_network_manager_config_gen calls the network manager config gen without any optional flag
    Args
        mock_subprocess: mocked subprocess call for testing
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    example_3x3_local_deployment_obj.run_network_manager_config_gen(local=True)

    # Expectation
    deployment_dir = (
        "/root/.race/rib/deployments/local/example_3x3_local_deployment_obj"
    )
    cmd = [
        "bash",
        f"{deployment_dir}/plugins/MockPluginNMStub/config-generator/generate_configs.sh",
        f"--range={deployment_dir}/configs/race-config.json",
        f"--config-dir={deployment_dir}/configs/network-manager/MockPluginNMStub",
        "--overwrite",
        f"--channel-list={deployment_dir}/configs/channel_list.json",
        "--local",
    ]
    expected_call = mock.call(
        " ".join(cmd),
        check=True,
        shell=True,
        stdout_level=logging.DEBUG,
        timeout=300,
    )

    # Verify Calls
    assert expected_call in mock_subprocess.call_args_list


@patch("rib.utils.subprocess_utils.run")
def test_run_network_manager_config_gen_with_fulfilled_requests_flag(
    mock_subprocess, example_3x3_local_deployment_obj
) -> int:
    """
    Purpose:
        Test run_network_manager_config_gen calls the network manager config gen with fulfilled_requests_flag
    Args
        mock_subprocess: mocked subprocess call for testing
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    fulfilled_requests_flag = "/path/to/fulfilled/request.json"
    example_3x3_local_deployment_obj.run_network_manager_config_gen(
        local=True, fulfilled_requests_flag=fulfilled_requests_flag
    )

    # Expectation
    deployment_dir = (
        "/root/.race/rib/deployments/local/example_3x3_local_deployment_obj"
    )
    cmd = [
        "bash",
        f"{deployment_dir}/plugins/MockPluginNMStub/config-generator/generate_configs.sh",
        f"--range={deployment_dir}/configs/race-config.json",
        f"--config-dir={deployment_dir}/configs/network-manager/MockPluginNMStub",
        "--overwrite",
        f"--channel-list={deployment_dir}/configs/channel_list.json",
        fulfilled_requests_flag,
        "--local",
    ]
    expected_call = mock.call(
        " ".join(cmd),
        check=True,
        shell=True,
        stdout_level=logging.DEBUG,
        timeout=300,
    )

    # Verify Calls
    assert expected_call in mock_subprocess.call_args_list


@patch("rib.utils.subprocess_utils.run")
def test_run_network_manager_config_gen_with_custom_network_manager_args(
    mock_subprocess, example_3x3_local_deployment_obj
) -> int:
    """
    Purpose:
        Test run_network_manager_config_gen calls the network manager config gen with network_manager_custom_args
    Args
        mock_subprocess: mocked subprocess call for testing
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    network_manager_custom_args = "--custom-arg-1=value1 --custom-arg-2=value2"
    example_3x3_local_deployment_obj.run_network_manager_config_gen(
        local=True, network_manager_custom_args=network_manager_custom_args
    )

    # Expectation
    deployment_dir = (
        "/root/.race/rib/deployments/local/example_3x3_local_deployment_obj"
    )
    cmd = [
        "bash",
        f"{deployment_dir}/plugins/MockPluginNMStub/config-generator/generate_configs.sh",
        f"--range={deployment_dir}/configs/race-config.json",
        f"--config-dir={deployment_dir}/configs/network-manager/MockPluginNMStub",
        "--overwrite",
        f"--channel-list={deployment_dir}/configs/channel_list.json",
        "--custom-arg-1=value1",
        "--custom-arg-2=value2",
        "--local",
    ]
    expected_call = mock.call(
        " ".join(cmd),
        check=True,
        shell=True,
        stdout_level=logging.DEBUG,
        timeout=300,
    )

    # Verify Calls
    assert expected_call in mock_subprocess.call_args_list


@patch("rib.utils.subprocess_utils.run")
def test_run_comms_config_gen(mock_subprocess, example_3x3_local_deployment_obj) -> int:
    """
    Purpose:
        Test run_comms_config_gen calls the comms config gen
    Args
        mock_subprocess: mocked subprocess call for testing
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    deployment_dir = (
        "/root/.race/rib/deployments/local/example_3x3_local_deployment_obj"
    )

    for channel in example_3x3_local_deployment_obj.config.comms_channels:
        example_3x3_local_deployment_obj.run_comms_config_gen(
            local=True, channel=channel
        )

        # Expectation
        cmd = [
            "bash",
            f"{deployment_dir}/plugins/MockPluginCommsTwoSixStub/channels/{channel.name}/generate_configs.sh",
            f"--range={deployment_dir}/configs/race-config.json",
            f"--config-dir={deployment_dir}/configs/comms/MockPluginCommsTwoSixStub/{channel.name}",
            "--overwrite",
            f"--network-manager-request={deployment_dir}/configs/network-manager/MockPluginNMStub/network-manager-request.json",
            "--local",
        ]
        expected_call = mock.call(
            " ".join(cmd),
            check=True,
            shell=True,
            stdout_level=logging.DEBUG,
            timeout=300,
        )

        # Verify Calls
        assert expected_call in mock_subprocess.call_args_list


@patch("rib.utils.subprocess_utils.run")
def test_run_comms_config_gen_custom_args(
    mock_subprocess, example_3x3_local_deployment_obj
) -> int:
    """
    Purpose:
        Test run_comms_config_gen calls the comms config gen with the proper custom args specified
    Args
        mock_subprocess: mocked subprocess call for testing
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    deployment_dir = (
        "/root/.race/rib/deployments/local/example_3x3_local_deployment_obj"
    )

    comms_custom_args_map = {
        "mockTwoSixDirectCpp": "--custom-arg-1=custom-value-1 --custom-arg-2=custom-value-2",
        "mockTwoSixIndirectCpp": "--custom-arg-3='custom value-3' --custom-arg-4=custom-value-4",
    }
    first_channel = example_3x3_local_deployment_obj.config.comms_channels[0]
    example_3x3_local_deployment_obj.run_comms_config_gen(
        local=True, channel=first_channel, comms_custom_args_map=comms_custom_args_map
    )

    # Expectation
    cmd = [
        "bash",
        f"{deployment_dir}/plugins/MockPluginCommsTwoSixStub/channels/mockTwoSixDirectCpp/generate_configs.sh",
        f"--range={deployment_dir}/configs/race-config.json",
        f"--config-dir={deployment_dir}/configs/comms/MockPluginCommsTwoSixStub/mockTwoSixDirectCpp",
        "--overwrite",
        f"--network-manager-request={deployment_dir}/configs/network-manager/MockPluginNMStub/network-manager-request.json",
        "--local",
        "--custom-arg-1=custom-value-1",
        "--custom-arg-2=custom-value-2",
    ]
    expected_call = mock.call(
        " ".join(cmd),
        check=True,
        shell=True,
        stdout_level=logging.DEBUG,
        timeout=300,
    )

    # Verify Calls
    assert expected_call in mock_subprocess.call_args_list

    second_channel = example_3x3_local_deployment_obj.config.comms_channels[1]
    example_3x3_local_deployment_obj.run_comms_config_gen(
        local=True, channel=second_channel, comms_custom_args_map=comms_custom_args_map
    )

    # Expectation
    cmd = [
        "bash",
        f"{deployment_dir}/plugins/MockPluginCommsTwoSixStub/channels/mockTwoSixIndirectCpp/generate_configs.sh",
        f"--range={deployment_dir}/configs/race-config.json",
        f"--config-dir={deployment_dir}/configs/comms/MockPluginCommsTwoSixStub/mockTwoSixIndirectCpp",
        "--overwrite",
        f"--network-manager-request={deployment_dir}/configs/network-manager/MockPluginNMStub/network-manager-request.json",
        "--local",
        "--custom-arg-3='custom value-3'",
        "--custom-arg-4=custom-value-4",
    ]
    expected_call = mock.call(
        " ".join(cmd),
        check=True,
        shell=True,
        stdout_level=logging.DEBUG,
        timeout=300,
    )

    # Verify Calls
    assert expected_call in mock_subprocess.call_args_list


################################################################################
# start/stop_external_services
################################################################################


@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.get_nodes_that_match_status",
    MagicMock(return_value=set()),
)
@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment.validate_global_configs",
    MagicMock(),
)
@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment._generate_docker_compose_env_vars",
    MagicMock(),
)
@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.wait_for_containers_to_match_status",
    MagicMock(),
)
@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.wait_for_nodes_to_match_status",
    MagicMock(),
)
@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.wait_for_services_to_match_status",
    MagicMock(),
)
@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment.update_metadata",
    MagicMock(),
)
@patch(
    "rib.utils.docker_compose_utils.run_docker_compose_up",
    MagicMock(),
)
@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment.upload_configs",
    MagicMock(),
)
@patch(
    "rib.utils.general_utils.load_file_into_memory",
    MagicMock(return_value={"executable": "/app/to/run"}),
)
def test_up_calls_call_external_services_script_if_first_call_to_up(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        Test up calls call_external_services_script on first up only
    Args
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    example_3x3_local_deployment_obj.status.get_containers_that_match_status = (
        MagicMock(
            side_effect=[
                {"race-client-00001"},  # first call, can be upped
                set(),  # first call, already up
                {"race-client-00002"},  # second call, can be upped
                {"race-client-00001"},  # second call, already up
            ]
        )
    )

    # Expect call to call_external_services_script when all nodes are not running
    with patch.object(
        example_3x3_local_deployment_obj, "call_external_services_script"
    ) as mock_call_external_services_script:
        example_3x3_local_deployment_obj.up()
        assert mock_call_external_services_script.call_count == 1
        expected_call = mock.call(action="Start", verbose=False)
        assert expected_call in mock_call_external_services_script.call_args_list

    # Expect no call to call_external_services_script when at least one node is running
    with patch.object(
        example_3x3_local_deployment_obj, "call_external_services_script"
    ) as mock_call_external_services_script:
        example_3x3_local_deployment_obj.up()
        assert mock_call_external_services_script.call_count == 0


@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment._generate_docker_compose_env_vars",
    MagicMock(),
)
@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.wait_for_containers_to_match_status",
    MagicMock(),
)
@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.wait_for_nodes_to_match_status",
    MagicMock(),
)
@patch(
    "rib.deployment.status.rib_local_deployment_status.RibLocalDeploymentStatus.wait_for_services_to_match_status",
    MagicMock(),
)
@patch(
    "rib.deployment.rib_local_deployment.RibLocalDeployment.update_metadata",
    MagicMock(),
)
@patch(
    "rib.utils.docker_compose_utils.run_docker_compose_stop",
    MagicMock(),
)
@patch(
    "rib.utils.docker_compose_utils.run_docker_compose_remove",
    MagicMock(),
)
def test_down_calls_call_external_services_script_if_last_call(
    example_3x3_local_deployment_obj,
):
    """
    Purpose:
        Test down calls call_external_services_script only when it's being called to fully down
    Args
        example_3x3_local_deployment_obj: Example configured 3x3 local deployment for testing
    """

    example_3x3_local_deployment_obj.managed_personas = [
        "race-client-00001",
        "race-client-00002",
    ]
    example_3x3_local_deployment_obj.status.get_nodes_that_match_status = MagicMock(
        return_value=set()
    )
    example_3x3_local_deployment_obj.status.get_containers_that_match_status = (
        MagicMock(
            side_effect=[
                {"race-client-00002"},  # first call, can be downed
                {"race-client-00001"},  # first call, already down
                {"race-client-00001"},  # second call, can be downed
                set(),  # second call, already down
            ]
        )
    )

    # Expect call to call_external_services_script when all nodes will be down after execution
    with patch.object(
        example_3x3_local_deployment_obj, "call_external_services_script"
    ) as mock_call_external_services_script:
        example_3x3_local_deployment_obj.down()
        assert mock_call_external_services_script.call_count == 1
        expected_call = mock.call(action="Stop", verbose=False)
        assert expected_call in mock_call_external_services_script.call_args_list

    # Expect no call to call_external_services_script when at least one node will not be downed
    with patch.object(
        example_3x3_local_deployment_obj, "call_external_services_script"
    ) as mock_call_external_services_script:
        example_3x3_local_deployment_obj.down()
        assert mock_call_external_services_script.call_count == 0


################################################################################
# bootstrap_node
################################################################################


def test_bootstrap_node_raises_when_mixing_client_and_server(
    example_3x3_local_deployment_obj,
):
    example_3x3_local_deployment_obj.config["artifact_manager_plugins"] = [
        {"plugin_name": "MockArtifactManagerPlugin"}
    ]

    with pytest.raises(error_utils.RIB339, match=r"Bootstrapping client.*via server"):
        example_3x3_local_deployment_obj.bootstrap_node(
            force=False,
            introducer="race-server-00002",
            target="race-client-00002",
            passphrase="bootstrap-passphrase",
            architecture="x86-64",
            bootstrapChannelId="",
        )

    with pytest.raises(error_utils.RIB339, match=r"Bootstrapping server.*via client"):
        example_3x3_local_deployment_obj.bootstrap_node(
            force=False,
            introducer="race-client-00002",
            target="race-server-00002",
            passphrase="bootstrap-passphrase",
            architecture="x86-64",
            bootstrapChannelId="",
        )


def test_bootstrap_node_detects_platform(
    example_3x3_local_deployment_obj,
):
    example_3x3_local_deployment_obj.status.get_nodes_that_match_status = MagicMock()
    example_3x3_local_deployment_obj.status.get_node_os_details = MagicMock(
        return_value=("android", "amd64")
    )
    with pytest.raises(error_utils.RIB406, match=r"Detected platform.*"):
        example_3x3_local_deployment_obj.bootstrap_node(
            force=False,
            introducer="race-client-00002",
            target="race-client-00003",
            passphrase="bootstrap-passphrase",
            architecture="amd64",
            bootstrapChannelId="",
        )


def test_bootstrap_node_detects_architecture(
    example_3x3_local_deployment_obj,
):
    example_3x3_local_deployment_obj.status.get_nodes_that_match_status = MagicMock()
    example_3x3_local_deployment_obj.status.get_node_os_details = MagicMock(
        return_value=("linux", "amd64")
    )
    with pytest.raises(error_utils.RIB406, match=r"Detected architecture.*"):
        example_3x3_local_deployment_obj.bootstrap_node(
            force=False,
            introducer="race-client-00002",
            target="race-client-00003",
            passphrase="bootstrap-passphrase",
            architecture="x86-64",
            bootstrapChannelId="",
        )


################################################################################
# copy_plugin_artifacts_into_deployment
################################################################################


@pytest.mark.parametrize(
    "platform,arch,node_type",
    [
        ("android", "arm64-v8a", "client"),
        ("android", "x86_64", "client"),
        ("linux", "arm64-v8a", "client"),
        ("linux", "arm64-v8a", "server"),
        ("linux", "x86_64", "client"),
        ("linux", "x86_64", "server"),
    ],
)
def test_copy_plugin_artifacts_into_deployment_for_deployment_nodes(
    platform,
    arch,
    node_type,
    example_3x3_local_deployment_temp_filesystem_obj,
):
    """Verifies that only artifacts for nodes in the deployment get copied"""
    example_3x3_local_deployment_temp_filesystem_obj.config["nodes"] = {
        f"race-{node_type}-00001": {
            "platform": platform,
            "architecture": arch,
            "node_type": node_type,
            "genesis": True,
            "bridge": False,
            "gpu": False,
        }
    }
    # Have to reset the cached_property attribute so the modified node config is used
    del example_3x3_local_deployment_temp_filesystem_obj.cached_node_lists

    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_network_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name="plugin_name",
        ta="network-manager",
        plugin_local_path=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{platform}-{arch}-{node_type}/network-manager/{platform}-{node_type}-artifact.txt"
    }
    assert deployment_artifacts == expected_artifacts


def test_copy_plugin_artifacts_into_deployment_for_bridged_nodes(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    example_3x3_local_deployment_temp_filesystem_obj.config["nodes"] = {
        f"race-config-00001": {
            "platform": "android",
            "architecture": "auto",
            "node_type": "client",
            "genesis": True,
            "bridge": True,
            "gpu": False,
        }
    }
    # Have to reset the cached_property attribute so the modified node config is used
    del example_3x3_local_deployment_temp_filesystem_obj.cached_node_lists

    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_network_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name="plugin_name",
        ta="network-manager",
        plugin_local_path=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/android-arm64-v8a-client/network-manager/android-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/android-x86_64-client/network-manager/android-client-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


################################################################################
# validate_local_network_manager_plugin_copying
################################################################################


def test_local_network_manager_plugin_artifacts_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_network_manager_plugin"
    plugin_name = "example_network_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name=plugin_name,
        ta="network-manager",
        plugin_local_path=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-client/network-manager/linux-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-server/network-manager/linux-server-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


def test_local_network_manager_plugin_support_files_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_network_manager_plugin"
    plugin_name = "example_network_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_support_files_into_deployment(
        plugin_name=plugin_name,
        plugin_src=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/config-generator/config-gen.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/race-python-utils/python-util.txt",
    }
    assert deployment_artifacts == expected_artifacts


################################################################################
# validate_local_comms_plugin_copying
################################################################################


def test_local_comms_plugin_artifacts_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_comms_plugin"
    plugin_name = "example_comms_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name=plugin_name,
        ta="comms",
        plugin_local_path=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-client/comms/linux-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-server/comms/linux-server-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


def test_local_comms_plugin_support_files_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_comms_plugin"
    plugin_name = "example_comms_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_support_files_into_deployment(
        plugin_name=plugin_name,
        plugin_src=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/config-generator/config-gen.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/race-python-utils/python-util.txt",
    }
    assert deployment_artifacts == expected_artifacts


################################################################################
# validate_local_artifact_manager_plugin_copying
################################################################################


def test_local_amp_plugin_artifacts_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_artifact_manager_plugin"
    plugin_name = "example_artifact_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name=plugin_name,
        ta="artifact-manager",
        plugin_local_path=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-client/artifact-manager/linux-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-server/artifact-manager/linux-server-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


def test_local_amp_plugin_support_files_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    local_plugin_path = f"{os.path.dirname(os.path.realpath(__file__))}/rib_state_path/.race/rib/example_local_plugins/example_artifact_manager_plugin"
    plugin_name = "example_artifact_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_support_files_into_deployment(
        plugin_name=plugin_name,
        plugin_src=local_plugin_path,
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/config-generator/config-gen.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/race-python-utils/python-util.txt",
    }
    assert deployment_artifacts == expected_artifacts


################################################################################
# validate_plugin_cache_network_manager_plugin_copying
################################################################################


def test_prod_network_manager_plugin_artifacts_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    plugin_name = "example_network_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name=plugin_name,
        ta="network-manager",
        plugin_local_path=f"{plugin_utils.CACHE_DIR}/prod/race/version/network-manager/{plugin_name}/revision",
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-client/network-manager/linux-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-server/network-manager/linux-server-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


def test_prod_network_manager_plugin_support_files_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    plugin_name = "example_network_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_support_files_into_deployment(
        plugin_name=plugin_name,
        plugin_src=f"{plugin_utils.CACHE_DIR}/prod/race/version/network-manager/{plugin_name}/revision",
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/config-generator/config-gen.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/race-python-utils/python-util.txt",
    }
    assert deployment_artifacts == expected_artifacts


################################################################################
# validate_plugin_cache_comms_plugin_copying
################################################################################


def test_prod_comms_plugin_artifacts_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    plugin_name = "example_comms_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name=plugin_name,
        ta="comms",
        plugin_local_path=f"{plugin_utils.CACHE_DIR}/prod/race/version/comms/{plugin_name}/revision",
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-client/comms/linux-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-server/comms/linux-server-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


def test_prod_comms_plugin_support_files_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    plugin_name = "example_comms_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_support_files_into_deployment(
        plugin_name=plugin_name,
        plugin_src=f"{plugin_utils.CACHE_DIR}/prod/race/version/comms/{plugin_name}/revision",
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/config-generator/config-gen.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/race-python-utils/python-util.txt",
    }
    assert deployment_artifacts == expected_artifacts


################################################################################
# validate_plugin_cache_artifact_manager_plugin_copying
################################################################################


def test_prod_amp_plugin_artifacts_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    plugin_name = "example_artifact_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_artifacts_into_deployment(
        plugin_name=plugin_name,
        ta="artifact-manager",
        plugin_local_path=f"{plugin_utils.CACHE_DIR}/prod/race/version/artifact-manager/{plugin_name}/revision",
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-client/artifact-manager/linux-client-artifact.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/linux-x86_64-server/artifact-manager/linux-server-artifact.txt",
    }
    assert deployment_artifacts == expected_artifacts


def test_prod_amp_plugin_support_files_copied(
    example_3x3_local_deployment_temp_filesystem_obj,
):
    plugin_name = "example_artifact_manager_plugin"
    example_3x3_local_deployment_temp_filesystem_obj.copy_plugin_support_files_into_deployment(
        plugin_name=plugin_name,
        plugin_src=f"{plugin_utils.CACHE_DIR}/prod/race/version/artifact-manager/{plugin_name}/revision",
    )
    deployment_artifacts = set()
    for root, _, files in os.walk(
        example_3x3_local_deployment_temp_filesystem_obj.paths.dirs["plugins"]
    ):
        for name in files:
            file_name = os.path.join(root, name)
            deployment_artifacts.add(file_name)
    expected_artifacts = {
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/config-generator/config-gen.txt",
        f"{example_3x3_local_deployment_temp_filesystem_obj.paths.dirs['plugins']}/{plugin_name}/race-python-utils/python-util.txt",
    }
    assert deployment_artifacts == expected_artifacts

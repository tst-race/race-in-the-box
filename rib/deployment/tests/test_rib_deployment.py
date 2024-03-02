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
        Test File for rib_deployment.py
"""

# Python Library Imports
from datetime import datetime
import json
import os
import pytest
from typing import Any, Dict
from unittest import mock
from unittest.mock import MagicMock, patch, create_autospec

# Local Library Imports
from rib.deployment.rib_aws_deployment import RibAwsDeployment
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.rib_deployment_config import (
    BaseDeploymentConfig,
    ChannelConfig,
    DeploymentMetadata,
    NodeConfig,
)
from rib.deployment.rib_local_deployment import RibLocalDeployment
from rib.deployment.status.rib_deployment_status import RibDeploymentStatus
from rib.utils import (
    error_utils,
    race_node_utils,
)
from rib.utils.plugin_utils import (
    KitCacheMetadata,
    KitConfig,
    KitSource,
    KitSourceType,
    KitType,
)


###
# Data Fixtures/Mocks
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


@pytest.fixture
def base_deployment_config() -> BaseDeploymentConfig:
    """Base deployment configuration"""
    return BaseDeploymentConfig(
        name="test-deployment",
        mode="test-rib-mode",
        rib_version="test-rib-version",
        race_core=KitSource(
            raw="local=/race-core",
            source_type=KitSourceType.LOCAL,
            uri="/race-core",
        ),
        android_app=KitConfig(
            name="AndroidApp",
            kit_type=KitType.APP,
            source=KitSource(
                raw="core=android-app",
                source_type=KitSourceType.CORE,
                asset="android-app",
            ),
        ),
        linux_app=KitConfig(
            name="LinuxApp",
            kit_type=KitType.APP,
            source=KitSource(
                raw="core=linux-app",
                source_type=KitSourceType.CORE,
                asset="linux-app",
            ),
        ),
        node_daemon=KitConfig(
            name="NodeDaemon",
            kit_type=KitType.APP,
            source=KitSource(
                raw="core=node-daemon",
                source_type=KitSourceType.CORE,
                asset="node-daemon",
            ),
        ),
        network_manager_kit=KitConfig(
            name="test-network-manager-plugin",
            kit_type=KitType.NETWORK_MANAGER,
            source=KitSource(
                raw="core=test-network-manager-plugin",
                source_type=KitSourceType.CORE,
                asset="test-network-manager-plugin",
            ),
        ),
        comms_channels=[
            ChannelConfig(
                name="test-comms-channel",
                kit_name="test-comms-plugin",
                enabled=True,
            ),
        ],
        comms_kits=[
            KitConfig(
                name="test-comms-plugin",
                kit_type=KitType.COMMS,
                source=KitSource(
                    raw="core=test-comms-plugin",
                    source_type=KitSourceType.CORE,
                    asset="test-comms-plugin",
                ),
            ),
        ],
        artifact_manager_kits=[
            KitConfig(
                name="test-artifact-manager-plugin",
                kit_type=KitType.ARTIFACT_MANAGER,
                source=KitSource(
                    raw="core=test-artifact-manager-plugin",
                    source_type=KitSourceType.CORE,
                    asset="test-artifact-manager-plugin",
                ),
            ),
        ],
        nodes={
            "race-client-00001": NodeConfig(
                platform="android",
                architecture="arm64-v8a",
                node_type="client",
                genesis=True,
                bridge=False,
                gpu=False,
            ),
            "race-client-00002": NodeConfig(
                platform="linux",
                architecture="x86_64",
                node_type="client",
                genesis=True,
                bridge=False,
                gpu=False,
            ),
            "race-client-00003": NodeConfig(
                platform="linux",
                architecture="x86_64",
                node_type="client",
                genesis=True,
                bridge=False,
                gpu=False,
            ),
            "race-server-00001": NodeConfig(
                platform="linux",
                architecture="x86_64",
                node_type="server",
                genesis=True,
                bridge=False,
                gpu=False,
            ),
            "race-server-00002": NodeConfig(
                platform="linux",
                architecture="x86_64",
                node_type="server",
                genesis=True,
                bridge=False,
                gpu=False,
            ),
            "race-server-00003": NodeConfig(
                platform="linux",
                architecture="x86_64",
                node_type="server",
                genesis=True,
                bridge=False,
                gpu=False,
            ),
        },
        images=[],
        race_encryption_type="ENC_NONE",
    )


@pytest.fixture
def deployment_metadata() -> DeploymentMetadata:
    """Deployment metadata"""
    cache_metadata = KitCacheMetadata(
        source_type=KitSourceType.LOCAL,
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
def stub_deployment(base_deployment_config, deployment_metadata) -> RibDeployment:
    """
    Purpose:
        Test fixture of a RibDeployment, with all abstract methods replaced with MagicMocks
    Return:
        Mocked out RibDeployment instance
    """
    RibDeployment.pathsClass.dirs = {
        "mode": "/tmp/test-rib-state-path/.race/rib/deployments"
    }
    RibDeployment.load_metadata = MagicMock(return_value={})
    RibDeployment.remove = MagicMock(return_value={})
    orig_abstract_methods = RibDeployment.__abstractmethods__
    RibDeployment.__abstractmethods__ = set()

    deployment = RibDeployment(
        config=base_deployment_config,
        metadata=deployment_metadata,
    )
    deployment.paths = MagicMock()
    deployment.status = RibDeploymentStatus(deployment)
    deployment._orig_verify_deployment_is_active = (
        deployment.status.verify_deployment_is_active
    )
    deployment.status.verify_deployment_is_active = MagicMock()
    deployment._race_node_interface = create_autospec(race_node_utils.RaceNodeInterface)
    deployment._race_node_interface.get_all_node_personas = MagicMock(return_value=[])
    for method_name in orig_abstract_methods:
        try:
            setattr(deployment, method_name, MagicMock())
        except:
            pass  # Fails for @property abstract methods

    return deployment


###
# Test Deployment Methods (Base Class)
###


################################################################################
# get_deployment_class
################################################################################


def test_get_deployment_class() -> int:
    """
    Purpose:
        Test get_deployment_class returns the correct classes
    Args
        N/A
    """

    assert RibDeployment.get_deployment_class("aws") == RibAwsDeployment
    assert RibDeployment.get_deployment_class("local") == RibLocalDeployment
    assert RibDeployment.get_deployment_class("not_real") == None


################################################################################
# Plugin Config Gen
################################################################################


def test_merge_fulfilled_requests_same_link() -> int:
    """
    Purpose:
        Test test_merge_fulfilled_requests merges a link from two different channels
    Args
        N/A
    """

    fulfulled_requests_channel_1 = [
        {
            "channels": ["channel_1"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002", "race-client-00003"],
        }
    ]

    fulfulled_requests_channel_2 = [
        {
            "channels": ["channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002", "race-client-00003"],
        }
    ]

    list_of_fulfilled_requests = [
        fulfulled_requests_channel_1,
        fulfulled_requests_channel_2,
    ]

    original_request = [
        {
            "channels": ["channel_1", "channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002", "race-client-00003"],
        }
    ]

    expected_merge_result = [
        {
            "channels": ["channel_1", "channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002", "race-client-00003"],
        }
    ]

    assert (
        RibDeployment.merge_fulfilled_requests(
            original_request, list_of_fulfilled_requests
        )
        == expected_merge_result
    )


def test_merge_fulfilled_requests_different_links() -> int:
    """
    Purpose:
        Test test_merge_fulfilled_requests merges two different links from two different channels
    Args
        N/A
    """

    fulfulled_requests_channel_1 = [
        {
            "channels": ["channel_1"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002"],
        }
    ]

    fulfulled_requests_channel_2 = [
        {
            "channels": ["channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00003"],
        }
    ]

    list_of_fulfilled_requests = [
        fulfulled_requests_channel_1,
        fulfulled_requests_channel_2,
    ]

    original_request = [
        {
            "channels": ["channel_1", "channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002"],
        },
        {
            "channels": ["channel_1", "channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00003"],
        },
    ]

    expected_merge_result = [
        {
            "channels": ["channel_1"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00002"],
        },
        {
            "channels": ["channel_2"],
            "sender": "race-client-00001",
            "recipients": ["race-client-00003"],
        },
    ]

    assert (
        RibDeployment.merge_fulfilled_requests(
            original_request, list_of_fulfilled_requests
        )
        == expected_merge_result
    )


################################################################################
# plugin copying
################################################################################


@patch("rib.utils.general_utils.get_contents_of_dir")
@patch("os.path.isdir")
@patch("os.path.isfile")
@patch("zipfile.ZipFile")
def test_copy_plugin_to_shard_dir_one_so_per_platform(
    mock_zip,
    mock_isfile,
    mock_isdir,
    mock_get_contents_of_dir,
    stub_deployment,
) -> int:
    """
    Purpose:
        Test base case of copying one plugin SO from each platorm directory
    Args
        N/A
    """
    mock_isdir.return_value = (
        True  # return true for path to plugin and all platform dirs
    )
    mock_isfile.return_value = True  # make this look like a plugin SO
    mock_get_contents_of_dir.return_value = ["plugin_1"]
    stub_deployment.paths.dirs = {
        "plugins": "plugins/dir",
        "distribution_artifacts": "dist/dir",
    }

    arcnames = []

    def mock_zipfile_init(filename, _):
        plugin_name = filename.split("/")[-1]
        arcnames.append(plugin_name)
        return MagicMock()

    mock_zip.side_effect = mock_zipfile_init

    stub_deployment.paths.supported_platform_arch_node_type_combinations = [
        ("android", "arm64-v8a", "client"),
        ("android", "x86_64", "client"),
        ("linux", "arm64-v8a", "client"),
        ("linux", "x86_64", "client"),
        ("linux", "arm64-v8a", "server"),
        ("linux", "x86_64", "server"),
    ]

    stub_deployment.paths.get_plugin_artifacts_ta_dir_key = MagicMock(
        return_value="plugins"
    )

    stub_deployment.copy_plugin_to_distribution_dir(
        plugin_name="plugin_1", plugin_type="network-manager"
    )
    expected_arcnames = [
        "android-arm64-v8a-client-plugin_1.zip",
        "android-x86_64-client-plugin_1.zip",
        "linux-arm64-v8a-client-plugin_1.zip",
        "linux-x86_64-client-plugin_1.zip",
        "linux-x86_64-server-plugin_1.zip",
    ]
    assert arcnames == expected_arcnames


################################################################################
# race.json
################################################################################


@patch("rib.deployment.rib_deployment.RibDeployment.get_deployment_channels_list")
@patch("rib.deployment.rib_deployment.RibDeployment.get_plugin_manifests")
@patch("rib.utils.general_utils.load_file_into_memory")
def test_create_race_json(
    mock_load_file_into_memory,
    mock_get_plugin_manifest,
    mock_get_deployment_channels_list,
    stub_deployment,
) -> int:
    """
    Purpose:
        Test creation of race.json for plugins without manifest.json's
    Args
        N/A
    """
    example_template = {"bandwidth": "-1", "debug": "false"}

    mock_load_file_into_memory.return_value = example_template
    mock_get_plugin_manifest.return_value = [], []
    mock_get_deployment_channels_list.return_value = []
    # required to get fields
    stub_deployment.paths.dirs = {}

    expected_race_json = dict(example_template)
    expected_race_json.update({"plugins": []})
    expected_race_json.update({"channels": []})
    expected_race_json.update({"compositions": []})
    expected_race_json.update({"isPluginFetchOnStartEnabled": "false"})

    assert (
        stub_deployment.create_race_json(
            config_template_dir="not/used/in/unit/test",
        )
        == expected_race_json
    )


@patch("rib.deployment.rib_deployment.RibDeployment.get_deployment_channels_list")
@patch("rib.deployment.rib_deployment.RibDeployment.get_plugin_manifests")
@patch("rib.utils.general_utils.load_file_into_memory")
@patch("rib.utils.general_utils.write_data_to_file")
def test_update_race_json(
    mock_write_data_to_file,
    mock_load_file_into_memory,
    mock_get_plugin_manifest,
    mock_get_deployment_channels_list,
    stub_deployment,
) -> int:
    """
    Purpose:
        Test that when update_race_json is called, the value of
        isPluginFetchOnStartEnabled field is preserved in the new file
    Args
        N/A
    """
    example_template = {
        "bandwidth": "-1",
        "debug": "false",
        "isPluginFetchOnStartEnabled": "true",
    }

    mock_write_data_to_file.return_value = None
    mock_load_file_into_memory.return_value = example_template
    mock_get_plugin_manifest.return_value = [], []
    mock_get_deployment_channels_list.return_value = []
    # required to get fields
    stub_deployment.paths.dirs = {
        "templates": "not/used/in/unit/test",
        "global_android_configs": "not/used/in/unit/test",
        "global_linux_configs": "not/used/in/unit/test",
    }

    expected_race_json = dict(example_template)
    expected_race_json.update({"plugins": []})
    expected_race_json.update({"channels": []})
    expected_race_json.update({"compositions": []})
    # The default value for this field is "false"; if the "true" value persists
    # then the value from the field was successfully propagated through
    expected_race_json.update({"isPluginFetchOnStartEnabled": "true"})

    assert stub_deployment.update_race_json() == expected_race_json


@patch("os.path.isfile")
@patch("os.path.isdir")
@patch("rib.utils.general_utils.get_contents_of_dir")
def test_get_plugin_manifests_no_manifest(
    mock_get_contents_of_dir, mock_is_dir, mock_is_file, stub_deployment
) -> int:
    """
    Purpose:
        Test that get_plugin_manifests returns an empty list when the plugin does not have a manifest
    Args
        N/A
    """

    stub_deployment.paths.dirs = {"plugins": "plugins/dir"}

    # Used to get plugins from plugin dir
    mock_get_contents_of_dir.return_value = [
        "path/to/.gitignore",
        "path/to/plugin_1.so",
        "path/to/additional-libraries/",
    ]

    def mock_is_file_side_effect_func(value):
        # Only return file found for .so, not manifest.json
        return value.split(".")[-1] == "so"

    mock_is_file.side_effect = mock_is_file_side_effect_func

    stub_deployment.paths.dirs = {"plugins": "plugins/dir"}
    stub_deployment.paths.get_plugin_artifacts_ta_dir_key = MagicMock(
        return_value="plugins"
    )

    assert (
        stub_deployment.get_plugin_manifests(
            kit_name="ignored-in-unit-test", kit_type="network-manager"
        )
        == [],
        [],
    )


@patch("rib.utils.general_utils.load_file_into_memory")
@patch("os.path.isfile")
@patch("os.path.isdir")
@patch("rib.utils.general_utils.get_contents_of_dir")
def test_get_plugin_manifests_with_supplied_manifest(
    mock_get_contents_of_dir,
    mock_is_dir,
    mock_is_file,
    mock_load_file_into_memory,
    stub_deployment,
) -> int:
    """
    Purpose:
        Test generation of plugin manifests with supplied manifest
    Args
        N/A
    """

    # Copied the manfiest from Python network manager because it was the most difficult case to handle
    supplied_manifest = {
        "plugins": [
            {
                "file_path": "PluginNMTwoSixPython",
                "plugin_type": "network-manager",
                "file_type": "python",
                "node_type": "client",
                "python_module": "PluginNMTwoSixPython.PluginNMTwoSixClientPy",
                "python_class": "PluginNMTwoSixClientPy",
                "config_path": "PluginNMTwoSixPython/",
            },
            {
                "file_path": "PluginNMTwoSixPython",
                "plugin_type": "network-manager",
                "file_type": "python",
                "node_type": "server",
                "python_module": "PluginNMTwoSixPython.PluginNMTwoSixServerPy",
                "python_class": "PluginNMTwoSixServerPy",
                "config_path": "PluginNMTwoSixPython/",
            },
        ],
        "compositions": [
            {
                "id": "twoSixIndirectComposition",
                "transport": "twoSixIndirect",
                "usermodel": "periodic",
                "encodings": ["base64"],
            }
        ],
    }

    mock_load_file_into_memory.return_value = supplied_manifest

    # Used to get plugins from plugin dir
    mock_get_contents_of_dir.return_value = ["path/to/plugin_1"]
    # Always returning True will make it think plugin is a directory with manifest within
    mock_is_dir.return_value = True
    mock_is_file.return_value = True

    stub_deployment.paths.dirs = {"plugins": "plugins/dir"}
    stub_deployment.paths.get_plugin_artifacts_ta_dir_key = MagicMock(
        return_value="plugins"
    )

    expected_plugins = [
        {
            "file_path": "PluginNMTwoSixPython",
            "plugin_type": "network-manager",
            "file_type": "python",
            "node_type": "client",
            "python_module": "PluginNMTwoSixPython.PluginNMTwoSixClientPy",
            "python_class": "PluginNMTwoSixClientPy",
            "config_path": "PluginNMTwoSixPython/",
            "platform": "android",
            "architecture": "arm64-v8a",
        },
        {
            "file_path": "PluginNMTwoSixPython",
            "plugin_type": "network-manager",
            "file_type": "python",
            "node_type": "client",
            "python_module": "PluginNMTwoSixPython.PluginNMTwoSixClientPy",
            "python_class": "PluginNMTwoSixClientPy",
            "config_path": "PluginNMTwoSixPython/",
            "platform": "android",
            "architecture": "x86_64",
        },
        {
            "file_path": "PluginNMTwoSixPython",
            "plugin_type": "network-manager",
            "file_type": "python",
            "node_type": "client",
            "python_module": "PluginNMTwoSixPython.PluginNMTwoSixClientPy",
            "python_class": "PluginNMTwoSixClientPy",
            "config_path": "PluginNMTwoSixPython/",
            "platform": "linux",
            "architecture": "x86_64",
        },
        {
            "file_path": "PluginNMTwoSixPython",
            "plugin_type": "network-manager",
            "file_type": "python",
            "node_type": "server",
            "python_module": "PluginNMTwoSixPython.PluginNMTwoSixServerPy",
            "python_class": "PluginNMTwoSixServerPy",
            "config_path": "PluginNMTwoSixPython/",
            "platform": "linux",
            "architecture": "x86_64",
        },
    ]

    expected_compositions = [
        {
            "id": "twoSixIndirectComposition",
            "transport": "twoSixIndirect",
            "usermodel": "periodic",
            "encodings": ["base64"],
            "node_type": "client",
            "platform": "android",
            "architecture": "arm64-v8a",
        },
        {
            "id": "twoSixIndirectComposition",
            "transport": "twoSixIndirect",
            "usermodel": "periodic",
            "encodings": ["base64"],
            "node_type": "client",
            "platform": "android",
            "architecture": "x86_64",
        },
        {
            "id": "twoSixIndirectComposition",
            "transport": "twoSixIndirect",
            "usermodel": "periodic",
            "encodings": ["base64"],
            "node_type": "client",
            "platform": "linux",
            "architecture": "x86_64",
        },
        {
            "id": "twoSixIndirectComposition",
            "transport": "twoSixIndirect",
            "usermodel": "periodic",
            "encodings": ["base64"],
            "node_type": "server",
            "platform": "linux",
            "architecture": "x86_64",
        },
    ]

    assert (
        stub_deployment.get_plugin_manifests(
            kit_name="ignored-in-unit-test", kit_type="network-manager"
        )
        == expected_plugins,
        expected_compositions,
    )


###
# get_deployments
###


def test_get_deployments() -> int:
    """
    Test get_deployments function
    """

    with pytest.raises(Exception):
        RibDeployment.get_deployment(None)

    # TODO, test load_config


################################################################################
# validate_sender_recipient
################################################################################


def test_validate_sender_recipient_non_existant_recipient(stub_deployment):
    with pytest.raises(error_utils.RIB307, match=r".*Recipient is not a valid node.*"):
        stub_deployment.validate_sender_recipient(
            "race-client-00001", "race-client-00004", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_non_existant_sender(stub_deployment):
    with pytest.raises(error_utils.RIB307, match=r".*Sender is not a valid node.*"):
        stub_deployment.validate_sender_recipient(
            "race-client-00004", "race-client-00001", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_client_to_client_non_comms(stub_deployment):
    with pytest.raises(error_utils.RIB307) as error:
        stub_deployment.validate_sender_recipient(
            "race-client-00001", "race-client-00002", is_network_manager_bypass=True
        )


def test_validate_sender_recipient_client_to_server_comms(stub_deployment):
    with pytest.raises(error_utils.RIB307) as error:
        stub_deployment.validate_sender_recipient(
            "race-client-00001", "race-server-00001", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_server_to_server_comms(stub_deployment):
    with pytest.raises(error_utils.RIB307) as error:
        stub_deployment.validate_sender_recipient(
            "race-server-00001", "race-server-00002", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_server_to_client_comms(stub_deployment):
    with pytest.raises(error_utils.RIB307) as error:
        stub_deployment.validate_sender_recipient(
            "race-server-00001", "race-client-00001", is_network_manager_bypass=False
        )


def test_validate_sender_recipient_self(stub_deployment):
    with pytest.raises(error_utils.RIB307, match=r".*Cannot send to self.*"):
        stub_deployment.validate_sender_recipient(
            "race-client-00001", "race-client-00001", is_network_manager_bypass=False
        )


################################################################################
# get_available_recipients_by_sender
################################################################################


def test_get_available_recipients_by_sender_client_comms_mode(stub_deployment):
    available_recipients = stub_deployment.get_available_recipients_by_sender(
        "race-client-00001", is_network_manager_bypass=True
    )

    assert sorted(
        ["race-server-00001", "race-server-00002", "race-server-00003"]
    ) == sorted(available_recipients)


def test_get_available_recipients_by_sender_client(stub_deployment):
    available_recipients = stub_deployment.get_available_recipients_by_sender(
        "race-client-00001", is_network_manager_bypass=False
    )

    assert sorted(["race-client-00002", "race-client-00003"]) == sorted(
        available_recipients
    )


def test_get_available_recipients_by_sender_server_comms_mode(stub_deployment):
    available_recipients = stub_deployment.get_available_recipients_by_sender(
        "race-server-00001", is_network_manager_bypass=True
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


def test_get_available_recipients_by_sender_server(stub_deployment):
    available_recipients = stub_deployment.get_available_recipients_by_sender(
        "race-server-00001", is_network_manager_bypass=False
    )

    assert [] == available_recipients


################################################################################
# send_message
################################################################################


def test_send_message_manual_no_nodes(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a manual message, no
            nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={
            "race-client-00001",
            "race-client-00002",
            "race-client-00003",
            "race-server-00001",
            "race-server-00002",
            "race-server-00003",
        }
    )

    # Run Test
    stub_deployment.send_message(
        message_type="manual", message_content="hello", test_id="test-id"
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_manual_message.call_count == 6
    assert expected_call in race_node_interface.send_manual_message.call_args_list


def test_send_message_manual_no_nodes_partially_up(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a manual message, no
            nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001", "race-client-00003"}
    )

    # Run Test
    stub_deployment.send_message(
        message_type="manual", message_content="hello", test_id="test-id"
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_manual_message.call_count == 4
    assert expected_call in race_node_interface.send_manual_message.call_args_list


def test_send_message_manual_sender(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a manual message,
            sender node specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={
            "race-client-00001",
            "race-client-00002",
            "race-client-00003",
            "race-server-00001",
            "race-server-00002",
            "race-server-00003",
        }
    )

    # Run Test
    stub_deployment.send_message(
        message_type="manual",
        message_content="hello",
        sender="race-client-00001",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_manual_message.call_count == 2
    assert expected_call in race_node_interface.send_manual_message.call_args_list


def test_send_message_manual_recipient(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a manual message, both
            sender and recipient nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={
            "race-client-00001",
            "race-client-00002",
            "race-client-00003",
            "race-server-00001",
            "race-server-00002",
            "race-server-00003",
        }
    )

    # Run Test
    stub_deployment.send_message(
        message_type="manual",
        message_content="hello",
        recipient="race-client-00002",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_manual_message.call_count == 2
    assert expected_call in race_node_interface.send_manual_message.call_args_list


def test_send_message_manual_nodes(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a manual message, both
            sender and recipient nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={
            "race-client-00001",
            "race-client-00002",
            "race-client-00003",
            "race-server-00001",
            "race-server-00002",
            "race-server-00003",
        }
    )

    # Run Test
    stub_deployment.send_message(
        message_type="manual",
        message_content="hello",
        sender="race-client-00001",
        recipient="race-client-00002",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_manual_message.call_count == 1
    assert expected_call in race_node_interface.send_manual_message.call_args_list
    race_node_interface.send_manual_message.assert_called_once_with(
        sender="race-client-00001",
        recipient="race-client-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="",
    )


def test_send_message_manual_explicit_network_manager_bypass_route(
    stub_deployment,
):
    """
    Purpose:
        Test the `deployment.send_message` works with: a manual message and a
        message-specific network-manager-bypass route
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001", "race-server-00002"}
    )

    stub_deployment.network_manager_bypass_route = "twoSixDirectCpp"

    # Run Test
    stub_deployment.send_message(
        message_type="manual",
        message_content="hello",
        sender="race-client-00001",
        recipient="race-server-00002",
        network_manager_bypass_route="twoSixIndirectCpp",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-server-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="twoSixIndirectCpp",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_manual_message.call_count == 1
    assert expected_call in race_node_interface.send_manual_message.call_args_list
    race_node_interface.send_manual_message.assert_called_once_with(
        sender="race-client-00001",
        recipient="race-server-00002",
        message="hello",
        test_id="test-id",
        network_manager_bypass_route="twoSixIndirectCpp",
    )


def test_send_message_auto_no_nodes(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a auto message, no
            nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={
            "race-client-00001",
            "race-client-00002",
            "race-client-00003",
            "race-server-00001",
            "race-server-00002",
            "race-server-00003",
        }
    )

    # Run Test
    stub_deployment.send_message(
        message_type="auto",
        message_period=10,
        message_quantity=10,
        message_size=10,
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_auto_message.call_count == 6
    assert expected_call in race_node_interface.send_auto_message.call_args_list


def test_send_message_auto_sender(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a auto message, only
            sender nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001"}
    )

    # Run Test
    stub_deployment.send_message(
        message_type="auto",
        message_period=10,
        message_quantity=10,
        message_size=10,
        sender="race-client-00001",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_auto_message.call_count == 2
    assert expected_call in race_node_interface.send_auto_message.call_args_list


def test_send_message_auto_recipient(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a auto message, only
            recipient nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001", "race-client-00003"}
    )

    # Run Test
    stub_deployment.send_message(
        message_type="auto",
        message_period=10,
        message_quantity=10,
        message_size=10,
        recipient="race-client-00002",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_auto_message.call_count == 2
    assert expected_call in race_node_interface.send_auto_message.call_args_list


def test_send_message_auto_nodes(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a auto message, both
            sender and recipient nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001"}
    )

    # Run Test
    stub_deployment.send_message(
        message_type="auto",
        message_period=10,
        message_quantity=10,
        message_size=10,
        sender="race-client-00001",
        recipient="race-client-00002",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-client-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_auto_message.call_count == 1
    assert expected_call in race_node_interface.send_auto_message.call_args_list
    race_node_interface.send_auto_message.assert_called_once_with(
        sender="race-client-00001",
        recipient="race-client-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="",
    )


def test_send_message_auto_explicit_network_manager_bypass_route(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_message` works with: a auto message and a
            message-specific network-manager-bypass route
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001"}
    )

    stub_deployment.network_manager_bypass_route = "twoSixDirectCpp"

    # Run Test
    stub_deployment.send_message(
        message_type="auto",
        message_period=10,
        message_quantity=10,
        message_size=10,
        sender="race-client-00001",
        recipient="race-server-00002",
        network_manager_bypass_route="twoSixIndirectCpp",
        test_id="test-id",
    )

    # Expectations
    expected_call = mock.call(
        sender="race-client-00001",
        recipient="race-server-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="twoSixIndirectCpp",
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_auto_message.call_count == 1
    assert expected_call in race_node_interface.send_auto_message.call_args_list
    race_node_interface.send_auto_message.assert_called_once_with(
        sender="race-client-00001",
        recipient="race-server-00002",
        period=10,
        quantity=10,
        size=10,
        test_id="test-id",
        network_manager_bypass_route="twoSixIndirectCpp",
    )


################################################################################
# send_plan
################################################################################


@patch(
    "rib.utils.general_utils.load_file_into_memory",
    MagicMock(return_value={"messages": {}}),
)
def test_send_message_plan_no_nodes(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_plan` works with: a manual message, no
            nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(return_value={})

    # Run Test
    stub_deployment.send_plan(
        message_plan_file="plan.json",
        start_time=1234567890000,
        test_id="test-id",
    )

    # Verify Calls
    assert stub_deployment._race_node_interface.send_message_plan.call_count == 0


@patch(
    "rib.utils.general_utils.load_file_into_memory",
    MagicMock(
        return_value={
            "messages": {
                "race-client-00001": {
                    "race-client-00002": [
                        {"size": 10, "time": 0},
                        {"size": 100, "time": 10000},
                    ],
                }
            }
        }
    ),
)
def test_send_message_plan_single_node(stub_deployment):
    """
    Purpose:
        Test the `deployment.send_plan` works with: a manual message, no
            nodes specified
    Args:
        stub_deployment: Stub/mock deployment
    """

    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001"}
    )

    # Run Test
    stub_deployment.send_plan(
        message_plan_file="plan.json",
        start_time=1234567890000,
        test_id="test-id",
    )

    expected_call = mock.call(
        sender="race-client-00001",
        plan={
            "start-time": 1234567890000,
            "test-id": "test-id",
            "messages": {
                "race-client-00002": [
                    {"size": 10, "time": 0},
                    {"size": 100, "time": 10000},
                ],
            },
            "network-manager-bypass-route": "",
        },
    )

    # Verify Calls
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.send_message_plan.call_count == 1
    assert expected_call in race_node_interface.send_message_plan.call_args_list


################################################################################
# node regex
################################################################################


def test_get_nodes_from_regex_standard_name(stub_deployment):
    """
    Purpose:
        Test get_nodes_from_regex works with: standard node names
    Args:
        stub_deployment: Stub/mock deployment
    """

    standard_node_names = ["race-client-00001", "race-client-00002"]

    assert sorted(standard_node_names) == sorted(
        stub_deployment.get_nodes_from_regex(standard_node_names)
    )


def test_get_nodes_from_regex_wildcard(stub_deployment):
    """
    Purpose:
        Test get_nodes_from_regex works with: wildcards
    Args:
        stub_deployment: Stub/mock deployment
    """

    standard_node_names = ["race-server-0000*"]
    expected_node_names = [
        "race-server-00001",
        "race-server-00002",
        "race-server-00003",
    ]

    assert sorted(expected_node_names) == sorted(
        stub_deployment.get_nodes_from_regex(standard_node_names)
    )


def test_get_nodes_from_regex_overalapping_regex(stub_deployment):
    """
    Purpose:
        Test get_nodes_from_regex works with: over-lapping regexes
    Args:
        stub_deployment: Stub/mock deployment
    """

    standard_node_names = ["race-server-0000*", "race-server-0000[1-2]"]
    expected_node_names = [
        "race-server-00001",
        "race-server-00002",
        "race-server-00003",
    ]

    assert sorted(expected_node_names) == sorted(
        stub_deployment.get_nodes_from_regex(standard_node_names)
    )


################################################################################
# timezone functionality
################################################################################


@patch(
    "rib.utils.general_utils.get_current_utc_time",
    MagicMock(return_value=datetime(2022, 9, 14, 19, 1, 0, 0)),
)
def test_set_timezone_local_time_set(stub_deployment):
    # set up mocks
    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001", "race-client-00003"}
    )

    # set up expectations
    # manually tested this date and time combo to verify this is the correct expectation
    expected_call = mock.call(
        persona="race-client-00001", specified_zone="America/Creston"
    )

    # run the calls
    stub_deployment.set_timezone(
        local_time=12,
    )
    # verify results
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.set_timezone.call_count == 2
    assert expected_call in race_node_interface.set_timezone.call_args_list


def test_set_timezone_zone_set(stub_deployment):
    # set up mocks
    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001", "race-client-00003"}
    )

    # set up expectations
    # manually tested this date and time combo to verify this is the correct expectation
    expected_call = mock.call(
        persona="race-client-00001", specified_zone="America/Creston"
    )

    # run the calls
    stub_deployment.set_timezone(
        zone="America/Creston",
    )
    # verify results
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.set_timezone.call_count == 2
    assert expected_call in race_node_interface.set_timezone.call_args_list


def test_set_timezone_subset_of_nodes(stub_deployment):
    # set up mocks
    stub_deployment.status.get_nodes_that_match_status = MagicMock(
        return_value={"race-client-00001", "race-client-00003"}
    )

    expected_nodes = {"race-client-00001", "race-client-00002", "race-client-00003"}

    # set up expectations
    # manually tested this date and time combo to verify this is the correct expectation
    expected_call = mock.call(
        persona="race-client-00001",
        specified_zone="America/Creston",
    )

    # run the calls
    stub_deployment.set_timezone(
        nodes=expected_nodes,
        zone="America/Creston",
    )

    # verify results
    race_node_interface = stub_deployment._race_node_interface
    assert race_node_interface.set_timezone.call_count == 2
    assert expected_call in race_node_interface.set_timezone.call_args_list

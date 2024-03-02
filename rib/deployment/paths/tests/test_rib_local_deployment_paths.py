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
        Test File for rib_local_deployment_paths.py
"""

# Python Library Imports
import pytest

# Local Library Imports
from rib.deployment.paths.rib_local_deployment_paths import RibLocalDeploymentPaths
from rib.deployment.rib_deployment import RibDeployment

###
# Mocks
###


@pytest.fixture
def paths():
    paths: RibLocalDeploymentPaths = RibLocalDeploymentPaths("test-deployment")
    return paths


###
# Tests
###


def test_verify_expected_dirs(paths):
    docker_rib_state_path = RibDeployment.rib_config.DOCKER_RIB_STATE_PATH
    assert paths.dirs == {
        "artifact_manager_configs_base": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/artifact-manager",
        "base": f"{docker_rib_state_path}/deployments/local/test-deployment",
        "data": f"{docker_rib_state_path}/deployments/local/test-deployment/data",
        "device-prepare-archives": f"{docker_rib_state_path}/deployments/local/test-deployment/android-device-prepare-archives",
        "distribution_artifacts": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/dist",
        "dnsproxy": f"{docker_rib_state_path}/deployments/local/test-deployment/dnsproxy",
        "elasticsearch": f"{docker_rib_state_path}/deployments/local/test-deployment/logs/opentracing/elasticsearch",
        "etc": f"{docker_rib_state_path}/deployments/local/test-deployment/etc",
        "global_android_configs": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/global/android",
        "global_configs": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/global",
        "global_linux_configs": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/global/linux",
        "keys": f"{docker_rib_state_path}/deployments/local/test-deployment/data/keys",
        "logs": f"{docker_rib_state_path}/deployments/local/test-deployment/logs",
        "mode": f"{docker_rib_state_path}/deployments/local",
        "opentracing": f"{docker_rib_state_path}/deployments/local/test-deployment/logs/opentracing",
        "plugins_android_arm64-v8a_client_artifact-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-arm64-v8a-client/artifact-manager",
        "plugins_android_arm64-v8a_client_dir": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-arm64-v8a-client",
        "plugins_android_arm64-v8a_client_network-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-arm64-v8a-client/network-manager",
        "plugins_android_arm64-v8a_client_comms": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-arm64-v8a-client/comms",
        "plugins_android_arm64-v8a_client_core": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-arm64-v8a-client/core",
        "plugins_android_x86_64_client_artifact-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-x86_64-client/artifact-manager",
        "plugins_android_x86_64_client_dir": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-x86_64-client",
        "plugins_android_x86_64_client_network-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-x86_64-client/network-manager",
        "plugins_android_x86_64_client_comms": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-x86_64-client/comms",
        "plugins_android_x86_64_client_core": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/android-x86_64-client/core",
        "plugins_linux_arm64-v8a_client_artifact-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-client/artifact-manager",
        "plugins_linux_arm64-v8a_client_dir": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-client",
        "plugins_linux_arm64-v8a_client_network-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-client/network-manager",
        "plugins_linux_arm64-v8a_client_comms": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-client/comms",
        "plugins_linux_arm64-v8a_client_core": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-client/core",
        "plugins_linux_arm64-v8a_server_artifact-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-server/artifact-manager",
        "plugins_linux_arm64-v8a_server_dir": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-server",
        "plugins_linux_arm64-v8a_server_network-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-server/network-manager",
        "plugins_linux_arm64-v8a_server_comms": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-server/comms",
        "plugins_linux_arm64-v8a_server_core": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-arm64-v8a-server/core",
        "plugins_linux_x86_64_client_artifact-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-client/artifact-manager",
        "plugins_linux_x86_64_client_dir": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-client",
        "plugins_linux_x86_64_client_network-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-client/network-manager",
        "plugins_linux_x86_64_client_comms": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-client/comms",
        "plugins_linux_x86_64_client_core": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-client/core",
        "plugins_linux_x86_64_server_artifact-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-server/artifact-manager",
        "plugins_linux_x86_64_server_dir": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-server",
        "plugins_linux_x86_64_server_network-manager": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-server/network-manager",
        "plugins_linux_x86_64_server_comms": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-server/comms",
        "plugins_linux_x86_64_server_core": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins/linux-x86_64-server/core",
        "plugins": f"{docker_rib_state_path}/deployments/local/test-deployment/plugins",
        "previous-runs": f"{docker_rib_state_path}/deployments/local/test-deployment/previous-run-logs",
        "race_configs": f"{docker_rib_state_path}/deployments/local/test-deployment/configs",
        "runtime-configs": f"{docker_rib_state_path}/deployments/local/test-deployment/runtime-configs",
        "network_manager_configs_base": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/network-manager",
        "comms_configs_base": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/comms",
        "templates": f"/race_in_the_box/rib/artifacts/deployments/local/templates",
        "vpn": f"{docker_rib_state_path}/deployments/local/test-deployment/vpn",
    }


def test_verify_expected_files(paths):
    docker_rib_state_path = RibDeployment.rib_config.DOCKER_RIB_STATE_PATH
    assert paths.files == {
        "channel_list": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/channel_list.json",
        "config": f"{docker_rib_state_path}/deployments/local/test-deployment/deployment_config.json",
        "docker_compose": f"{docker_rib_state_path}/deployments/local/test-deployment/docker-compose.yml",
        "metadata": f"{docker_rib_state_path}/deployments/local/test-deployment/deployment_metadata.json",
        "race_config": f"{docker_rib_state_path}/deployments/local/test-deployment/configs/race-config.json",
    }

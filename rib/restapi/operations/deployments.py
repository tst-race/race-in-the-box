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

""" Common deployment operation functions """

# Python Library Imports
from typing import Any, Dict

# Local Python Library Imports
from rib.deployment import RibDeployment
from rib.restapi.schemas.deployments import (
    BootstrapNodeParams,
    GenerateConfigParams,
    NodeOperationParams,
)


def generate_configs(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Generate deployment configs"""

    params = GenerateConfigParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    deployment.generate_plugin_or_channel_configs(
        network_manager_custom_args=params.network_manager_custom_args,
        comms_custom_args_map=params.comms_custom_args,
        artifact_manager_custom_args_map=params.artifact_manager_custom_args,
        max_iterations=params.max_iterations,
        force=params.force,
        skip_config_tar=params.skip_config_tar,
        timeout=params.timeout,
    )


def archive_node_configs(
    deployment_name: str, deployment_mode: str, data: Dict[str, Any]
):
    """Create node config archives"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.tar_configs(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )


def publish_node_configs(
    deployment_name: str, deployment_mode: str, data: Dict[str, Any]
):
    """Publish node configs"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.upload_configs(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )


def install_node_configs(
    deployment_name: str, deployment_mode: str, data: Dict[str, Any]
):
    """Install node configs"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.install_configs(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )


def bootstrap_node(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Bootstrap node into RACE network"""

    params = BootstrapNodeParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    deployment.bootstrap_node(
        force=params.force,
        introducer=params.introducer,
        target=params.target,
        passphrase=params.passphrase,
        architecture=params.architecture,
        timeout=params.timeout,
    )


def start_race_apps(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Start RACE apps"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.start(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )


def stop_race_apps(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Stop RACE apps"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.stop(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )


def clear_configs(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Clear configs & etc from nodes (and artifacts if bootstrapped)"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.clear(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )


def reset_to_initial_state(
    deployment_name: str, deployment_mode: str, data: Dict[str, Any]
):
    """Reset nodes back to initial state"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.reset(
        force=params.force,
        nodes=params.nodes,
        timeout=params.timeout,
    )

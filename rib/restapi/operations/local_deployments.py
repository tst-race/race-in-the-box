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

""" Local deployment operation functions """

# Python Library Imports
import os
import tempfile
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict

# Local Python Library Imports
from rib.deployment import RibLocalDeployment
from rib.restapi.schemas.local_deployments import (
    NodeOperationParams,
    StandUpLocalDeploymentParams,
    ValidatedCreateLocalDeploymentParams,
)
from rib.utils import general_utils


def create_local_deployment(data: Dict[str, Any]):
    """Create a local deployment"""

    params = ValidatedCreateLocalDeploymentParams.parse_obj(data)
    race_node_arch = (
        "arm64-v8a" if "arm" in os.environ.get("HOST_ARCHITECTURE", "") else "x86_64"
    )

    RibLocalDeployment.ensure_deployment_not_existing_or_fail(params.name, "local")

    with tempfile.NamedTemporaryFile() as range_config_file:
        general_utils.write_data_to_file(
            range_config_file.name, jsonable_encoder(params.range_config), "json"
        )

        RibLocalDeployment.create(
            create_command="Created from RiB UI",
            deployment_name=params.name,
            ## range-config
            range_config=range_config_file.name,
            disable_config_encryption=params.disable_config_encryption,
            ## node counts (uses range config)
            android_client_count=0,
            linux_client_count=0,
            linux_server_count=0,
            ## images
            android_client_image=params.android_client_image,
            linux_client_image=params.linux_client_image,
            linux_server_image=params.linux_server_image,
            # TODO registry_client_image=
            ## RACE version
            race_core=params.race_core,
            race_node_arch=race_node_arch,
            ## artifacts
            android_app=params.android_app,
            linux_app=params.linux_app,
            # TODO
            registry_app=None,
            node_daemon=params.node_daemon,
            network_manager_kit=params.network_manager_kit,
            comms_channels=params.comms_channels,
            comms_kits=params.comms_kits,
            artifact_manager_kits=params.artifact_manager_kits,
            cache=params.cache,
            fetch_plugins_on_start=params.fetch_plugins_on_start,
            ## Local Env
            enable_gpu=params.enable_gpu,
            # TODO android_client_accel=
            # TODO tmpfs_size=
            # TODO disable_elasticsearch_volume_mounts=
            # TODO disable_open_tracing=
            no_config_gen=params.no_config_gen,
            race_log_level=params.race_log_level,
        )


def stand_up_local_deployment(deployment_name: str, data: Dict[str, Any]):
    """Stand up a local deployment"""

    params = StandUpLocalDeploymentParams.parse_obj(data)

    deployment = RibLocalDeployment.get_existing_deployment_or_fail(
        deployment_name, "local"
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.up(
        force=params.force,
        nodes=params.nodes,
        no_publish=params.no_publish,
        timeout=params.timeout,
    )


def tear_down_local_deployment(deployment_name: str, data: Dict[str, Any]):
    """Tear down a local deployment"""

    params = NodeOperationParams.parse_obj(data)

    deployment = RibLocalDeployment.get_existing_deployment_or_fail(
        deployment_name, "local"
    )

    if params.nodes:
        params.nodes = deployment.get_nodes_from_regex(params.nodes)

    deployment.down(force=params.force, nodes=params.nodes, timeout=params.timeout)

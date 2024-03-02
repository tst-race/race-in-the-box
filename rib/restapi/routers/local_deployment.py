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

""" RiB /api/deployments/local router """

# Python Library Imports
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Local Python Library Imports
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.status.rib_deployment_status import Require
from rib.utils import general_utils
from rib.deployment.rib_deployment_config import (
    DeploymentMetadata,
    LocalDeploymentConfig,
)
from rib.restapi.dependencies import get_queue_operation
from rib.restapi.internal.models import OperationResponse
from rib.restapi.schemas.deployments import (
    ActiveDeployment,
    BootstrapNodeParams,
    DeploymentsList,
    GenerateConfigParams,
    GrandparentServiceStatusReport,
    NodeList,
    ParentContainerStatusReport,
    ParentNodeStatusReport,
    RangeConfig,
)
from rib.restapi.schemas.local_deployments import (
    CreateLocalDeploymentParams,
    NodeOperationParams,
    StandUpLocalDeploymentParams,
)
from rib.restapi.schemas.operations import OperationQueuedResult
from rib.utils.status_utils import AppStatus, DaemonStatus, RaceStatus
from rib.utils import error_utils, github_utils, plugin_utils

router = APIRouter(
    prefix="/api/deployments/local",
    tags=["Local deployments"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=DeploymentsList)
def get_local_deployments():
    """Get list of existing local deployments"""

    output = {}
    output["compatible"] = []
    output["incompatible"] = []

    rib_deployment_class = RibDeployment.get_deployment_class("local")

    deployments = (
        rib_deployment_class.get_defined_deployments()
    )  # Get Deployments on host

    if deployments.compatible:
        lists = []
        for deployment_name in sorted(deployments.compatible):
            lists.append({"name": deployment_name})
        output["compatible"] = lists

    if deployments.incompatible:
        lists = []
        for deployment in sorted(deployments.incompatible):
            lists.append(
                {"name": deployment.name, "rib_version": deployment.rib_version}
            )
        output["incompatible"] = lists

    return output


class DestinationDeployment(BaseModel):
    """Copy/move deployment destination"""

    name: str


@router.post(
    "/{old_name}/copy",
    response_model=OperationResponse,
    responses={422: {"description": "Destination already exists"}},
)
def copy_local_deployment(old_name: str, dest: DestinationDeployment):
    """Create a copy of a deployment"""

    try:
        current_deployment = RibDeployment.get_existing_deployment_or_fail(
            old_name, "local"
        )
    except:
        raise HTTPException(
            status_code=404,
            detail=f"deployment {old_name} doesn't exist",
        )

    try:
        RibDeployment.ensure_deployment_not_existing_or_fail(dest.name, "local")
    except:
        raise HTTPException(
            status_code=422, detail=f"deployment {dest.name} already exists"
        )

    reason = ""
    success = False

    try:
        current_deployment.copy(dest.name, f"copied from {old_name}")
        success = True
    except Exception as err:
        reason = f"failed to copy deployment: {err}"

    return {"success": success, "reason": reason}


@router.put(
    "/{old_name}/name",
    response_model=OperationResponse,
    responses={422: {"description": "Destination already exists"}},
)
def rename_local_deployment(
    old_name: str, dest: DestinationDeployment, force: bool = False
):
    """Rename an existing deployment"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(old_name, "local")
    except:
        raise HTTPException(
            status_code=404, detail=f"deployment {old_name} doesn't exist"
        )

    try:
        RibDeployment.ensure_deployment_not_existing_or_fail(dest.name, "local")
    except:
        raise HTTPException(
            status_code=422, detail=f"deployment {dest.name} already exists"
        )

    reason = ""
    success = False

    try:
        deployment.rename(dest.name, force)
        success = True
    except Exception as err:
        reason = f"failed to rename deployment: {err}"

    return {"success": success, "reason": reason}


@router.delete("/{name}", response_model=OperationResponse)
def delete_local_deployment(name: str, force: bool = False):
    """Delete a deployment"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    try:
        deployment.remove(force)  # maybe down deployment if force
    except:
        return {
            "success": False,
            "reason": f"failed to remove deployment {name}",
        }

    return {
        "success": True,
        "reason": f"successfully deleted deployment {name}",
    }


###
# Retrieval routes
###


@router.get("/active", response_model=ActiveDeployment)
def get_active_local_deployment():
    """Get the active local deployment, if any"""

    return {"name": RibDeployment.get_active("local")["local"]}


class LocalDeploymentInfo(BaseModel):
    """Local deployment information"""

    config: LocalDeploymentConfig
    metadata: DeploymentMetadata


@router.get("/{name}/info", response_model=LocalDeploymentInfo)
def get_local_deployment_info(name: str):
    """Get config and metadata for a deployment"""
    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return {"config": deployment.config, "metadata": deployment.metadata}


@router.get("/{name}/status/nodes", response_model=ParentNodeStatusReport)
def get_node_status(name: str):
    """Get status of nodes in a deployment"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return deployment.status.get_app_status_report()


@router.get("/{name}/status/containers", response_model=ParentContainerStatusReport)
def get_container_status(name: str):
    """Get status of containers in a deployment"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return deployment.status.get_container_status_report()


@router.get("/{name}/status/services", response_model=GrandparentServiceStatusReport)
def get_service_status(name: str):
    """Get status of services in a deployment"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return deployment.status.get_services_status_report()


@router.get("/{name}/range-config", response_model=RangeConfig)
def get_range_config(name: str):
    """Get range configuration from deployment"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return general_utils.load_file_into_memory(
        deployment.paths.files["race_config"], data_format="json"
    )


@router.get("/{name}/nodes", response_model=NodeList)
def get_nodes(
    name: str,
    app: Optional[AppStatus] = None,
    daemon: Optional[DaemonStatus] = None,
    race: Optional[RaceStatus] = None,
):
    """Get deployment nodes matching status filters"""

    try:
        deployment = RibDeployment.get_existing_deployment_or_fail(name, "local")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return {
        "nodes": deployment.status.get_nodes_that_match_status(
            action="",
            force=False,
            quiet=True,
            require=Require.NONE,
            app_status=[app] if app else None,
            daemon_status=[daemon] if daemon else None,
            race_status=[race] if race else None,
        )
    }


###
# Operation routes
###


def _parse_kit_source(value: str, core=False) -> plugin_utils.KitSource:
    source = plugin_utils.parse_kit_source(value)
    if core:
        return plugin_utils.apply_race_core_defaults(source)
    return plugin_utils.apply_kit_defaults(source)


def _parse_kit_sources(values: List[str]) -> List[plugin_utils.KitSource]:
    return [_parse_kit_source(value) for value in values]


@router.post("", response_model=OperationQueuedResult)
def create_local_deployment(
    data: CreateLocalDeploymentParams, queue_operation=Depends(get_queue_operation)
):
    """Create a local deployment"""

    try:
        data_dict = data.dict()
        data_dict["race_core"] = _parse_kit_source(data.race_core, core=True)
        data_dict["android_app"] = _parse_kit_source(data.android_app)
        data_dict["linux_app"] = _parse_kit_source(data.linux_app)
        data_dict["node_daemon"] = _parse_kit_source(data.node_daemon)
        data_dict["network_manager_kit"] = _parse_kit_source(data.network_manager_kit)
        data_dict["comms_kits"] = _parse_kit_sources(data.comms_kits)
        data_dict["artifact_manager_kits"] = _parse_kit_sources(
            data.artifact_manager_kits
        )

        data_dict["android_client_image"] = github_utils.apply_defaults_to_image(
            data.android_client_image, "race-runtime-android-x86_64"
        )
        data_dict["linux_client_image"] = github_utils.apply_defaults_to_image(
            data.linux_client_image, "race-runtime-linux"
        )
        data_dict["linux_server_image"] = github_utils.apply_defaults_to_image(
            data.linux_server_image, "race-runtime-linux"
        )
    except error_utils.RIB000 as err:
        raise HTTPException(
            status_code=400,
            detail=getattr(err, "msg", ""),
        )

    return queue_operation(
        target=f"deployment:local:{data.name}",
        name=f"Create local deployment: {data.name}",
        function="rib.restapi.operations.local_deployments.create_local_deployment",
        data=data_dict,
    )


def _operation_name(action: str, nodes: Optional[List[str]], name: str) -> str:
    """Create an operation name for an action against the nodes of a deployment"""
    if nodes:
        return f"{action} {len(nodes)} nodes in local deployment: {name}"
    return f"{action} local deployment: {name}"


@router.post(
    "/{name}/operations/generate-configs", response_model=OperationQueuedResult
)
def generate_configs(
    name: str,
    data: GenerateConfigParams,
    queue_operation=Depends(get_queue_operation),
):
    """Generate deployment configs"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Generate configs for", None, name),
        function="rib.restapi.operations.deployments.generate_configs",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/archive-configs", response_model=OperationQueuedResult)
def archive_node_configs(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Create node config archives"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Create config archives for", data.nodes, name),
        function="rib.restapi.operations.deployments.archive_node_configs",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/up", response_model=OperationQueuedResult)
def stand_up_local_deployment(
    name: str,
    data: StandUpLocalDeploymentParams,
    queue_operation=Depends(get_queue_operation),
):
    """Stand up a local deployment"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Stand up", data.nodes, name),
        function="rib.restapi.operations.local_deployments.stand_up_local_deployment",
        deployment_name=name,
        data=data,
    )


@router.post("/{name}/operations/publish-configs", response_model=OperationQueuedResult)
def publish_node_configs(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Publish node configs"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Publish configs for", data.nodes, name),
        function="rib.restapi.operations.deployments.publish_node_configs",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/install-configs", response_model=OperationQueuedResult)
def install_node_configs(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Install node configs"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Install configs for", data.nodes, name),
        function="rib.restapi.operations.deployments.install_node_configs",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/bootstrap", response_model=OperationQueuedResult)
def bootstrap_node(
    name: str,
    data: BootstrapNodeParams,
    queue_operation=Depends(get_queue_operation),
):
    """Bootstrap node into RACE network"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name(f"Bootstrap {data.target} into", None, name),
        function="rib.restapi.operations.deployments.bootstrap_node",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/start", response_model=OperationQueuedResult)
def start_race_apps(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Start RACE apps"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Start", data.nodes, name),
        function="rib.restapi.operations.deployments.start_race_apps",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/stop", response_model=OperationQueuedResult)
def stop_race_apps(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Stop RACE apps"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Stop", data.nodes, name),
        function="rib.restapi.operations.deployments.stop_race_apps",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/clear", response_model=OperationQueuedResult)
def clear_configs(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Clear configs & etc from nodes (and artifacts if bootstrapped)"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Clear", data.nodes, name),
        function="rib.restapi.operations.deployments.clear_configs",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/reset", response_model=OperationQueuedResult)
def reset_to_initial_state(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Reset nodes back to initial state"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Reset", data.nodes, name),
        function="rib.restapi.operations.deployments.reset_to_initial_state",
        deployment_name=name,
        deployment_mode="local",
        data=data,
    )


@router.post("/{name}/operations/down", response_model=OperationQueuedResult)
def tear_down_local_deployment(
    name: str,
    data: NodeOperationParams,
    queue_operation=Depends(get_queue_operation),
):
    """Tear down a local deployment"""

    return queue_operation(
        target=f"deployment:local:{name}",
        name=_operation_name("Tear down", data.nodes, name),
        function="rib.restapi.operations.local_deployments.tear_down_local_deployment",
        deployment_name=name,
        data=data,
    )

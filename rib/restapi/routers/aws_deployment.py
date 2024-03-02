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

""" RiB /api/deployments/aws router """

# Python Library Imports
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Local Python Library Imports
from rib.deployment.rib_aws_deployment import RibAwsDeployment
from rib.deployment.status.rib_deployment_status import Require
from rib.utils import general_utils
from rib.deployment.rib_deployment_config import (
    DeploymentMetadata,
    AwsDeploymentConfig,
)
from rib.restapi.dependencies import get_queue_operation
from rib.restapi.schemas.deployments import (
    ActiveDeployment,
    BootstrapNodeParams,
    DeploymentsList,
    GenerateConfigParams,
    GrandparentServiceStatusReport,
    NodeList,
    NodeOperationParams,
    ParentNodeStatusReport,
    RangeConfig,
)
from rib.restapi.schemas.aws_deployments import (
    StandUpAwsDeploymentParams,
    TearDownAwsDeploymentParams,
)
from rib.restapi.schemas.operations import OperationQueuedResult
from rib.utils.status_utils import AppStatus, DaemonStatus, RaceStatus

router = APIRouter(
    prefix="/api/deployments/aws",
    tags=["AWS deployments"],
    responses={404: {"description": "Not found"}},
)


###
# Retrieval routes
###


@router.get("", response_model=DeploymentsList)
def get_aws_deployments():
    """Get list of existing AWS deployments"""

    output = {}
    output["compatible"] = []
    output["incompatible"] = []

    deployments = RibAwsDeployment.get_defined_deployments()

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


@router.get("/active", response_model=ActiveDeployment)
def get_active_aws_deployment():
    """Get the active AWS deployment, if any"""

    # TODO need to query a particular AWS host env
    # return {"name": RibAwsDeployment.get_active_deployment_name()}


class AwsDeploymentInfo(BaseModel):
    """AWS deployment information"""

    config: AwsDeploymentConfig
    metadata: DeploymentMetadata


@router.get("/{name}/info", response_model=AwsDeploymentInfo)
def get_aws_deployment_info(name: str):
    """Get config and metadata for a deployment"""
    try:
        deployment = RibAwsDeployment.get_existing_deployment_or_fail(name, "aws")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return {"config": deployment.config, "metadata": deployment.metadata}


@router.get("/{name}/status/nodes", response_model=ParentNodeStatusReport)
def get_node_status(name: str):
    """Get status of nodes in a deployment"""

    try:
        deployment = RibAwsDeployment.get_existing_deployment_or_fail(name, "aws")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return deployment.status.get_app_status_report()


@router.get("/{name}/status/services", response_model=GrandparentServiceStatusReport)
def get_service_status(name: str):
    """Get status of services in a deployment"""

    try:
        deployment = RibAwsDeployment.get_existing_deployment_or_fail(name, "aws")
    except:
        raise HTTPException(status_code=404, detail=f"deployment {name} doesn't exist")

    return deployment.status.get_services_status_report()


@router.get("/{name}/range-config", response_model=RangeConfig)
def get_range_config(name: str):
    """Get range configuration from deployment"""

    try:
        deployment = RibAwsDeployment.get_existing_deployment_or_fail(name, "aws")
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
        deployment = RibAwsDeployment.get_existing_deployment_or_fail(name, "aws")
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


def _operation_name(action: str, nodes: Optional[List[str]], name: str) -> str:
    """Create an operation name for an action against the nodes of a deployment"""
    if nodes:
        return f"{action} {len(nodes)} nodes in AWS deployment: {name}"
    return f"{action} AWS deployment: {name}"


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
        target=f"deployment:aws:{name}",
        name=_operation_name("Generate configs for", None, name),
        function="rib.restapi.operations.deployments.generate_configs",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Create config archives for", data.nodes, name),
        function="rib.restapi.operations.deployments.archive_node_configs",
        deployment_name=name,
        deployment_mode="aws",
        data=data,
    )


@router.post("/{name}/operations/up", response_model=OperationQueuedResult)
def stand_up_aws_deployment(
    name: str,
    data: StandUpAwsDeploymentParams,
    queue_operation=Depends(get_queue_operation),
):
    """Stand up an AWS deployment"""

    return queue_operation(
        target=f"deployment:aws:{name}",
        name=_operation_name("Stand up", None, name),
        function="rib.restapi.operations.aws_deployments.stand_up_aws_deployment",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Publish configs for", data.nodes, name),
        function="rib.restapi.operations.deployments.publish_node_configs",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Install configs for", data.nodes, name),
        function="rib.restapi.operations.deployments.install_node_configs",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name(f"Bootstrap {data.target} into", None, name),
        function="rib.restapi.operations.deployments.bootstrap_node",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Start", data.nodes, name),
        function="rib.restapi.operations.deployments.start_race_apps",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Stop", data.nodes, name),
        function="rib.restapi.operations.deployments.stop_race_apps",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Clear", data.nodes, name),
        function="rib.restapi.operations.deployments.clear_configs",
        deployment_name=name,
        deployment_mode="aws",
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
        target=f"deployment:aws:{name}",
        name=_operation_name("Reset", data.nodes, name),
        function="rib.restapi.operations.deployments.reset_to_initial_state",
        deployment_name=name,
        deployment_mode="aws",
        data=data,
    )


@router.post("/{name}/operations/down", response_model=OperationQueuedResult)
def tear_down_aws_deployment(
    name: str,
    data: TearDownAwsDeploymentParams,
    queue_operation=Depends(get_queue_operation),
):
    """Tear down an AWS deployment"""

    return queue_operation(
        target=f"deployment:aws:{name}",
        name=_operation_name("Tear down", None, name),
        function="rib.restapi.operations.aws_deployments.tear_down_aws_deployment",
        deployment_name=name,
        data=data,
    )

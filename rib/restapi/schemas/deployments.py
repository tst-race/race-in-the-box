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

""" Common deployment API schemas """

# Python Library Imports
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from rib.utils.status_utils import (
    AppStatus,
    ArtifactsStatus,
    ConfigsStatus,
    ContainerStatus,
    DaemonStatus,
    EtcStatus,
    NodeStatus,
    ParentStatus,
    RaceStatus,
    ServiceStatus,
)


###
# Lists
###

# Can't use the existing types in rib_deployment_config because they are named tuples, which
# don't work with pydantic


class CompatibleDeployment(BaseModel):
    """Compatible deployment"""

    name: str


class IncompatibleDeployment(BaseModel):
    """Incompatible deployment"""

    name: str
    rib_version: str


class DeploymentsList(BaseModel):
    """List of deployments"""

    compatible: List[CompatibleDeployment]
    incompatible: List[IncompatibleDeployment]


class ActiveDeployment(BaseModel):
    """Active deployment, if any"""

    name: str = None


###
# Range config
###


class NodeConfig(BaseModel):
    """Node configuration"""

    bridge: bool
    enclave: str
    environment: str
    genesis: bool
    gpu: bool
    identities: List[str]
    name: str
    nat: bool
    platform: str
    architecture: Optional[str]
    type: str


class BastionConfig(BaseModel):
    """Bastion configuration"""

    range_ip: Optional[str]


class PortMapping(BaseModel):
    """Enclave port mapping configuration"""

    hosts: List[str]
    port: str


class EnclaveConfig(BaseModel):
    """Enclave configuration"""

    name: str
    ip: str
    port_mapping: Dict[str, PortMapping]


class AccessConfig(BaseModel):
    """Service access configuration"""

    protocol: str
    url: str
    userFmt: Optional[str]
    password: Optional[str]


class ServiceConfig(BaseModel):
    """Service configuration"""

    name: str
    access: List[AccessConfig]
    type: str


class RangeDefinition(BaseModel):
    """Range definition"""

    RACE_nodes: List[NodeConfig]
    bastion: Optional[BastionConfig]
    enclaves: List[EnclaveConfig]
    name: str
    services: List[ServiceConfig]


class RangeConfig(BaseModel):
    """Range configuration"""

    range: RangeDefinition


###
# Status
###


class BaseStatusReport(BaseModel):
    reason: Optional[str] = Field(..., nullable=True)


class DaemonStatusReport(BaseStatusReport):
    status: DaemonStatus


class ArtifactsStatusReport(BaseStatusReport):
    status: ArtifactsStatus


class AppStatusReport(BaseStatusReport):
    status: AppStatus


class RaceStatusReport(BaseStatusReport):
    status: RaceStatus


class ConfigsStatusReport(BaseStatusReport):
    status: ConfigsStatus


class EtcStatusReport(BaseStatusReport):
    status: EtcStatus


class NodeDetailStatusReport(BaseModel):
    daemon: DaemonStatusReport
    artifacts: ArtifactsStatusReport
    app: AppStatusReport
    race: RaceStatusReport
    configs: ConfigsStatusReport
    etc: EtcStatusReport


class NodeStatusReport(BaseModel):
    status: NodeStatus
    children: NodeDetailStatusReport


class ParentNodeStatusReport(BaseModel):
    status: ParentStatus
    children: Dict[str, NodeStatusReport]


class ContainerStatusReport(BaseModel):
    status: ContainerStatus


class ParentContainerStatusReport(BaseModel):
    status: ParentStatus
    children: Dict[str, ContainerStatusReport]


class ServiceStatusReport(BaseModel):
    status: ServiceStatus
    reason: Optional[str]


class ParentServiceStatusReport(BaseModel):
    status: ParentStatus
    children: Dict[str, ServiceStatusReport]


class GrandparentServiceStatusReport(BaseModel):
    status: ParentStatus
    children: Dict[str, ParentServiceStatusReport]


class NodeList(BaseModel):
    """List of nodes"""

    nodes: List[str]


###
# Operation Payloads
###


class GenerateConfigParams(BaseModel):
    """Config generation request parameters"""

    network_manager_custom_args: str = None
    comms_custom_args: Dict[str, str] = None
    artifact_manager_custom_args: Dict[str, str] = None
    max_iterations: int = 20
    force: bool = False
    skip_config_tar: bool = False
    timeout: int = 300


class NodeOperationParams(BaseModel):
    """Generic node operation request parameters"""

    force: bool = False
    nodes: Optional[List[str]] = Field(..., nullable=True)
    timeout: int = 300


class ArchitectureEnum(str, Enum):
    x86 = "x86_64"
    arm = "arm64-v8a"


class BootstrapNodeParams(BaseModel):
    """Bootstrap node request parameters"""

    force: bool = False
    introducer: str
    target: str
    passphrase: str
    architecture: ArchitectureEnum
    timeout: int = 600

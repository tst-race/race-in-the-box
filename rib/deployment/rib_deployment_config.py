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
    Configuration types for deployments
"""

# Python Library Imports
from pydantic import BaseModel
from typing import (
    Any,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Set,
)

# Local Python Library Imports
from rib.config.rib_host_env import RibHostEnvConfig
from rib.utils.general_utils import Subscriptable
from rib.utils.plugin_utils import (
    KitCacheMetadata,
    KitConfig,
    KitSource,
)


###
# Types
###


class NodeConfig(BaseModel, Subscriptable):
    """Configuration for a specific RACE node"""

    platform: str
    architecture: str
    node_type: str
    genesis: bool
    bridge: bool
    gpu: bool


class ImageConfig(BaseModel, Subscriptable):
    """Configuration for a specific RACE Image"""

    tag: str
    platform: str
    architecture: str
    node_type: str


class ChannelConfig(BaseModel, Subscriptable):
    """Configuration for a comms channel"""

    name: str
    kit_name: str
    enabled: bool


class BaseDeploymentConfig(BaseModel, Subscriptable):
    """Base deployment configuration"""

    name: str
    mode: str
    rib_version: str
    race_core: KitSource
    android_app: Optional[KitConfig]
    linux_app: KitConfig
    registry_app: Optional[KitConfig]
    node_daemon: KitConfig
    network_manager_kit: KitConfig
    comms_channels: List[ChannelConfig]
    comms_kits: List[KitConfig]
    artifact_manager_kits: List[KitConfig]
    nodes: Mapping[str, NodeConfig]
    images: List[ImageConfig]
    race_encryption_type: str
    log_metadata_to_es: bool = True
    es_metadata_index: str = "deployment-metadata-log"


class AwsDeploymentConfig(BaseDeploymentConfig):
    """AWS deployment configuration"""

    aws_env_name: str
    bastion_image: str


class LocalDeploymentConfig(BaseDeploymentConfig):
    """Local deployment configuration"""

    android_container_acceleration: bool
    tmpfs_size: Optional[int]
    host_env_config: RibHostEnvConfig


class DeploymentMetadata(BaseModel, Subscriptable):
    """Deployment metadata"""

    rib_image: Mapping[str, Any]

    create_command: str
    create_date: str

    race_core_cache: KitCacheMetadata
    android_app_cache: Optional[KitCacheMetadata]
    linux_app_cache: KitCacheMetadata
    registry_app_cache: Optional[KitCacheMetadata]
    node_daemon_cache: KitCacheMetadata
    network_manager_kit_cache: KitCacheMetadata
    comms_kits_cache: Mapping[str, KitCacheMetadata]
    artifact_manager_kits_cache: Mapping[str, KitCacheMetadata]

    last_config_gen_command: Optional[str] = None
    last_config_gen_time: Optional[str] = None

    last_up_command: Optional[str] = None
    last_up_time: Optional[str] = None

    last_start_command: Optional[str] = None
    last_start_time: Optional[str] = None

    last_stop_command: Optional[str] = None
    last_stop_time: Optional[str] = None

    last_down_command: Optional[str] = None
    last_down_time: Optional[str] = None


class IncompatibleDeployment(NamedTuple):
    """Incompatible deployment"""

    name: str
    rib_version: str


class DefinedDeployments(NamedTuple):
    """Names of defined deployments"""

    compatible: Set[str]
    incompatible: Set[IncompatibleDeployment]

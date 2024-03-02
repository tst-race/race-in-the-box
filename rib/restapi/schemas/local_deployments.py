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

""" Local deployment API schemas """

# Python Library Imports
from pydantic import BaseModel
from typing import List

from rib.restapi.schemas.deployments import NodeOperationParams, RangeConfig
from rib.utils import plugin_utils


###
# Operation Payloads
###


class CreateLocalDeploymentParams(BaseModel):
    """Local deployment creation request parameters"""

    name: str
    race_core: str
    network_manager_kit: str
    comms_channels: List[str]
    comms_kits: List[str]
    artifact_manager_kits: List[str]
    android_app: str
    linux_app: str
    node_daemon: str
    android_client_image: str
    linux_client_image: str
    linux_server_image: str
    range_config: RangeConfig
    fetch_plugins_on_start: bool = False
    no_config_gen: bool = False
    disable_config_encryption: bool = False
    enable_gpu: bool = False
    cache: str = "auto"
    race_log_level: str = "info"


class ValidatedCreateLocalDeploymentParams(CreateLocalDeploymentParams):
    race_core: plugin_utils.KitSource
    android_app: plugin_utils.KitSource
    linux_app: plugin_utils.KitSource
    node_daemon: plugin_utils.KitSource
    network_manager_kit: plugin_utils.KitSource
    comms_kits: List[plugin_utils.KitSource]
    artifact_manager_kits: List[plugin_utils.KitSource]


class StandUpLocalDeploymentParams(NodeOperationParams):
    """Stand up local deployment request parameters"""

    no_publish: bool = False

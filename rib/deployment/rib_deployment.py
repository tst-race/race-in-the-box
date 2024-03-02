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
        The RibDeployment Class is a representation of RiB Deployments
"""

# Python Library Imports
import click
import copy
import logging
from opensearchpy import OpenSearch as Elasticsearch
from opensearchpy.exceptions import OpenSearchWarning as ElasticsearchWarning
import os
from rib.deployment.paths.rib_deployment_paths import RibDeploymentPaths
import sh
import shutil
import tarfile
import time
import io
import warnings
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pytz
from functools import cached_property
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)
import re
from rib.utils import elasticsearch_utils, plugin_utils, subprocess_utils

# Local Python Library Imports
import rib.deployment.rib_deployment_artifacts as deployment_artifacts
from rib.config import rib_host_env
from rib.deployment.rib_deployment_config import (
    BaseDeploymentConfig,
    ChannelConfig,
    DefinedDeployments,
    DeploymentMetadata,
    ImageConfig,
    IncompatibleDeployment,
    NodeConfig,
)
import rib.deployment.rib_deployment_rpc as rib_deployment_rpc
import rib.deployment.status.rib_deployment_status as rib_deployment_status
from rib.deployment.status.rib_deployment_status import Require
from rib.utils import (
    adb_utils,
    config_utils,
    error_utils,
    file_server_utils,
    general_utils,
    race_node_utils,
    voa_utils,
    rib_utils,
    status_utils,
)
from rib.utils import plugin_utils
from rib.utils.plugin_utils import CacheStrategy

# Set up logger
logger = logging.getLogger(__name__)


class RibDeployment(ABC):
    """
    Purpose:
        The RibDeployment Class is a representation of RiB Deployments
    """

    ###
    # Class Attributes
    ###

    # Rib Information
    rib_mode = None

    # Config Information
    rib_config = rib_utils.load_race_global_configs()

    # RiB dirs and files info
    paths: RibDeploymentPaths = None
    pathsClass = RibDeploymentPaths

    # Deployment config class, to be overridden by subclasses.
    config_class = BaseDeploymentConfig

    # Host Environment Information
    host_env_config = rib_host_env.get_rib_env_config()

    # Port Information
    # TODO: change this to a namedtuple. This will make the data structure immutable,
    #       and also will allow fields to be accessed by name, e.g.
    #           self.ports.race_api_port
    #       instead of
    #           self.race_api_port["race_api_port"]
    ports = {  # For interaction with nodes from Flask/Each Other. 5k space for each
        "race_api_port": 5_000,
        "vnc_port": 5_901,
        "server_start_port_api": 30_000,
        "client_start_port_api": 25_000,
        "client_start_port_vnc": 35_000,
    }

    # Services used to support opentracing
    opentracing_services = [
        "jaeger-query",
        "elasticsearch",
        "kibana",
        "jaeger-collector",
        "graph_renderer",
    ]
    # Services used to support orchestration management
    orchestration_services = [
        "dnsproxy",
        "openvpn",
        "rib-redis",
        "rib-file-server",
    ]

    aux_services = opentracing_services + orchestration_services

    DEPLOYMENT_NAME_CONTAINER_LABEL_KEY = "race.rib.deployment-name"
    DEPLOYMENT_TYPE_CONTAINER_LABEL_KEY = "race.rib.deployment-type"

    # Max number of server or client nodes. (10k of each)
    MAX_NODES = 10_000

    # Default testapp-config.json settings
    PERIOD_DEFAULT = 3
    TIME_TO_LIVE_DEFAULT = 3

    ###
    # Instance attributes
    ###

    metadata: DeploymentMetadata
    config: BaseDeploymentConfig

    _race_node_interface: Optional[race_node_utils.RaceNodeInterface] = None
    _file_server_client: Optional[file_server_utils.FileServerClient] = None

    ###
    # Lifecycle Methods
    ###

    def __init__(
        self, config: BaseDeploymentConfig, metadata: DeploymentMetadata
    ) -> None:
        """
        Purpose:
            Initialize the base deployment object.
        Args:
            config: Base deployment configuration
            metadata: Deployment metadata
        Returns:
            N/A
        """

        self.config = config
        self.metadata = metadata

    ###
    # Deployment Properties
    ###

    @cached_property
    def cached_image_lists(self) -> Dict[str, Any]:
        """Initial set of cached image propertes"""
        image_nodes_to_tags = {}
        for image in self.config["images"]:
            image_node = f'{image["platform"]}_{image["architecture"]}_{image["node_type"]}_image'
            image_nodes_to_tags[image_node] = image["tag"]
        return image_nodes_to_tags

    @cached_property
    def android_x86_64_client_image(self):
        return self.cached_image_lists.get("android_x86_64_client_image", None)

    @cached_property
    def android_arm64_v8a_client_image(self):
        return self.cached_image_lists.get("android_arm64-v8a_client_image", None)

    @cached_property
    def linux_x86_64_client_image(self):
        return self.cached_image_lists.get("linux_x86_64_client_image", None)

    @cached_property
    def linux_arm64_v8a_client_image(self):
        return self.cached_image_lists.get("linux_arm64-v8a_client_image", None)

    @cached_property
    def linux_x86_64_server_image(self):
        return self.cached_image_lists.get("linux_x86_64_server_image", None)

    @cached_property
    def linux_arm64_v8a_server_image(self):
        return self.cached_image_lists.get("linux_arm64-v8a_server_image", None)

    @cached_property
    def cached_node_lists(self) -> Dict[str, Any]:
        """Initial set of cached node propertes"""
        # Android Clients
        android_client_personas = []
        android_genesis_client_personas = []
        android_bootstrap_client_personas = []
        android_bridge_client_personas = []

        # Linux Clients
        linux_client_personas = []
        linux_genesis_client_personas = []
        linux_bootstrap_client_personas = []
        linux_bridge_client_personas = []

        # Linux Servers
        linux_server_personas = []
        linux_genesis_server_personas = []
        linux_bootstrap_server_personas = []
        linux_bridge_server_personas = []

        # Registry Clients
        registry_client_personas = []
        genesis_registry_client_personas = []
        bootstrap_registry_client_personas = []

        # GPU
        gpu_client_personas = []
        gpu_server_personas = []
        gpu_registry_client_personas = []

        # Architecture-specific nodes
        arm_client_personas = []
        arm_server_personas = []
        x86_client_personas = []
        x86_server_personas = []

        for persona, node in self.config["nodes"].items():
            if node["platform"] == "android":
                android_client_personas.append(persona)
                if node["genesis"]:
                    android_genesis_client_personas.append(persona)
                else:
                    android_bootstrap_client_personas.append(persona)
                if node["bridge"]:
                    android_bridge_client_personas.append(persona)
                elif node["architecture"] == "x86_64":
                    x86_client_personas.append(persona)
                else:
                    arm_client_personas.append(persona)
            elif node["platform"] == "linux":
                if node["node_type"] == "client":
                    linux_client_personas.append(persona)
                    if node["genesis"]:
                        linux_genesis_client_personas.append(persona)
                    else:
                        linux_bootstrap_client_personas.append(persona)
                    if node["bridge"]:
                        linux_bridge_client_personas.append(persona)
                    elif node["architecture"] == "x86_64":
                        x86_client_personas.append(persona)
                    else:
                        arm_client_personas.append(persona)
                    if node["gpu"]:
                        gpu_client_personas.append(persona)
                elif node["node_type"] == "server":
                    linux_server_personas.append(persona)
                    if node["genesis"]:
                        linux_genesis_server_personas.append(persona)
                    else:
                        linux_bootstrap_server_personas.append(persona)
                    if node["bridge"]:
                        linux_bridge_server_personas.append(persona)
                    elif node["architecture"] == "x86_64":
                        x86_server_personas.append(persona)
                    else:
                        arm_server_personas.append(persona)
                    if node["gpu"]:
                        gpu_server_personas.append(persona)
                elif node["node_type"] == "registry":
                    registry_client_personas.append(persona)
                    if node["genesis"]:
                        genesis_registry_client_personas.append(persona)
                    else:
                        bootstrap_registry_client_personas.append(persona)
                    if node["architecture"] == "x86_64":
                        x86_client_personas.append(persona)
                    else:
                        arm_client_personas.append(persona)
                    if node["gpu"]:
                        gpu_registry_client_personas.append(persona)

        return {
            "android_client_personas": android_client_personas,
            "android_genesis_client_personas": android_genesis_client_personas,
            "android_bootstrap_client_personas": android_bootstrap_client_personas,
            "android_bridge_client_personas": android_bridge_client_personas,
            "linux_client_personas": linux_client_personas,
            "linux_genesis_client_personas": linux_genesis_client_personas,
            "linux_bootstrap_client_personas": linux_bootstrap_client_personas,
            "linux_bridge_client_personas": linux_bridge_client_personas,
            "linux_server_personas": linux_server_personas,
            "linux_genesis_server_personas": linux_genesis_server_personas,
            "linux_bootstrap_server_personas": linux_bootstrap_server_personas,
            "linux_bridge_server_personas": linux_bridge_server_personas,
            "registry_client_personas": registry_client_personas,
            "genesis_registry_client_personas": genesis_registry_client_personas,
            "bootstrap_registry_client_personas": bootstrap_registry_client_personas,
            "gpu_registry_client_personas": gpu_registry_client_personas,
            "gpu_client_personas": gpu_client_personas,
            "gpu_server_personas": gpu_server_personas,
            "arm64-v8a_client_personas": arm_client_personas,
            "arm64-v8a_server_personas": arm_server_personas,
            "x86_64_client_personas": x86_client_personas,
            "x86_64_server_personas": x86_server_personas,
        }

    @cached_property
    def android_client_personas(self) -> List[str]:
        """List of Android client node personas"""
        return self.cached_node_lists["android_client_personas"]

    @cached_property
    def android_bootstrap_client_personas(self) -> List[str]:
        """List of non-genesis Android client node personas"""
        return self.cached_node_lists["android_bootstrap_client_personas"]

    @cached_property
    def android_genesis_client_personas(self) -> List[str]:
        """List of genesis Android client node personas"""
        return self.cached_node_lists["android_genesis_client_personas"]

    @cached_property
    def android_bridge_client_personas(self) -> List[str]:
        """List of bridged Android client node personas"""
        return self.cached_node_lists["android_bridge_client_personas"]

    @cached_property
    def linux_client_personas(self) -> List[str]:
        """List of Linux client node personas"""
        return self.cached_node_lists["linux_client_personas"]

    @cached_property
    def linux_bootstrap_client_personas(self) -> List[str]:
        """List of non-genesis Linux client node personas"""
        return self.cached_node_lists["linux_bootstrap_client_personas"]

    @cached_property
    def linux_genesis_client_personas(self) -> List[str]:
        """List of genesis Linux client node personas"""
        return self.cached_node_lists["linux_genesis_client_personas"]

    @cached_property
    def linux_bridge_client_personas(self) -> List[str]:
        """List of bridged Linux client node personas"""
        return self.cached_node_lists["linux_bridge_client_personas"]

    @cached_property
    def client_personas(self) -> List[str]:
        """List of client node personas"""
        return self.android_client_personas + self.linux_client_personas

    @cached_property
    def bootstrap_client_personas(self) -> List[str]:
        """List of non-genesis client node personas"""
        return (
            self.android_bootstrap_client_personas
            + self.linux_bootstrap_client_personas
        )

    @cached_property
    def genesis_client_personas(self) -> List[str]:
        """List of genesis client node personas"""
        return self.android_genesis_client_personas + self.linux_genesis_client_personas

    @cached_property
    def bridge_client_personas(self) -> List[str]:
        """List of bridged client node personas"""
        return self.android_bridge_client_personas + self.linux_bridge_client_personas

    @cached_property
    def linux_server_personas(self) -> List[str]:
        """List of Linux server node personas"""
        return self.cached_node_lists["linux_server_personas"]

    @cached_property
    def linux_bootstrap_server_personas(self) -> List[str]:
        """List of non-genesis Linux server node personas"""
        return self.cached_node_lists["linux_bootstrap_server_personas"]

    @cached_property
    def linux_genesis_server_personas(self) -> List[str]:
        """List of genesis Linux server node personas"""
        return self.cached_node_lists["linux_genesis_server_personas"]

    @cached_property
    def linux_bridge_server_personas(self) -> List[str]:
        """List of bridged Linux server node personas"""
        return self.cached_node_lists["linux_bridge_server_personas"]

    @cached_property
    def server_personas(self) -> List[str]:
        """List of server node personas"""
        return self.linux_server_personas

    @cached_property
    def registry_personas(self) -> List[str]:
        """List of Registry Client Personas"""
        return self.cached_node_lists["registry_client_personas"]

    @cached_property
    def genesis_registry_personas(self) -> List[str]:
        """List of Genesis Registry Client Personas"""
        return self.cached_node_lists["genesis_registry_client_personas"]

    @cached_property
    def bootstrap_registry_personas(self) -> List[str]:
        """List of Bootstrap Registry Client Personas"""
        return self.cached_node_lists["bootstrap_registry_client_personas"]

    @cached_property
    def gpu_registry_personas(self) -> List[str]:
        """List of GPU Registry Client Personas"""
        return self.cached_node_lists["gpu_registry_client_personas"]

    @cached_property
    def bridge_server_personas(self) -> List[str]:
        """List of bridged server node personas"""
        return self.linux_bridge_server_personas

    @cached_property
    def bridge_personas(self) -> List[str]:
        """List of all bridged node personas"""
        return self.bridge_client_personas + self.bridge_server_personas

    @cached_property
    def linux_personas(self) -> List[str]:
        """List of all linux node personas"""
        return (
            self.linux_client_personas
            + self.linux_server_personas
            + self.registry_personas
        )

    @cached_property
    def managed_personas(self) -> List[str]:
        """
        List of RACE nodes managed by RiB. Bridge nodes will not be managed by
        RiB
        """

        return list(set(self.personas) - set(self.bridge_personas))

    @cached_property
    def personas(self) -> List[str]:
        """List of all node personas"""
        return self.client_personas + self.server_personas + self.registry_personas

    @cached_property
    def genesis_personas(self) -> List[str]:
        """List of all genesis node personas"""
        # TODO: currently servers are _only_ linux, but if this ever changes then this
        #       property will need to be updated.
        return (
            self.genesis_client_personas
            + self.linux_genesis_server_personas
            + self.genesis_registry_personas
        )

    @cached_property
    def arm64_v8a_client_personas(self) -> List[str]:
        """List of all ARM64 client node personas"""
        return self.cached_node_lists["arm64-v8a_client_personas"]

    @cached_property
    def arm64_v8a_server_personas(self) -> List[str]:
        """List of all ARM64 server node personas"""
        return self.cached_node_lists["arm64-v8a_server_personas"]

    @cached_property
    def x86_64_client_personas(self) -> List[str]:
        """List of all x86_64 client node personas"""
        return self.cached_node_lists["x86_64_client_personas"]

    @cached_property
    def x86_64_server_personas(self) -> List[str]:
        """List of all x86_64 server node personas"""
        return self.cached_node_lists["x86_64_server_personas"]

    # This is *NOT* a cached property because it is potentially mutable
    @property
    def all_personas(self) -> List[str]:
        """List of all known and auto-detected personas"""
        return set(self.personas + self.race_node_interface.get_all_node_personas())

    @cached_property
    def _external_services(self) -> List[Dict[str, str]]:
        """Map of plugin/channel ID to local path to external service script directories"""
        external_services = {}

        for channel in self.config.comms_channels:
            channel_name = channel.name
            channel_dir = os.path.join(
                self.paths.dirs["plugins"],
                channel.kit_name,
                "channels",
                channel_name,
            )
            if plugin_utils.channel_plugin_has_external_services(
                channel_name, channel_dir
            ):
                external_services[channel_name] = channel_dir

        for kit in self.config.artifact_manager_kits:
            kit_name = kit.name
            kit_dir = os.path.join(
                self.paths.dirs["plugins"], kit_name, "runtime-scripts"
            )
            if plugin_utils.channel_plugin_has_external_services(kit_name, kit_dir):
                external_services[kit_name] = kit_dir

        return external_services

    ###
    # Deployment Class Management Methods
    ###

    @staticmethod
    def get_deployment_class(rib_mode: str) -> "RibDeployment":
        """
        Purpose:
            Get the correct RibDeployment class for the rib mode
        Args:
            rib_mode (String): Mode for RACE system (local and aws)
        Return:
            rib_deployment_class (RiB Deployment Class): The matching
                RibDeployment class
        """

        rib_deployment_class = None
        for deployment_subclass in general_utils.get_all_subclasses(RibDeployment):
            if rib_mode == deployment_subclass.rib_mode:
                rib_deployment_class = deployment_subclass
                break

        return rib_deployment_class

    ###
    # Create Deployment Methods
    ###

    @abstractmethod
    def create(self, **kwargs: Dict[str, Any]) -> None:
        """
        Purpose:
            Create a deployment (Not Implemented in Base Class)

            Note: Init will initialize a deployment object. This can
            be loaded from a file or from command line args (or other means
            if testing). But a NEW deployment needs to be "created", in that
            its files, structure, etc need to be created and persisted
            on disk. This is the method to do so
        Expected Args:
            **kwargs (Dict): Dynamic keyword args depending on deployment type
        Expected Return:
            N/A
        """

        pass

    def _write_race_json_files(self, race_json: Dict[str, Any]) -> None:
        """
        Purpose:
            Write the race_json object to the platform-specific directories
        Args:
            race_json: The race_json object
        Returns:
            N/A
        """

        # Same race json for linux and android currently
        general_utils.write_data_to_file(
            data=race_json,
            data_format="json",
            filename=f"{self.paths.dirs['global_android_configs']}/race.json",
        )
        general_utils.write_data_to_file(
            data=race_json,
            data_format="json",
            filename=f"{self.paths.dirs['global_linux_configs']}/race.json",
        )

    def create_global_etc_files(self, disable_open_tracing: bool = False) -> None:
        """
        Purpose:
            Create etc files (jaeger-config, etc.) per node
        Args:
            N/A
        Returns:
            N/A
        """

        range_config = general_utils.load_file_into_memory(
            self.paths.files["race_config"], data_format="json"
        )

        config_template_dir = f"{self.paths.dirs['templates']}/configs"
        for node in range_config["range"]["RACE_nodes"]:
            persona = node["name"]
            platform = node["platform"]
            node_type = node["type"]
            ui_enabled = node.get("uiEnabled", False)

            testapp_json_to_write = {
                "name": persona,
                "type": node_type,
                "period": RibDeployment.PERIOD_DEFAULT,
                "ttl-factor": RibDeployment.TIME_TO_LIVE_DEFAULT,
                "headless": not ui_enabled,
            }

            # write the testing config json data to the file
            general_utils.write_data_to_file(
                data=testapp_json_to_write,
                data_format="json",
                filename=f"{self.paths.dirs['etc']}/{persona}/{self.paths.global_etc_filenames['testapp_config']}",
            )

            # write platform specific jaeger config templates into the node's etc direcotry
            if platform == "linux":
                source_jaeger_config = f"{config_template_dir}/jaeger-config-linux.yml"
            elif platform == "android":
                source_jaeger_config = (
                    f"{config_template_dir}/jaeger-config-android.yml"
                )
            else:
                # TODO use real error
                raise error_utils.RIB000()
            jaeger_config = general_utils.load_file_into_memory(
                filename=source_jaeger_config, data_format="yaml"
            )
            if disable_open_tracing:
                jaeger_config["disabled"] = True
            general_utils.write_data_to_file(
                data=jaeger_config,
                data_format="yaml",
                filename=f"{self.paths.dirs['etc']}/{persona}/jaeger-config.yml",
            )

    def create_global_configs_and_data(
        self,
        fetch_plugins_on_start: bool = False,
        log_level: Optional[str] = None,
    ) -> None:
        """
        Purpose:
            Create Global Configs and Data for a local deployment, and write
            the objects to the deployment dir
        Args:
            fetch_plugins_on_start: Enable fetching of plugins from artifact managers on application start
            initial_enabled_channels: List of initially enabled channels
            log_level: RACE application log level
        Returns:
            N/A
        """

        # Write Opentracing Config
        config_template_dir = f"{self.paths.dirs['templates']}/configs"

        initial_enabled_channels = [
            channel.name for channel in self.config.comms_channels if channel.enabled
        ]

        # generate the race_json config
        race_json = self.create_race_json(
            config_template_dir=config_template_dir,
            fetch_plugins_on_start=fetch_plugins_on_start,
            initial_enabled_channels=initial_enabled_channels,
            log_level=log_level,
        )

        self._write_race_json_files(race_json)

    def update_race_json(self) -> Dict[str, Any]:
        """
        Purpose:

        Args:
            N/A
        Returns:
            A dict corresponding to the refreshed race_json structure
        """
        config_template_dir = f"{self.paths.dirs['templates']}/configs"

        # Read the current isPluginFetchOnStartEnabled setting value
        race_json = general_utils.load_file_into_memory(
            filename=f"{self.paths.dirs['global_linux_configs']}/race.json",
            data_format="json",
        )

        fetch_plugins_on_start = (
            race_json["isPluginFetchOnStartEnabled"]
            if ("isPluginFetchOnStartEnabled" in race_json)
            else "false"
        )

        initial_enabled_channels = race_json.get("initial_enabled_channels")
        log_level = race_json.get("level")

        # re-generate the race_json config
        race_json = self.create_race_json(
            config_template_dir=config_template_dir,
            fetch_plugins_on_start=fetch_plugins_on_start,
            initial_enabled_channels=initial_enabled_channels,
            log_level=log_level,
        )

        self._write_race_json_files(race_json)

        # Return the new config that was written
        return race_json

    def update_daemon_config(
        self,
        nodes: Optional[List[str]] = None,
        period: Optional[int] = None,
        ttl_factor: Optional[int] = None,
        reset: bool = False,
        force: bool = False,
    ) -> None:
        """
        Purpose:
            Update the Daemon config
        Args:
            nodes: List of nodes to configure the Daemon for
            period: Statusing period to set
            ttl_factor: Mulitplier of period to get the time to live
            reset: reset Daemon config to defaults
            force: Whether or not to force the operation
        Returns:
            N/A
        """
        if nodes:
            require = Require.ALL
        else:
            require = Require.ANY
            # If no nodes specified, update testing config for all RACE nodes
            nodes = self.personas

        # Get the nodes that can be configured
        nodes_to_update_daemon_config_for = self.status.get_nodes_that_match_status(
            action="daemon configure",
            personas=nodes,
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            require=require,
            force=force,
        )

        # reset the testapp-config to default values
        if reset:
            period = RibDeployment.PERIOD_DEFAULT
            ttl_factor = RibDeployment.TIME_TO_LIVE_DEFAULT

        for node in nodes_to_update_daemon_config_for:
            self.race_node_interface.set_daemon_config(
                persona=node, period=period, ttl_factor=ttl_factor
            )
            logger.debug(f"Updated daemon config for {node}")

    def update_testapp_config(
        self,
        nodes: Optional[List[str]] = None,
        period: Optional[int] = None,
        ttl_factor: Optional[int] = None,
        reset: bool = False,
        force: bool = False,
    ) -> None:
        """
        Purpose:
            Update the testapp-config.json
        Args:
            nodes: List of nodes to configure the testapp for
            period: Statusing period to set
            ttl_factor: Mulitplier of period to get the time to live
            reset: reset testapp config to defaults
            force: Whether or not to force the operation
        Returns:
            N/A
        """

        if nodes:
            require = Require.ALL
        else:
            require = Require.ANY
            # If no nodes specified, update testing config for all RACE nodes
            nodes = self.personas

        # Get the nodes that can be configured
        nodes_to_update_testing_config_for = self.status.get_nodes_that_match_status(
            action="testapp configure",
            personas=nodes,
            etc_status=[status_utils.EtcStatus.CONFIG_GEN_SUCCESS],
            require=require,
            force=force,
        )

        # reset the testapp-config to default values
        if reset:
            period = RibDeployment.PERIOD_DEFAULT
            ttl_factor = RibDeployment.TIME_TO_LIVE_DEFAULT

        for node in nodes_to_update_testing_config_for:
            testapp_config_json = general_utils.load_file_into_memory(
                filename=f"{self.paths.dirs['etc']}/{node}/{self.paths.global_etc_filenames['testapp_config']}",
                data_format="json",
            )

            # use saved period unless user specifies a change
            if period:
                testapp_config_json["period"] = period
            # use saved ttl unless user specifies a change
            if ttl_factor:
                testapp_config_json["ttl-factor"] = ttl_factor

            # write the testing config json data to the file
            general_utils.write_data_to_file(
                data=testapp_config_json,
                data_format="json",
                filename=f"{self.paths.dirs['etc']}/{node}/{self.paths.global_etc_filenames['testapp_config']}",
            )
            logger.debug(f"Updated testapp-config for {node}")

    def get_deployment_channels_list(self) -> List[Mapping[str, Any]]:
        """
        Purpose:
            Compile channel properties for deployment
        Args:
            N/A
        Returns:
            list of all channel properties
        """

        full_channel_list = []
        for channel in self.config.comms_channels:
            channel_props_file = (
                f'{self.paths.dirs["plugins"]}/{channel.kit_name}/channels/'
                f"{channel.name}/channel_properties.json"
            )
            channel_props = general_utils.load_file_into_memory(
                channel_props_file, data_format="json"
            )
            channel_props["enabled"] = channel.enabled
            full_channel_list.append(channel_props)

        return full_channel_list

    def get_plugin_manifests(
        self, kit_name: str, kit_type: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Purpose:
            Get or create list of plugin manifests from the named kit; one per platform.
            This splits out manifests that are meant for multiple platforms.
        Args:
            kit_name: Name of the kit
            kit_type: Type of the kit (network-manager, comms, core, artifact-manager)
        Return:
            Tuple of plugin manifests list and composition manifests list
        """

        plugins = []
        compositions = []
        platforms = [
            {
                "platform_filepath": "android-arm64-v8a-client",
                "node_type": "client",
                "os": "android",
                "architecture": "arm64-v8a",
            },
            {
                "platform_filepath": "android-x86_64-client",
                "node_type": "client",
                "os": "android",
                "architecture": "x86_64",
            },
            {
                "platform_filepath": "linux-x86_64-client",
                "node_type": "client",
                "os": "linux",
                "architecture": "x86_64",
            },
            {
                "platform_filepath": "linux-x86_64-server",
                "node_type": "server",
                "os": "linux",
                "architecture": "x86_64",
            },
            {
                "platform_filepath": "linux-arm64-v8a-client",
                "node_type": "client",
                "os": "linux",
                "architecture": "arm64-v8a",
            },
            {
                "platform_filepath": "linux-arm64-v8a-server",
                "node_type": "server",
                "os": "linux",
                "architecture": "arm64-v8a",
            },
        ]
        for platform in platforms:
            node_type = platform.get("node_type")
            platform_os = platform.get("os")
            architecture = platform.get("architecture")
            platform_artifacts_path = f"{self.paths.dirs[self.paths.get_plugin_artifacts_ta_dir_key(platform_os, architecture, node_type, kit_type)]}/{kit_name}"
            if os.path.isdir(platform_artifacts_path):
                # Get fields from Manifest if it exists
                manifest_file_path = platform_artifacts_path + "/manifest.json"
                if os.path.isfile(manifest_file_path):
                    manifest_file = general_utils.load_file_into_memory(
                        filename=manifest_file_path, data_format="json"
                    )
                    # This is a bit redundant because the manifest.json is placed in all supported platforms with all plugins defined, including for the other platforms.
                    for plugin in manifest_file.get("plugins"):
                        if (
                            plugin["node_type"].lower() == "any"
                            or plugin["node_type"].lower() == node_type
                        ):
                            plugin_manifest = plugin
                            plugin_manifest["node_type"] = node_type
                            plugin_manifest["platform"] = platform_os
                            plugin_manifest["architecture"] = architecture
                            plugins.append(copy.deepcopy(plugin_manifest))

                    for composition in manifest_file.get("compositions", []):
                        # architecture check?
                        composition = copy.deepcopy(composition)
                        composition["node_type"] = node_type
                        composition["platform"] = platform_os
                        composition["architecture"] = architecture
                        compositions.append(composition)

                else:
                    logger.error(
                        f"No manifest file found for {platform_artifacts_path}"
                    )
                    continue

        return plugins, compositions

    def create_race_json(
        self,
        config_template_dir: str,
        fetch_plugins_on_start: bool = False,
        initial_enabled_channels: Optional[List[str]] = None,
        log_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Create race.json based on deployment plugins/channels
        Expected Args:
            config_template_dir: directory where template race.json is
            fetch_plugins_on_start: Enable fetching of plugins from artifact managers on application start
            initial_enabled_channels: List of initially enabled channels
            log_level: RACE application log level
        Expected Return:
            data to be written to race.json
        """

        race_json = general_utils.load_file_into_memory(
            filename=f"{config_template_dir}/race.json", data_format="json"
        )

        race_json["isPluginFetchOnStartEnabled"] = f"{fetch_plugins_on_start}".lower()

        plugins_section = []
        compositions_section = []

        plugins, compositions = self.get_plugin_manifests(
            self.config.network_manager_kit.name, "network-manager"
        )
        plugins_section.extend(plugins)
        compositions_section.extend(compositions)

        for comms_kit in self.config.comms_kits:
            plugins, compositions = self.get_plugin_manifests(comms_kit.name, "comms")
            plugins_section.extend(plugins)
            compositions_section.extend(compositions)

        for artifact_manager_kit in self.config.artifact_manager_kits:
            plugins, compositions = self.get_plugin_manifests(
                artifact_manager_kit.name, "artifact-manager"
            )
            plugins_section.extend(plugins)
            compositions_section.extend(compositions)

        deployment_artifacts.validate_compositions(
            plugins_section, compositions_section
        )

        race_json["plugins"] = plugins_section
        race_json["compositions"] = compositions_section

        race_json["channels"] = self.get_deployment_channels_list()

        if initial_enabled_channels:
            race_json["initial_enabled_channels"] = initial_enabled_channels

        if log_level:
            race_json["level"] = log_level.upper()

        return race_json

    @abstractmethod
    def generate_plugin_or_channel_configs(
        self,
        verbose: int = 0,
        force: bool = False,
        network_manager_custom_args: str = "",
        comms_custom_args_map: Dict[str, Any] = None,
        artifact_manager_custom_args_map: Dict[str, Any] = None,
        timeout: int = 300,
        max_iterations: int = 5,
        skip_config_tar: bool = False,
    ) -> None:
        """
        Purpose:
            Handle interaction between network manager and comms config generation. Abstract method required to allow deployment modes to set local flag
        Args:
            verbose (int): level of verbosity for output
            force (bool): whether or not to remove existing configs
            network_manager_custom_args (str): custom arguments to pass to network manager config generator
            comms_custom_args_map (dict): map of channel_ids to dict of custom args and values to pass to channel config generators
            artifact_manager_custom_args_map: map of plugin_ids to dict of custom args and values to pass to artifact manager config generators
            timeout (int): timeout for an individual iteration of a config generation script to run
            max_iterations(int): max number of iterations to run config generation through
            skip_config_tar(bool): skip taring configs
        Returns:
            N/A
        """

    def _generate_plugin_or_channel_configs(
        self,
        force: bool = False,
        local: bool = False,
        network_manager_custom_args: str = "",
        comms_custom_args_map: Dict[str, Any] = None,
        artifact_manager_custom_args_map: Dict[str, Any] = None,
        timeout: int = 300,
        max_iterations: int = 5,
        skip_config_tar: bool = False,
    ) -> None:
        """
        Purpose:
            Handle interaction between network manager and comms config generation.
        Args:
            force (bool): whether or not to remove existing configs
            local (bool): whether or not to include --local flag (which indicates
                RiB local mode to the generators) to all config generators
            network_manager_custom_args (str): custom arguments to pass to network manager config generator
            comms_custom_args_map (dict): map of channel_ids to dict of custom args and values to pass to channel config generators
            artifact_manager_custom_args_map: map of plugin_ids to dict of custom args and values to pass to artifact manager config generators
            timeout (int): timeout for an individual iteration of a config generation script to run
            max_iterations(int): max number of iterations to run config generation through
            skip_config_tar(bool): skip taring configs
        Returns:
            N/A
        """

        # Set Default val if None
        comms_custom_args_map = (
            {} if comms_custom_args_map is None else comms_custom_args_map
        )
        artifact_manager_custom_args_map = (
            {}
            if artifact_manager_custom_args_map is None
            else artifact_manager_custom_args_map
        )

        if force:
            # Delete existing configs if force
            general_utils.remove_dir_file(
                f'{self.paths.dirs["network_manager_configs_base"]}/'
            )
            general_utils.remove_dir_file(f'{self.paths.dirs["comms_configs_base"]}/')
            general_utils.remove_dir_file(
                f'{self.paths.dirs["artifact_manager_configs_base"]}/'
            )
            # Recreate dirs. This is easier than looping through files/dirs to remove
            os.mkdir(self.paths.dirs["network_manager_configs_base"])
            os.mkdir(self.paths.dirs["comms_configs_base"])
            os.mkdir(self.paths.dirs["artifact_manager_configs_base"])

        try:
            full_channel_list = self.get_deployment_channels_list()
            general_utils.write_data_to_file(
                self.paths.files["channel_list"], full_channel_list, data_format="json"
            )

            network_manager_config_gen_status = {}
            fulfilled_requests_flag = ""

            user_responses_by_plugin_id = {}

            composition_ids = set()
            for channel in self.config.comms_channels:
                _, compositions = self.get_plugin_manifests(channel.kit_name, "comms")
                for composition in compositions:
                    composition_ids.add(composition.get("id", ""))

            iteration_count = 0
            while iteration_count < max_iterations and (
                not network_manager_config_gen_status
                or network_manager_config_gen_status.get("status") != "complete"
            ):
                iteration_count += 1
                # Run Network Manager Config Gen
                self.run_network_manager_config_gen(
                    local=local,
                    fulfilled_requests_flag=fulfilled_requests_flag,
                    network_manager_custom_args=network_manager_custom_args,
                    timeout=timeout,
                )

                # Check Network Manager Status
                network_manager_config_gen_status = general_utils.load_file_into_memory(
                    f'{self.paths.dirs["network_manager_configs_base"]}/{self.config.network_manager_kit.name}/network-manager-config-gen-status.json',
                    data_format="json",
                )
                if network_manager_config_gen_status.get("status") == "complete":
                    break

                network_manager_request = general_utils.load_file_into_memory(
                    f'{self.paths.dirs["network_manager_configs_base"]}/{self.config.network_manager_kit.name}/network-manager-request.json',
                    data_format="json",
                ).get("links")

                network_manager_user_responses_file = f'{self.paths.dirs["network_manager_configs_base"]}/{self.config.network_manager_kit.name}/user-responses.json'
                if os.path.exists(network_manager_user_responses_file):
                    user_responses_by_plugin_id[
                        self.config.network_manager_kit.name
                    ] = general_utils.load_file_into_memory(
                        network_manager_user_responses_file, data_format="json"
                    )

                # Run Comms Config Gen for all channels
                fulfilled_requests = []
                genenesis_link_addresses = {}
                for channel in self.config.comms_channels:
                    self.run_comms_config_gen(
                        local=local,
                        comms_custom_args_map=comms_custom_args_map,
                        channel=channel,
                        timeout=timeout,
                    )

                    # Get genesis link addresses for channel
                    channel_config_dir = f'{self.paths.dirs["comms_configs_base"]}/{channel.kit_name}/{channel.name}'
                    try:
                        current_genenesis_link_addresses = (
                            general_utils.load_file_into_memory(
                                f"{channel_config_dir}/genesis-link-addresses.json",
                                data_format="json",
                            )
                        )
                        if current_genenesis_link_addresses:
                            print(
                                f"Got genesis-link-addresses for channel {channel_config_dir}"
                            )
                            genenesis_link_addresses.update(
                                current_genenesis_link_addresses
                            )
                    except:
                        print(
                            f"no genesis-link-addresses for channel {channel_config_dir}"
                        )

                    # Get fulfilled requests for channel
                    current_fulfilled_requests = general_utils.load_file_into_memory(
                        f"{channel_config_dir}/fulfilled-network-manager-request.json",
                        data_format="json",
                    ).get("links")
                    if current_fulfilled_requests:
                        # To be safe, ensure that the comms only included their channel
                        for link in current_fulfilled_requests:
                            link["channels"] = [channel.name]

                        fulfilled_requests.append(current_fulfilled_requests)

                    channel_user_responses_file = (
                        f"{channel_config_dir}/user-responses.json"
                    )
                    if os.path.exists(channel_user_responses_file):
                        plugin_id = channel.kit_name
                        channel_id = channel.name
                        if channel_id in composition_ids:
                            # Use composition ID if a decomposed channel
                            plugin_id = channel_id
                        user_responses_by_plugin_id.setdefault(plugin_id, {})
                        channel_user_responses = general_utils.load_file_into_memory(
                            channel_user_responses_file, data_format="json"
                        )
                        for node in channel_user_responses.keys():
                            user_responses_by_plugin_id[plugin_id].setdefault(node, {})
                            user_responses_by_plugin_id[plugin_id][node].update(
                                channel_user_responses[node]
                            )

                # Merge fulfilled request from all channels
                merged_fulfilled_requests = RibDeployment.merge_fulfilled_requests(
                    network_manager_request, fulfilled_requests
                )
                merged_fulfilled_requests_map = {"links": merged_fulfilled_requests}
                general_utils.write_data_to_file(
                    f'{self.paths.dirs["comms_configs_base"]}/merged-fulfilled-requests.json',
                    merged_fulfilled_requests_map,
                    "json",
                )
                fulfilled_requests_flag = f'--fulfilled-requests={self.paths.dirs["comms_configs_base"]}/merged-fulfilled-requests.json'

            for persona in self.all_personas:
                links_profiles_for_persona = {}
                for (
                    channel_id,
                    persona_link_profiles,
                ) in genenesis_link_addresses.items():
                    links_profiles_for_persona[channel_id] = persona_link_profiles.get(
                        persona, []
                    )

                # Node specific dirs should have been created in network manager config Gen but try to
                # create just in case (If the only config network manager needs is the link-profiles, they
                # will not have this dir created yet)
                network_manager_config_dir = f'{self.paths.dirs["network_manager_configs_base"]}/{self.config.network_manager_kit.name}/{persona}'
                os.makedirs(
                    network_manager_config_dir,
                    exist_ok=True,
                )
                general_utils.write_data_to_file(
                    f"{network_manager_config_dir}/link-profiles.json",
                    links_profiles_for_persona,
                    "json",
                )

            # Run config gen for all artifact manager channels
            for kit in self.config.artifact_manager_kits:
                self.run_artifact_manager_config_gen(
                    kit=kit,
                    local=local,
                    custom_args_map=artifact_manager_custom_args_map,
                    timeout=timeout,
                )

                plugin_user_responses_file = f'{self.paths.dirs["artifact_manager_configs_base"]}/{kit.name}/user-responses.json'
                if os.path.exists(plugin_user_responses_file):
                    user_responses_by_plugin_id[
                        kit.name
                    ] = general_utils.load_file_into_memory(
                        plugin_user_responses_file, data_format="json"
                    )

            # Create node-specific user response files from plugin responses
            self.create_user_responses(user_responses_by_plugin_id)
        except Exception as err:
            message = str(err)
            if len(message) > 1000:
                message = message[:1000] + "..."
            raise error_utils.RIB333(
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                message=message,
            ) from None

        if network_manager_config_gen_status:
            exit_reason = network_manager_config_gen_status.get("reason")
            if len(exit_reason) > 500:
                exit_reason = exit_reason[:500] + "..."
        else:
            exit_reason = "Network manager failed to produce network-manager-config-gen-status.json"
        logger.info(
            f'Network manager config gen status: {network_manager_config_gen_status.get("status")}, reason: {exit_reason}'
        )
        if not skip_config_tar:
            self.tar_configs(force=force)

    def run_network_manager_config_gen(
        self,
        local: bool = False,
        fulfilled_requests_flag: str = "",
        network_manager_custom_args: str = "",
        timeout: int = 300,
    ):
        """
        Purpose:
            Call network manager config generation passing arguments based on deployment configuration
        Args:
            local (bool): whether or not to include --local flag (which indicates RiB local mode to the generators) to all config generators
            fulfilled_requests_flag (str): flag for passing the merged fulfilled request file
            network_manager_custom_args (str): custom arguments to pass to network manager config generator
            timeout (int): timeout for an individual iteration of a config generation script to run
        Returns:
            N/A
        """

        network_manager_generate_configs_script = f'{self.paths.dirs["plugins"]}/{self.config.network_manager_kit.name}/config-generator/generate_configs.sh'
        cmd = [
            "bash",
            network_manager_generate_configs_script,
            f'--range={self.paths.files["race_config"]}',
            f'--config-dir={self.paths.dirs["network_manager_configs_base"]}/{self.config.network_manager_kit.name}',
            "--overwrite",
            f'--channel-list={self.paths.files["channel_list"]}',
        ]
        if fulfilled_requests_flag:
            cmd.append(fulfilled_requests_flag)
        if network_manager_custom_args:
            cmd.append(network_manager_custom_args)
        if local:
            cmd.append("--local")
        cmd_as_str = " ".join(cmd)
        logger.debug(f"Network Manager Config Generation Command: {cmd_as_str}")
        subprocess_utils.run(
            cmd_as_str,
            check=True,
            shell=True,
            stdout_level=logging.DEBUG,
            timeout=timeout,
        )

        # NOTE: network manager config gen will delete it's config gen directory prior to generating configs.
        # Because of this, network manager must be responsible for creating node specific config dirs.

    def run_comms_config_gen(
        self,
        channel: ChannelConfig,
        local: bool = False,
        comms_custom_args_map: Dict[str, Any] = None,
        timeout: int = 300,
    ) -> None:
        """
        Purpose:
            Call comms config generation passing arguments based on deployment configuration
        Args:
            local: whether or not to include --local flag (which indicates RiB
                local mode to the generator)
            comms_custom_args_map: map of channel_ids to dict of custom args and
                values to pass to channel config generators
            channel: Comms channel config
            timeout: timeout for an individual iteration of a config generation
                script to run
        Returns:
            N/A
        """

        # Set Default values if None
        comms_custom_args_map = (
            {} if comms_custom_args_map is None else comms_custom_args_map
        )

        comms_generate_configs_script = f'{self.paths.dirs["plugins"]}/{channel.kit_name}/channels/{channel.name}/generate_configs.sh'
        cmd = [
            "bash",
            comms_generate_configs_script,
            f'--range={self.paths.files["race_config"]}',
            f'--config-dir={self.paths.dirs["comms_configs_base"]}/{channel.kit_name}/{channel.name}',
            "--overwrite",
            f'--network-manager-request={self.paths.dirs["network_manager_configs_base"]}/{self.config.network_manager_kit.name}/network-manager-request.json',
        ]
        if local:
            cmd.append("--local")
        if comms_custom_args_map:
            flags_for_channel = comms_custom_args_map.get(channel.name)
            if flags_for_channel:
                cmd.append(flags_for_channel)
        cmd_as_str = " ".join(cmd)
        logger.debug(f"Comms ({channel.name}) Config Generation Command: {cmd_as_str}")
        subprocess_utils.run(
            cmd_as_str,
            check=True,
            shell=True,
            stdout_level=logging.DEBUG,
            timeout=timeout,
        )

    def run_artifact_manager_config_gen(
        self,
        kit: plugin_utils.KitConfig,
        local: bool = False,
        custom_args_map: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
    ) -> None:
        """
        Purpose:
            Call artifact manager config generation passing arguments based on deployment configuration
        Args:
            kit: Artifact manager kit config
            local: whether or not to include --local flag (which indicates RiB local mode to the generator)
            custom_args_map: map of plugin_ids to dict of custom args and values to pass to config generators
            timeout: timeout for an individual iteration of a config generation script to run
        Returns:
            N/A
        """

        # Set Default values if None
        custom_args_map = {} if custom_args_map is None else custom_args_map

        generate_configs_script = f'{self.paths.dirs["plugins"]}/{kit.name}/config-generator/generate_configs.sh'
        cmd = [
            "bash",
            generate_configs_script,
            f'--range={self.paths.files["race_config"]}',
            f'--config-dir={self.paths.dirs["artifact_manager_configs_base"]}/{kit.name}',
            "--overwrite",
        ]
        if local:
            cmd.append("--local")
        if custom_args_map:
            flags_for_plugin = custom_args_map.get(kit.name)
            if flags_for_plugin:
                cmd.append(flags_for_plugin)
        cmd_as_str = " ".join(cmd)
        logger.debug(
            f"ArtifactManager ({kit.name}) Config Generation Command: {cmd_as_str}"
        )
        subprocess_utils.run(
            cmd_as_str,
            check=True,
            shell=True,
            stdout_level=logging.DEBUG,
            timeout=timeout,
        )

    def get_nodes_from_regex(self, raw_node_inputs: List[str]) -> List[str]:
        """
        Purpose:
            Call artifact manager config generation passing arguments based on deployment configuration
        Args:
            plugin: artifact manager plugin information
        Returns:
            N/A
        """

        nodes_set = set()
        for persona in self.personas:
            for raw_node in raw_node_inputs:
                match = re.search(raw_node, persona)
                if match:
                    nodes_set.add(persona)
        if not nodes_set:
            raise (error_utils.RIB351(raw_node_inputs))
        return list(nodes_set)

    ###
    # Artifact distribution related methods
    ###

    def copy_plugin_to_distribution_dir(
        self, plugin_name: str, plugin_type: str
    ) -> None:
        """
        Purpose:
            Copy plugin artifacts to distribution directory as zip files
        Args:
            plugin_name: Name of plugin
            plugin_type: Type of plugin (network-manager, comms, core, artifact-manager)
        Return:
            N/A
        """

        for (
            platform,
            architecture,
            node_type,
        ) in self.paths.supported_platform_arch_node_type_combinations:
            # Registry nodes use client artifacts
            if node_type == "registry":
                continue
            # Don't copy artifacts for node types that aren't part of this deployment
            if not self.cached_node_lists.get(f"{platform}_{node_type}_personas"):
                continue
            if not self.cached_node_lists.get(
                f"{platform}_bridge_{node_type}_personas"
            ) and not self.cached_node_lists.get(
                f"{architecture}_{node_type}_personas"
            ):
                continue
            platform_artifacts_path = f"{self.paths.dirs[self.paths.get_plugin_artifacts_ta_dir_key(platform, architecture, node_type, plugin_type)]}/{plugin_name}"
            if os.path.isdir(platform_artifacts_path):
                # Copy plugins to distribution dir and prepend platform
                output_file = f'{self.paths.dirs["distribution_artifacts"]}/{platform}-{architecture}-{node_type}-{plugin_name}.zip'
                general_utils.zip_directory(
                    dir_path=platform_artifacts_path,
                    output_file=output_file,
                )
                logger.trace(f"copied {platform_artifacts_path} into {output_file}")

    def create_distribution_artifacts(self) -> None:
        """
        Purpose:
            Create zip archives for plugins and apps to be distributed/used by artifact manager plugins
        Args:
            N/A
        Return:
            N/A
        """

        logger.debug(f"Clearing artifact distribution directory...")

        dir_contents = general_utils.get_contents_of_dir(
            self.paths.dirs["distribution_artifacts"]
        )
        for item in dir_contents:
            general_utils.remove_dir_file(item)
            logger.trace(f"Removed distribution artifact: {item}")

        logger.debug(f"Copying artifacts into distribution directory...")

        self.copy_plugin_to_distribution_dir(
            self.config.network_manager_kit.name, "network-manager"
        )

        for kit in self.config.comms_kits:
            self.copy_plugin_to_distribution_dir(kit.name, "comms")

        # Only copy in the apps if the deployment contains non-genesis nodes
        if self.bootstrap_client_personas:
            self.copy_plugin_to_distribution_dir("race", "core")

        for kit in self.config.artifact_manager_kits:
            self.copy_plugin_to_distribution_dir(kit.name, "artifact-manager")

    def get_plugins(
        self,
        cache: CacheStrategy = CacheStrategy.AUTO,
        race_core_cache: Optional[plugin_utils.KitCacheMetadata] = None,
        android_app_cache: Optional[plugin_utils.KitCacheMetadata] = None,
        linux_app_cache: Optional[plugin_utils.KitCacheMetadata] = None,
        registry_app_cache: Optional[plugin_utils.KitCacheMetadata] = None,
        node_daemon_cache: Optional[plugin_utils.KitCacheMetadata] = None,
        network_manager_kit_cache: Optional[plugin_utils.KitCacheMetadata] = None,
        comms_kits_cache: Optional[Dict[str, plugin_utils.KitCacheMetadata]] = None,
        artifact_manager_kits_cache: Optional[
            Dict[str, plugin_utils.KitCacheMetadata]
        ] = None,
    ) -> None:
        """
        Purpose:
            Get plugins for deployment
        Args:
            cache: Plugin cache strategy
        Return:
            N/A
        """

        # Remove existing plugins if they exist
        if os.path.isdir(self.paths.dirs["plugins"]):
            general_utils.remove_dir_file(self.paths.dirs["plugins"])

        # Remake Plugin Dirs
        self.create_plugin_directories()

        # Download (if necessary)
        if not race_core_cache:
            race_core_cache = plugin_utils.download_race_core(
                self.config.race_core, cache
            )
        if not android_app_cache and self.android_client_personas:
            android_app_cache = plugin_utils.download_kit(
                "Android app",
                self.config.android_app.source,
                race_core_cache,
                cache,
            )
        if not linux_app_cache:
            linux_app_cache = plugin_utils.download_kit(
                "Linux app",
                self.config.linux_app.source,
                race_core_cache,
                cache,
            )
        if not registry_app_cache and self.config.registry_app:
            registry_app_cache = plugin_utils.download_kit(
                "Registry app",
                self.config.registry_app.source,
                race_core_cache,
                cache,
            )
        if not node_daemon_cache:
            node_daemon_cache = plugin_utils.download_kit(
                "Node daemon",
                self.config.node_daemon.source,
                race_core_cache,
                cache,
            )
        if not network_manager_kit_cache:
            network_manager_kit_cache = plugin_utils.download_kit(
                "Network manager",
                self.config.network_manager_kit.source,
                race_core_cache,
                cache,
            )
        if not comms_kits_cache:
            comms_kits_cache = {
                kit.name: plugin_utils.download_kit(
                    kit.name, kit.source, race_core_cache, cache
                )
                for kit in self.config.comms_kits
            }
        if not artifact_manager_kits_cache:
            artifact_manager_kits_cache = {
                kit.name: plugin_utils.download_kit(
                    kit.name, kit.source, race_core_cache, cache
                )
                for kit in self.config.artifact_manager_kits
            }

        # Copy network manager kit
        self.copy_kit(
            self.config.network_manager_kit.name,
            "network-manager",
            network_manager_kit_cache,
        )

        # Copy Comms Kits
        for kit_name, kit_cache in comms_kits_cache.items():
            self.copy_kit(kit_name, "comms", kit_cache)

        # Copy Artifact Manager Kits
        for kit_name, kit_cache in artifact_manager_kits_cache.items():
            self.copy_kit(kit_name, "artifact-manager", kit_cache)

        # Copy App Kits
        if android_app_cache and self.android_client_personas:
            self.copy_kit(self.config.android_app.name, "core", android_app_cache)
        self.copy_kit(self.config.linux_app.name, "core", linux_app_cache)
        self.copy_kit(self.config.node_daemon.name, "core", node_daemon_cache)
        if registry_app_cache and self.config.registry_app:
            self.copy_kit(self.config.registry_app.name, "core", registry_app_cache)

    @abstractmethod
    def copy_kit(
        self,
        kit_name: str,
        kit_type: str,
        kit_cache: plugin_utils.KitCacheMetadata,
    ) -> None:
        """
        Purpose:
            Copy the specified kit into the deployment
        Args:
            kit_name: Name of kit
            kit_type: Type of kit (network-manager, comms, core, artifact-manager)
            kit_cache: kit download cache metadata
        Return:
            N/A
        """

    @abstractmethod
    def upload_artifacts(self, timeout: int) -> None:
        """
        Purpose:
            Upload distributable artifacts
        Expected Args:
            timeout: Time in seconds to timeout if the command fails
        Expected Return:
            N/A
        """

    def copy_plugin_support_files_into_deployment(
        self, plugin_name: str, plugin_src: str
    ) -> None:
        """
        Purpose:
            Copies the specified plugin from the plugin cache or local path into the specified
            destination.
        Args:
            plugin_name: Name of plugin
            plugin_src: Location of plugin
        Return:
            N/A
        """

        dest_dir = f"{self.paths.dirs['plugins']}/{plugin_name}/"
        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        for file in os.listdir(plugin_src):
            if file != "artifacts":
                source = f"{plugin_src}/{file}"
                dest = f"{dest_dir}/{file}"
                if os.path.isdir(source):
                    shutil.copytree(
                        src=source,
                        dst=dest,
                        dirs_exist_ok=True,
                    )
                else:
                    shutil.copy(
                        source,
                        dest,
                    )
                logger.trace(f"copied {source} to {dest}")

    def copy_plugin_artifacts_into_deployment(
        self, plugin_name: str, ta: str, plugin_local_path: str
    ):
        """
        Purpose:
            Copy plugin artifacts into platform specific directories for the deployment
        Args:
            plugin_name: Name of plugin
            ta: Type of plugin (network-manager, comms, core, artifact-manager)
            plugin_local_path: Location of plugin
        Return:
            N/A
        """

        # Copy Plugin Artifacts to volume mounted dirs
        unsupported_platform_arch_node_type_combos = []
        for (
            platform,
            architecture,
            node_type,
        ) in self.paths.supported_platform_arch_node_type_combinations:
            # Registry nodes use client artifacts
            if node_type == "registry":
                continue
            # Don't copy artifacts for node types that aren't part of this deployment
            if not self.cached_node_lists.get(f"{platform}_{node_type}_personas"):
                continue
            if not self.cached_node_lists.get(
                f"{platform}_bridge_{node_type}_personas"
            ) and not self.cached_node_lists.get(
                f"{architecture}_{node_type}_personas"
            ):
                continue
            platform_artifacts_path = f"{plugin_local_path}/artifacts/{self.paths.get_plugin_artifacts_base_dir_name(platform, architecture, node_type)}/"
            if os.path.isdir(platform_artifacts_path):
                plugin_files = general_utils.get_contents_of_dir(
                    file_path=platform_artifacts_path, include_dirs=True
                )
                for plugin_file in plugin_files:
                    plugin_destination = f'{self.paths.dirs[self.paths.get_plugin_artifacts_ta_dir_key(platform, architecture, node_type, ta)]}/{plugin_file.split("/")[-1]}'
                    general_utils.copy_dir_file(
                        plugin_file,
                        plugin_destination,
                        overwrite=True,
                    )
                    logger.trace(f"copied {plugin_file} to {plugin_destination}")
            else:
                unsupported_platform_arch_node_type_combos.append(
                    f"{platform}_{architecture}_{node_type}"
                )

        # Not all plugins/channels support all OS (mostly Android). This should not fail,
        # but we should warn to make sure that things are ok
        # TODO, we know if the deployment has nodes of these OS, should we
        # throw an error? if it possible that the plugin might be fine since not
        # all plugins will run on all nodes (e.g. s2s channels for simplicity). Network manager would
        # be a major issue.
        if unsupported_platform_arch_node_type_combos:
            # Explicitly ignore warnings for the apps
            if plugin_name not in {"AndroidApp", "LinuxApp"}:
                print(
                    f"WARNING: Plugin {plugin_name} does not contain artifacts "
                    f"for these nodes {unsupported_platform_arch_node_type_combos}"
                )

    ###
    # Rename Deployment Methods
    ###

    def rename(self, name: str, force: bool = False) -> None:
        """
        Purpose:
            Rename a deployment
        Args:
            name: New Name of the deployment
            force: Whether or not to force the operation
        Return:
            N/A
        Raises:
            Exception: when the move fails
            Exception: when the deployment is in the wrong status without force
            Exception: when the mode is not supported
        """

        if force and self.rib_mode in ("aws"):
            raise Exception(
                f"Force Rename Not Available for {self.rib_mode} Mode, "
                "Please `down` First"
            )

        # Check status pre remove
        self.status.verify_deployment_is_down(
            action="rename", force=force, forcible=True
        )

        # Update Info In in deployment config
        self.update_metadata({"name": name})

        # Move Dir
        shutil.move(self.paths.dirs["base"], f"{self.paths.dirs['mode']}/{name}")

        RibDeployment.update_configs(
            f"{self.paths.dirs['mode']}/{name}/{self.paths.filenames['config']}",
            {"name": name},
        )

    ###
    # Copy Deployment Methods
    ###

    def copy(self, name: str, copy_command: str, force: bool = False) -> None:
        """
         Purpose:
             Rename a deployment
        Args:
             name: Name of new deployment
             copy_command: Command used to copy/create new deployment
             force: Whether or not to force the operation
        Return:
            N/A
        Raises:
            Exception: when the copy fails
            Exception: when the deployment is in the wrong status without force
            Exception: when the mode is not supported
        """

        if force and self.rib_mode in ("aws"):
            raise Exception(
                f"Force Copy Not Available for {self.rib_mode} Mode, Please `down` First"
            )

        # Check status pre remove
        self.status.verify_deployment_is_down(
            action="copy",
            force=force,
            forcible=True,
        )

        # Copy Dir/Deployment
        shutil.copytree(self.paths.dirs["base"], f"{self.paths.dirs['mode']}/{name}")

        # update config file
        RibDeployment.update_configs(
            f"{self.paths.dirs['mode']}/{name}/{self.paths.filenames['config']}",
            {"name": name},
        )

        # Get New Deployment
        new_deployment = self.get_existing_deployment_or_fail(name, self.rib_mode)

        # Update Info In in deployment metadata
        new_deployment.update_metadata(
            {
                "name": name,
                "create_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                "create_command": copy_command,
            }
        )

    ###
    # Delete Deployment Methods
    ###

    def remove(self, force: bool = False) -> None:
        """
        Purpose:
            Remove a deployment
        Args:
            force: Whether or not to force the operation
        Return:
            N/A
        Raises:
            Exception: when the remove fails
            Exception: when the deployment is in the wrong status without force
            Exception: when the mode is not supported
        """

        if force and self.rib_mode in ("aws"):
            raise Exception(
                f"Force Remove Not Available for {self.rib_mode} Mode, Please `down` First"
            )

        self.status.verify_deployment_is_down(
            action="remove",
            force=force,
            forcible=self.rib_mode not in ("aws"),
        )

        # Remove the deployment dir
        shutil.rmtree(self.paths.dirs["base"])

    ###
    # Setup/Teardown Deployment Methods
    ###

    @abstractmethod
    def up(self) -> None:
        """
        Purpose:
            Setup and Stage a deployment. This will get the deployment to a point
            where all containers are running, all configs/code/etc is staged where
            it needs to be, and the Flask API for communicating with nodes is running
            and expecting requests.

            This does NOT start the RACE app on the nodes.
        Expected Args:
            **kwargs: Dynamic keyword args depending on deployment type
        Expected Return:
            N/A
        """

    def validate_global_configs(
        self,
        global_config_dir: str,
        require_global_config_plugins: bool = True,
    ) -> None:
        """
        Purpose:
            Validate global config directory contains all required files and that the
            files have the expected information
        Args:
            global_config_dir: User-specified global configs directory

            require_global_config_plugins: ensure that plugins are specified in
                the race.json file
        Return:
            N/A
        Raises:
            error_utils.RIB329: when global configs directory is missing a required file
            error_utils.RIB329: when plugins are required in race.json but the key
                is not set
        """

        # Check for missing files. There should be a set of known files
        missing = [
            filename
            for filename in self.paths.global_config_filenames
            if not os.path.exists(os.path.join(global_config_dir, filename))
        ]
        if missing:
            raise error_utils.RIB329(global_config_dir, missing)

        # Attempt to load the files and confirm they are well formatted
        for filename in self.paths.global_config_filenames:
            if filename.endswith(".json"):
                general_utils.load_file_into_memory(
                    os.path.join(global_config_dir, filename), data_format="json"
                )
            elif filename.endswith(".yaml") or filename.endswith(".yml"):
                general_utils.load_file_into_memory(
                    os.path.join(global_config_dir, filename), data_format="yaml"
                )

        if require_global_config_plugins:
            race_json = general_utils.load_file_into_memory(
                f"{self.paths.dirs['global_android_configs']}/race.json", "json"
            )
            if not race_json.get("plugins", None):
                raise error_utils.RIB334(
                    self.config["name"],
                    f"{self.paths.dirs['global_android_configs']}/race.json",
                )
            race_json = general_utils.load_file_into_memory(
                f"{self.paths.dirs['global_linux_configs']}/race.json", "json"
            )
            if not race_json.get("plugins", None):
                raise error_utils.RIB334(
                    self.config["name"],
                    f"{self.paths.dirs['global_linux_configs']}/race.json",
                )

    @abstractmethod
    def down(self, **kwargs: Dict[str, Any]) -> None:
        """
        Purpose:
            Teardown a deployment. This will takedown any containers running for the
            deployment, remove all configs/code/etc that was staged for the deployment (
            not the ones in /.race/rib/deployment, but if they were pushed to other
            hosts), and the API will no longer be running for communicating with
            the nodes.

            If the RACE test app is running and force is false, this will fail
        Expected Args:
            **kwargs: Dynamic keyword args depending on deployment type
        Expected Return:
            N/A
        """

    ###
    # Remote Interface/Client Methods
    ###

    @property
    def race_node_interface(self) -> race_node_utils.RaceNodeInterface:
        """
        Purpose:
            Returns an instance of the RACE node interface for communicating
            with RACE nodes, creating it if one has not already been created
        Args:
            N/A
        Returns:
            RACE node interface instance
        """
        if not self._race_node_interface:
            self._race_node_interface = self.create_race_node_interface()
        return self._race_node_interface

    @abstractmethod
    def create_race_node_interface(self) -> race_node_utils.RaceNodeInterface:
        """
        Purpose:
            Creates an instance of the RACE node interface for communicating
            with RACE nodes
        Args:
            N/A
        Returns:
            RACE node interface instance
        """

    @property
    def file_server_client(self) -> file_server_utils.FileServerClient:
        """
        Purpose:
            Returns an instance of the file server client for transferring
            files to/from RACE nodes, creating it if one has not already been created
        Args:
            N/A
        Returns:
            File server client instance
        """
        if not self._file_server_client:
            self._file_server_client = self.create_file_server_client()
        return self._file_server_client

    @abstractmethod
    def create_file_server_client(self) -> file_server_utils.FileServerClient:
        """
        Purpose:
            Creates an instance of a file server client for transferring
            files to/from RACE nodes
        Args:
            N/A
        Returns:
            File server client instance
        """

    ###
    # Subcommand interfaces
    ###

    @cached_property
    def rpc(self) -> rib_deployment_rpc.RibDeploymentRpc:
        """Deployment RPC commands"""
        return rib_deployment_rpc.RibDeploymentRpc(self)

    @cached_property
    def status(self) -> rib_deployment_status.RibDeploymentStatus:
        """Deployment Status commands"""
        return self.get_status()

    @abstractmethod
    def get_status(self):
        """Get the Status Object for the deployment"""

    ###
    # Bridged Node Methods
    ###

    @abstractmethod
    def get_vpn_ip_address(self) -> str:
        """
        Purpose:
            Get the IP address of the VPN server to be configured in bridged nodes
        Args:
            N/A
        Return:
            VPN server IP address
        """

    def _prepare_vpn_profile_config(self) -> str:
        """
        Purpose:
            Configures a VPN profile configuration for the current deployment
            to be used for bridged nodes
        Args:
            N/A
        Return:
            Location of the VPN profile configuration file
        """

        ip_address = self.get_vpn_ip_address()
        if not ip_address:
            raise error_utils.RIB345(self.rib_mode)

        template_token_file = f"{self.paths.dirs['base']}/vpn/tokens/race-client.ovpn"
        actuated_token_file = "/tmp/race.ovpn"

        # Remove previous token file in deployment if it existed
        if os.path.isfile(actuated_token_file):
            os.remove(actuated_token_file)

        # Copy to new file that we can update the ip address
        shutil.copyfile(template_token_file, actuated_token_file)

        # Set the correct IP in the token
        # TODO: add comment as to why we're using sh instead of subprocess.
        # TODO: suppress output of `sh.sed`. it shows up even with verbosity set to zero.
        sh.sed(
            [
                "-i",
                f"s/remote race 1194 udp/remote {ip_address} 1194 udp/",
                actuated_token_file,
            ],
            # _tty_out=False, # None of these work for suppressing command output to stdout
            # _out="/dev/null",
            # _err="/dev/null",
        )

        return actuated_token_file

    def prepare_bridged_android_device(
        self,
        persona: str,
        serial: str,
        allow_silent_installs: bool,
        push_configs: bool,
        install_daemon: bool = True,
    ) -> None:
        """
        Purpose:
            Prepares the specified Android device to bridge into the deployment
        Args:
            persona: RACE node persona that the device will run as
            serial: Android device serial number
            allow_silent_installs: Enable fully-automatic RACE app installation when bootstrapping
            push_configs: Push configs onto the Android device.
            install_daemon: Install the RACE node daemon on the device (default = True)
        Return:
            N/A
        """

        # Make sure that a different deployment isn't active.
        self.status.verify_deployment_is_active(
            "prepare bridged device in", none_ok=True
        )

        # Check that the persona exists.
        if persona not in self.android_bridge_client_personas:
            raise error_utils.RIB344(persona)

        is_genesis_node = persona in self.android_genesis_client_personas
        # If this is a genesis node make sure either the node daemon is installed or
        # configs are being pushed.
        if not install_daemon and not push_configs and is_genesis_node:
            raise error_utils.RIBa05(
                self.config["name"],
                self.rib_mode,
                serial,
                {
                    "invalid configuration",
                    "This device is a genesis node. You must either install the node daemon or push configs to the device.",
                },
            )
        if not is_genesis_node and push_configs:
            raise error_utils.RIBa05(
                self.config["name"],
                self.rib_mode,
                serial,
                {
                    "invalid parameters": "pushing configs to a bootstrap device is invalid"
                },
            )

        device = adb_utils.RaceAndroidDevice(
            adb_client=adb_utils.create_adb_client(),
            serial=serial,
        )

        # TODO limit supported architectures to available plugin artifacts
        device.verify_compatible_with_race(
            supported_architectures=["x86_64", "arm64-v8a"]
        )

        # Make sure nothing is left over from a previous run (however, it's fine if the VPN client app is still installed from a previous call to prepare).
        report = device.get_preparation_status_report(
            include_vpn_app_installation=False
        )
        if any(report.values()):
            raise error_utils.RIBa04(
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                serial=serial,
                details=report,
            )

        plugin_dir = f"{self.paths.dirs['plugins']}/android-{device.device_info['architecture']}-client"

        if not device.vpn_app_installed:
            device.install_vpn_app()
        device.push_vpn_profile(self._prepare_vpn_profile_config())
        if push_configs:
            device.push_configs(
                f"{self.paths.dirs['race_configs']}/{self.get_configs_tar_name(persona)}"
            )
            device.push_etc(f"{self.paths.dirs['etc']}/{persona}")
        device.set_race_deployment(self.config["name"])
        device.set_race_persona(persona)
        device.set_race_encryption_type(self.config["race_encryption_type"])
        if install_daemon:
            device.install_race_daemon(
                f"{plugin_dir}/core/race-daemon/race-daemon-android-debug.apk"
            )
            if allow_silent_installs:
                device.set_daemon_as_device_owner()
                device.disable_play_protect()

        if is_genesis_node:
            device.install_race_app(f"{plugin_dir}/core/race/race.apk")
            device.push_artifacts(plugin_dir)

        report = device.get_preparation_status_report(
            include_race_app_installation=is_genesis_node
        )
        if not all(report.values()):
            raise error_utils.RIBa05(
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                serial=serial,
                details=report,
            )

    def prepare_bridged_android_device_archive(
        self, persona: str, architecture: str, overwrite: bool
    ) -> str:
        """
        Purpose:
            Prepares an archive for a given persona that can be used to prepare an
            Android device to be bridged into the deployment.
        Args:
            persona: RACE node personato prepare the archive for.
            architecture: The architecture (arm64-v8a or x86_64) that will use this prepare archive.
            overwrite: Overwrite any existing archive.
        Return:
            File path of the android device archive.
        """

        self.status.verify_deployment_is_active(
            "prepare archive for bridged device", none_ok=True
        )

        if persona not in self.android_bridge_client_personas:
            raise error_utils.RIB344(persona)

        plugin_dir = f"{self.paths.dirs['plugins']}/android-{architecture}-client"

        prepare_archive_path = f"{self.paths.dirs['device-prepare-archives']}/{persona}-device-prepare.tar.gz"

        if os.path.exists(prepare_archive_path):
            if not overwrite:
                raise FileExistsError(
                    f"File {prepare_archive_path} already exists. Use the overwrite option to overwrite it."
                )
            os.remove(prepare_archive_path)

        def add_text_file_to_archive(
            archive: tarfile.TarFile, filename: str, content: str
        ) -> None:
            """
            Purpose:
                Add a text file with given name and contents to a tar file. Saves the
                trouble of creating a temporary file that would then need to be cleaned
                up
            Args:
                archive: The tar to save the text file to.
                filename: The name to give the file that is added to the tar.
                content: The content of the file being added to the tar.
            """
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            archive.addfile(
                tarinfo=tarinfo, fileobj=io.BytesIO(content.encode("utf-8"))
            )

        with tarfile.open(prepare_archive_path, "w:gz") as out:
            is_genesis_node = persona in self.android_genesis_client_personas
            vpn_profile_file_path = self._prepare_vpn_profile_config()
            out.add(
                vpn_profile_file_path,
                arcname=os.path.basename(vpn_profile_file_path),
            )

            add_text_file_to_archive(out, "deployment.txt", self.config["name"])
            add_text_file_to_archive(out, "persona.txt", persona)
            add_text_file_to_archive(
                out, "encryption_type.txt", self.config["race_encryption_type"]
            )

            out.add(plugin_dir, arcname="plugins")

            # Only include configs for genesis nodes.
            if is_genesis_node:
                out.add(
                    f"{self.paths.dirs['race_configs']}/{self.get_configs_tar_name(persona)}",
                    arcname="configs.tar.gz",
                )

            out.add(f"{self.paths.dirs['etc']}/{persona}", arcname="etc")
            # Overwrite the jaeger config to disable opentracing.
            add_text_file_to_archive(out, "etc/jaeger-config.yml", "disabled: true")

        return prepare_archive_path

    def connect_bridged_android_device(self, serial: str, timeout: int = 120) -> None:
        """
        Purpose:
            Connects the bridged Android device identified by the given serial number
        Args:
            serial: Serial number of the Android device
            timeout: Time in seconds to timeout if the command fails
        Return:
            N/A
        """

        self.status.verify_deployment_is_active("connect bridged device to")

        device = adb_utils.RaceAndroidDevice(
            adb_client=adb_utils.create_adb_client(),
            serial=serial,
        )

        is_genesis_node = (
            device.race_persona_prop in self.android_genesis_client_personas
        )
        report = device.get_preparation_status_report(
            include_race_app_installation=is_genesis_node
        )
        if not all(report.values()):
            raise error_utils.RIBa07(
                action="connect",
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                serial=serial,
                details=report,
            )

        device.connect_vpn()
        device.start_race_daemon()

        self.status.wait_for_nodes_to_match_status(
            action="connect",
            personas=[device.race_persona_prop],
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            timeout=timeout,
        )
        nodes_with_configs_pushed = self.status.get_nodes_that_match_status(
            action="pull configs",
            personas=[device.race_persona_prop],
            configs_status=[status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED],
        )
        self.race_node_interface.set_daemon_config(
            deployment_name=self.config["name"],
            persona=device.race_persona_prop,
            genesis=self.config["nodes"][device.race_persona_prop]["genesis"],
            app="",  # Android doesn't use this field because there's only one app
        )
        pull_etc_only = False if nodes_with_configs_pushed else True
        self.race_node_interface.pull_configs(
            deployment_name=self.config["name"],
            persona=device.race_persona_prop,
            etc_only=pull_etc_only,
        )
        if is_genesis_node:
            self.status.wait_for_nodes_to_match_status(
                action="pull configs",
                personas=[device.race_persona_prop],
                app_status=[status_utils.AppStatus.NOT_RUNNING],
                configs_status=[status_utils.ConfigsStatus.DOWNLOADED_CONFIGS],
            )
        else:
            self.status.wait_for_nodes_to_match_status(
                action="pull configs",
                personas=[device.race_persona_prop],
                app_status=[status_utils.AppStatus.NOT_INSTALLED],
                # etc_status=[status_utils.EtcStatus.READY],
            )

    def disconnect_bridged_android_device(
        self, serial: str, timeout: int = 120
    ) -> None:
        """
        Purpose:
            Disconnects the bridged Android device identified by the given serial number
        Args:
            serial: Serial number of the Android device
            timeout: Time in seconds to timeout if the command fails
        Return:
            N/A
        """

        self.status.verify_deployment_is_active("disconnect bridged device from")

        device = adb_utils.RaceAndroidDevice(
            adb_client=adb_utils.create_adb_client(),
            serial=serial,
        )

        report = device.get_preparation_status_report(
            include_race_app_installation=False
        )
        if not all(report.values()):
            raise error_utils.RIBa07(
                action="disconnect",
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                serial=serial,
                details=report,
            )

        device.stop_race_app()
        device.stop_race_daemon()
        device.disconnect_vpn()

        self.status.wait_for_nodes_to_match_status(
            action="disconnect",
            personas=[device.race_persona_prop],
            daemon_status=[status_utils.DaemonStatus.NOT_REPORTING],
            timeout=timeout,
        )

    def unprepare_bridged_android_device(self, serial: str) -> None:
        """
        Purpose:
            Unprepares the bridged Android device identified by the given serial number
        Args:
            serial: Serial number of the Android device
        Return:
            N/A
        """

        self.status.verify_deployment_is_active(
            "unprepare bridged device in", none_ok=True
        )

        device = adb_utils.RaceAndroidDevice(
            adb_client=adb_utils.create_adb_client(),
            serial=serial,
        )

        device.remove_vpn_profile()
        device.unset_race_deployment()
        device.unset_race_persona()
        device.unset_race_encryption_type()
        device.remove_daemon_as_device_owner()
        device.enable_play_protect()
        device.uninstall_race_daemon()
        device.uninstall_race_app()
        device.remove_race_data()

        report = device.get_preparation_status_report(
            include_vpn_app_installation=False
        )
        if any(report.values()):
            raise error_utils.RIBa06(
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                serial=serial,
                details=report,
            )

    ###
    # Setup/Teardown App Methods
    ###

    def tar_configs(
        self, nodes: Optional[List[str]] = None, timeout: int = 120, force: bool = False
    ) -> None:
        """
        Purpose:
            Tar configs
        Args:
            nodes: What nodes to tar configs for. If None, all nodes will be used
            timeout: Time in seconds to timeout if tar fails
            force: Ignore status checks
        Return:
            N/A
        """
        logger.info("Creating configs archive")

        # If no nodes specified, tar configs for all RACE nodes
        nodes_to_tar_configs_for = nodes or self.personas

        # Have to disable the pylint error on the next line because the class method get_active
        # requires parameters but the instance method get_active (which we're calling) doesn't
        # pylint: disable-next=no-value-for-parameter
        active_deployment = self.get_active()
        # Get list of nodes that do not yet have config tars
        nodes_with_configs = self.status.get_nodes_that_match_status(
            action="tar configs for",
            personas=nodes_to_tar_configs_for,
            configs_status=[status_utils.ConfigsStatus.CONFIG_GEN_SUCCESS],
            force=force,
            offline=active_deployment and active_deployment != self.config["name"],
        )
        for persona in nodes_with_configs:
            # Create tar.gz
            config_tar = "/".join(
                [
                    self.paths.dirs["race_configs"],
                    f"{self.config['name']}_{persona}_configs.tar.gz",
                ]
            )
            if os.path.isfile(config_tar):
                # No need to have a separate message/check about using force
                # because the precondition status check will fail if the file
                # exists and 'force' wasn't used
                os.remove(config_tar)
            with tarfile.open(config_tar, "w:gz") as out:
                # Only provide configs to genesis nodes.
                if persona in self.genesis_personas:
                    # Add Network Manager Configs
                    network_manager_plugin_name = self.config.network_manager_kit.name
                    out.add(
                        f'{self.paths.dirs["network_manager_configs_base"]}/{network_manager_plugin_name}/{persona}/',
                        arcname=f"data/configs/{network_manager_plugin_name}",
                    )
                    network_manager_shared_configs = f'{self.paths.dirs["network_manager_configs_base"]}/{network_manager_plugin_name}/shared/'
                    if os.path.exists(network_manager_shared_configs):
                        out.add(
                            network_manager_shared_configs,
                            arcname=f"data/configs/{network_manager_plugin_name}",
                        )
                    # Add Global Configs
                    if persona in self.android_client_personas:
                        out.add(
                            f'{self.paths.dirs["global_android_configs"]}',
                            arcname=f"data/configs/sdk",
                        )
                    else:
                        out.add(
                            f'{self.paths.dirs["global_linux_configs"]}',
                            arcname=f"data/configs/sdk",
                        )

                    # Add comms Configs
                    for channel in self.config.comms_channels:
                        comms_persona_configs = f'{self.paths.dirs["comms_configs_base"]}/{channel.kit_name}/{channel.name}/{persona}/'
                        if os.path.exists(comms_persona_configs):
                            out.add(
                                comms_persona_configs,
                                arcname=f"data/configs/{channel.kit_name}/{channel.name}",
                            )

                        comms_shared_configs = f'{self.paths.dirs["comms_configs_base"]}/{channel.kit_name}/{channel.name}/shared/'
                        if os.path.exists(comms_shared_configs):
                            out.add(
                                comms_shared_configs,
                                arcname=f"data/configs/{channel.kit_name}/{channel.name}",
                            )

                out.close()

            # Create etc tar.gz
            etc_tar = "/".join(
                [
                    self.paths.dirs["etc"],
                    f"{self.config['name']}_{persona}_etc.tar.gz",
                ]
            )
            if os.path.isfile(etc_tar) and force:
                # No need to have a separate message/check about using force
                # because the precondition status check will fail if the file
                # exists and 'force' wasn't used
                os.remove(etc_tar)
            with tarfile.open(etc_tar, "w:gz") as out:
                # Add etc files
                out.add(f'{self.paths.dirs["etc"]}/{persona}', arcname="")
                out.close()
            logger.info(f"Created configs/etc archives for {persona}")

    def upload_configs(
        self,
        nodes: Optional[List[str]] = None,
        timeout: int = 120,
        force: bool = False,
        require: Require = Require.ANY,
        quiet: bool = False,
    ) -> None:
        """
        Purpose:
            Upload configs to file server
        Args:
            nodes: What nodes to upload configs for. If None, all nodes will be used
            timeout: Time in seconds to timeout if upload fails
            force: Ignore status checks
            require: Raise an error if the matching containers don't meet the requirement
            quiet: Disable logging of matching/unmatching nodes (e.g., when part of a loop)
        Return:
            N/A
        """

        logger.info("Uploading configs archive")
        self.status.verify_deployment_is_active("publish configs")

        # If no nodes specified, upload configs for all RACE nodes
        nodes_to_upload_configs_for = nodes or self.personas

        # Get list of nodes that have config tars that have not been uploaded to the file server yet
        nodes_with_config_tars = self.status.get_nodes_that_match_status(
            action="upload configs",
            personas=nodes_to_upload_configs_for,
            configs_status=[status_utils.ConfigsStatus.CONFIGS_TAR_EXISTS],
            force=force,
            require=require,
            quiet=quiet,
        )
        for persona in nodes_with_config_tars:
            config_tar = "/".join(
                [
                    self.paths.dirs["race_configs"],
                    f"{self.config['name']}_{persona}_configs.tar.gz",
                ]
            )
            self.file_server_client.upload_file(config_tar)

            etc_tar = "/".join(
                [
                    self.paths.dirs["etc"],
                    f"{self.config['name']}_{persona}_etc.tar.gz",
                ]
            )
            self.file_server_client.upload_file(etc_tar)

    def install_configs(
        self,
        nodes: Optional[List[str]] = None,
        timeout: int = 120,
        force: bool = False,
        quiet: bool = False,
    ) -> None:
        """
        Purpose:
            Install configs tar on each node
        Args:
            nodes: What nodes to install configs for. If None, all nodes will be used
            timeout: Time in seconds to timeout if upload fails
            force: Ignore status checks
            quiet: Disable logging of matching/unmatching nodes (e.g., when part of a loop)
        Return:
            N/A
        """
        logger.info("Installing configs on nodes")
        # If no nodes specified, stand up all RACE nodes
        nodes_to_install = nodes or self.managed_personas
        # Call the node daemon to trigger a pull of the configs from the file server.
        nodes_with_configs_pushed = self.status.get_nodes_that_match_status(
            action="install configs",
            personas=nodes_to_install,
            configs_status=[status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED],
            force=force,
            quiet=quiet,
        )
        for node_name in nodes_to_install:
            pull_etc_only = False if node_name in nodes_with_configs_pushed else True
            self.race_node_interface.pull_configs(
                deployment_name=self.config["name"],
                persona=node_name,
                etc_only=pull_etc_only,
            )

    def delete_config_tars(self) -> None:
        """
        Purpose:
            Config tar files should be deleted when the deployment is down so that they don't get
            added to on the next up and so new config changes are reflected.
        Args:
            N/A
        Return:
            N/A
        """
        logger.info("Removing configs archive")
        for persona in self.personas:
            # Create tar.gz
            config_tar = "/".join(
                [self.paths.dirs["race_configs"], f"{persona}_configs.tar.gz"]
            )
            if os.path.isfile(config_tar):
                os.remove(config_tar)

    def start(
        self,
        last_start_command: Optional[str] = None,
        force: bool = False,
        timeout: int = 300,
        nodes: Optional[List[str]] = None,
    ) -> None:
        """
        Purpose:
            Start the RACE app on all nodes (or a given subset) in the deployment.
        Args:
            last_start_command: The command (CLI) that started the deployment
            force: Whether or not to force the operation
            timeout: Time in seconds to timeout if the command fails
            nodes: Optional list of nodes to be started, or else all applicable nodes in
                the deployment
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("start")

        # Get the nodes that can be started (this will also make sure services are running).
        can_be_started = self.status.get_nodes_that_match_status(
            action="start",
            personas=nodes,
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            app_status=[status_utils.AppStatus.NOT_RUNNING],
            force=force,
        )

        # Upload distribution artifacts if this is the first time that nodes are being started
        started_apps = self.status.get_nodes_that_match_status(
            action="",
            app_status=[status_utils.AppStatus.RUNNING],
            require=Require.NONE,
            quiet=True,
        )
        # Don't re-upload if some apps are running
        if not started_apps:
            self.upload_artifacts(timeout=timeout)

        failed_to_start = {}
        for node_name in can_be_started:
            try:
                self.race_node_interface.start_app(node_name)
            except Exception as error:
                failed_to_start[node_name] = error

        if failed_to_start:
            raise error_utils.RIB412(action="start", reasons=failed_to_start)

        # Check status post start
        self.status.wait_for_nodes_to_match_status(
            action="start",
            personas=can_be_started,
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            app_status=[status_utils.AppStatus.RUNNING],
            race_status=[status_utils.RaceStatus.RUNNING],
            timeout=timeout,
        )

        # Update Config
        self.update_metadata(
            {
                "last_start_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
                "last_start_command": last_start_command,
            }
        )

    def rotate_logs(
        self,
        backup_id: Optional[str] = None,
        delete: bool = True,
        force: bool = False,
        nodes: Optional[List[str]] = None,
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Rotate the logs between deployment runs.

            Optionally backs up logs from the requested nodes into logs/<timestamp>.
            Optionally deletes logs on RACE nodes.
        Args:
            backup_id: Unique identifier (e.g., a timestamp) for the backed up logs,
                if empty no backup will occur
            delete: Whether to delete logs
            force: Whether or not to force the operation
            nodes: Optional list of nodes on which to rotate logs, or else all
                applicable nodes in the deployment
            timeout: Time in seconds before raising an error
        Return:
            N/A
        """
        if backup_id and delete:
            action = "rotate logs for"
        elif backup_id:
            action = "backup logs for"
        elif delete:
            action = "delete logs for"
        else:
            # Neither backup nor delete enabled, what are we supposed to do?
            raise error_utils.RIB325(
                self.config["name"], "Invalid log rotation options"
            )

        self.status.verify_deployment_is_active(action)

        can_be_rotated = self.status.get_nodes_that_match_status(
            action=action,
            personas=nodes,
            app_status=[
                status_utils.AppStatus.NOT_RUNNING,
                status_utils.AppStatus.NOT_INSTALLED,
            ]
            if delete
            else None,
            force=force,
        )

        waiting_for_logs = []
        for node_name in can_be_rotated:
            try:
                self.race_node_interface.rotate_logs(
                    node_name, backup_id=backup_id, delete=delete
                )
                waiting_for_logs.append(node_name)
            except Exception as error:
                logger.error(f"Unable to rotate logs for {node_name}: {error}")

        if backup_id:
            backup_dir = "/".join([self.paths.dirs["previous-runs"], backup_id])
            os.makedirs(backup_dir, exist_ok=True)

            # Copy just the backed up nodes
            for node_name in can_be_rotated:
                local_node_log_dir = "/".join([self.paths.dirs["logs"], node_name])
                if os.path.exists(local_node_log_dir):
                    backup_node_dir = "/".join([backup_dir, node_name])
                    try:
                        shutil.copytree(
                            local_node_log_dir,
                            backup_node_dir,
                            dirs_exist_ok=True,
                        )
                    except shutil.Error:
                        raise Exception(
                            f"log rotation failed to copy logs from {local_node_log_dir} "
                            f"to {backup_dir}"
                        )

            logger.info(
                f"Waiting for {len(waiting_for_logs)} nodes to backup log files...",
            )
            failed_to_download = {}
            command_run_time = datetime.now()
            while waiting_for_logs:
                for node_name in waiting_for_logs:
                    try:
                        log_bundle_name = f"logs-{backup_id}-{node_name}.tar.gz"
                        log_bundle_path = "/".join([backup_dir, f"{node_name}.tar.gz"])
                        if self.file_server_client.download_file(
                            log_bundle_name, log_bundle_path
                        ):
                            log_dir = "/".join([backup_dir, node_name])
                            os.makedirs(log_dir, exist_ok=True)
                            with tarfile.open(log_bundle_path, "r:gz") as tar:
                                tar.extractall(log_dir)
                            os.remove(log_bundle_path)
                            waiting_for_logs.remove(node_name)
                    except Exception as error:
                        if node_name not in failed_to_download:
                            # This is the first time it failed, let it try once more
                            failed_to_download[node_name] = ""
                        else:
                            # It already had a second chance, it's a lost cause
                            waiting_for_logs.remove(node_name)
                            failed_to_download[node_name] = str(error)

                if not waiting_for_logs:
                    logger.info("Done waiting for node log files")
                    break

                if (datetime.now() - command_run_time).seconds > timeout:
                    break

                time.sleep(1)

            # Report any failed downloads
            for node_name, error in failed_to_download.items():
                if error:
                    logger.error(f"Failed to download logs for {node_name}: {error}")

            if waiting_for_logs:
                raise error_utils.RIB332(
                    deployment_name=self.config["name"],
                    rib_mode=self.rib_mode,
                    action=action,
                    info=waiting_for_logs,
                )

        if delete:
            # Delete the current log dirs, but maintain the directory structure since
            # these are Docker volume mounts and deleting them will mess things up.
            for sub_log_dir in os.listdir(self.paths.dirs["logs"]):
                # Do not delete the opentracing log files. These need to be maintained
                # between runs, otherwise the jaeger UI will break.
                if "opentracing" in sub_log_dir:
                    continue
                node_name = sub_log_dir.split("/")[-1]
                if node_name in can_be_rotated:
                    absolute_sub_log_dir = f"{self.paths.dirs['logs']}/{sub_log_dir}"
                    for file_to_delete in os.listdir(absolute_sub_log_dir):
                        absolute_file_to_delete = (
                            f"{absolute_sub_log_dir}/{file_to_delete}"
                        )
                        try:
                            os.remove(absolute_file_to_delete)
                        except OSError:
                            shutil.rmtree(absolute_file_to_delete, ignore_errors=True)

    def pull_runtime_configs(
        self, config_name: str, overwrite: bool = False, timeout: int = 120
    ) -> None:
        """
        Purpose

        Args:
            config_name (str): Name to give the directory where runtime configs will be stored.
            timeout (int, optional): Time in seconds to wait for operation to complete. Defaults to 120.
        """

        # Get the nodes that have runtime configs
        nodes_with_runtime_configs = self.status.get_nodes_that_match_status(
            action="pull-runtime",
            personas=self.personas,
            configs_status=[status_utils.ConfigsStatus.EXTRACTED_CONFIGS],
        )

        config_dest_dir = "/".join([self.paths.dirs["runtime-configs"], config_name])
        if os.path.isdir(config_dest_dir):
            if overwrite:
                shutil.rmtree(config_dest_dir)
            else:
                raise error_utils.RIB349(
                    f"name already exists: {config_name}",
                    "Choose a different name and rerun the command",
                )

        log_prefix = "pull_runtime_configs: "

        waiting_for_configs = []
        for node_name in nodes_with_runtime_configs:
            try:
                self.race_node_interface.push_runtime_configs(node_name, config_name)
                waiting_for_configs.append(node_name)
            except Exception as error:
                logger.error(f"Unable to save runtime configs for {node_name}: {error}")

        logger.info(
            f"Waiting for {len(waiting_for_configs)} nodes to save runtime configs...",
        )

        os.makedirs(config_dest_dir, exist_ok=True)
        failed_to_download = {}
        command_run_time = datetime.now()
        while waiting_for_configs:
            for node_name in waiting_for_configs:
                try:
                    config_tar_name = (
                        f"runtime-configs-{config_name}-{node_name}.tar.gz"
                    )
                    config_tar_path = "/".join([config_dest_dir, f"{node_name}.tar.gz"])
                    if self.file_server_client.download_file(
                        config_tar_name, config_tar_path
                    ):
                        logger.trace(f"{log_prefix}downloaded file: {config_tar_path}")
                        config_dir = "/".join([config_dest_dir, node_name])
                        os.makedirs(config_dir, exist_ok=True)

                        logger.trace(
                            f"{log_prefix}extracting {config_tar_path} to {config_dir} ..."
                        )
                        with tarfile.open(config_tar_path, "r:gz", errorlevel=2) as tar:
                            tar.extractall(config_dir)
                        logger.trace(
                            f"{log_prefix}extracted {config_tar_path} to {config_dir}"
                        )

                        os.remove(config_tar_path)
                        waiting_for_configs.remove(node_name)
                except Exception as error:
                    if node_name not in failed_to_download:
                        # This is the first time it failed, let it try once more.
                        failed_to_download[node_name] = ""
                    else:
                        # If it failed once before just give up.
                        waiting_for_configs.remove(node_name)
                        failed_to_download[node_name] = str(error)

            if not waiting_for_configs:
                logger.info("Done waiting for node runtime configs")
                break

            if (datetime.now() - command_run_time).seconds > timeout:
                break

            time.sleep(1)

        # Report any failed downloads
        for node_name, error in failed_to_download.items():
            if error:
                logger.error(f"Failed to download configs for {node_name}: {error}")

        if waiting_for_configs:
            raise error_utils.RIB332(
                deployment_name=self.config["name"],
                rib_mode=self.rib_mode,
                action="save runtime configs",
                info=waiting_for_configs,
            )

    def push_runtime_configs(self, config_name: str, timeout: int = 120) -> None:
        config_src_dir = "/".join([self.paths.dirs["runtime-configs"], config_name])
        if not os.path.isdir(config_src_dir):
            # TODO: raise some RiB error
            raise Exception(f"config path does not exist: {config_src_dir}")

        # Check that the deployment is up, but not running.
        self.status.get_nodes_that_match_status(
            action="publish runtime configs",
            configs_status=[status_utils.ConfigsStatus.CONFIGS_TAR_EXISTS],
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            app_status=[status_utils.AppStatus.NOT_RUNNING],
            require=Require.ALL,
        )

        # Upload the RACE configs to the file server.
        # Iterate over the runtime config directory. It *should* just be a list of
        # directories with the same names as personas in the deployment.
        for persona in os.listdir(config_src_dir):
            persona_config_path = f"{config_src_dir}/{persona}"
            # Check that the directory name is a valid persona.
            if persona not in self.personas:
                logger.warn(
                    f"found invalid runtime config directory at {persona_config_path}. Where did this file come from? Ignoring for now."
                )
                continue
            # Check that the path is a directory.
            if not os.path.isdir(persona_config_path):
                logger.warn(f"path is not a directory: {persona_config_path}")
                continue

            # Create tar.gz of the runtime configs for the persona.
            config_tar = self.get_configs_tar_name(persona)
            with tarfile.open(config_tar, "w:gz") as out:
                # Add all the runtime configs to the tar.
                for nested_config_dir in os.listdir(persona_config_path):
                    out.add(
                        f"{persona_config_path}/{nested_config_dir}",
                        arcname=f"data/{nested_config_dir}",
                    )

            # upload to file server
            self.file_server_client.upload_file(config_tar)

            # Upload /etc/ configs.
            etc_tar = "/".join(
                [
                    self.paths.dirs["etc"],
                    f"{self.config['name']}_{persona}_etc.tar.gz",
                ]
            )
            self.file_server_client.upload_file(etc_tar)

    def list_runtime_configs(self) -> List[str]:
        try:
            return os.listdir(self.paths.dirs["runtime-configs"])
        except FileNotFoundError:
            return []

    def stop(
        self,
        force: bool = False,
        nodes: Optional[List[str]] = None,
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Stop the RACE app on all nodes (or a given subset) in the deployment.
        Args:
            force: Whether or not to force the operation
            nodes: Optional list of nodes to be stopped, or else all applicable nodes in
                the deployment
            timeout: Time in seconds to timeout if the command fails
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("stop")

        # Get the nodes that can be stopped
        can_be_stopped = self.status.get_nodes_that_match_status(
            action="stop",
            personas=nodes,
            app_status=[status_utils.AppStatus.RUNNING],
            force=force,
        )

        node_stop_errors = {}
        for node_name in can_be_stopped:
            try:
                self.race_node_interface.stop_app(node_name)
            except Exception as error:
                node_stop_errors[node_name] = error

        if node_stop_errors:
            raise error_utils.RIB412(action="stop", reasons=node_stop_errors)

        # Check status post stop
        self.status.wait_for_nodes_to_match_status(
            action="stop",
            personas=can_be_stopped,
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            app_status=[status_utils.AppStatus.NOT_RUNNING],
            timeout=timeout,
        )

        # Update Info In in deployment config
        # TODO: Refactor metadata, as last_stop_time may not make sense when stopping
        #       individual nodes
        self.update_metadata(
            {"last_stop_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S")}
        )

    def clear(
        self,
        nodes: List[str],
        force: bool = False,
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Clear all nodes (or a given subset) in the deployment.
        Args:
            nodes: List of nodes to be clear in the deployment
            force: Whether or not to force the operation
            timeout: Time in seconds to timeout if the command fails
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("clear", none_ok=force)

        # Get the nodes that can be cleared
        can_be_cleared = self.status.get_nodes_that_match_status(
            action="clear",
            personas=nodes,
            etc_status=[
                status_utils.EtcStatus.READY,
                status_utils.EtcStatus.ETC_TAR_PUSHED,
            ],
            app_status=[
                status_utils.AppStatus.NOT_INSTALLED,
                status_utils.AppStatus.NOT_REPORTING,
                status_utils.AppStatus.NOT_RUNNING,
            ],
            force=force,
        )
        if not can_be_cleared:
            return
        failed_to_clear = {}
        for node_name in can_be_cleared:
            try:
                self.race_node_interface.clear_configs_and_etc(node_name)
                if not self.config["nodes"][node_name]["genesis"]:
                    self.race_node_interface.clear_artifacts(node_name)
            except Exception as error:
                failed_to_clear[node_name] = error

        if failed_to_clear and not force:
            raise error_utils.RIB412(action="clear", reasons=failed_to_clear)

        genesis_can_be_cleared = set(can_be_cleared) & set(self.genesis_personas)
        non_genesis_can_be_cleared = set(can_be_cleared) & set(
            self.bootstrap_client_personas
        )

        # Check status post clear
        if genesis_can_be_cleared:
            self.status.wait_for_nodes_to_match_status(
                action="clear on-node config and etc files",
                personas=genesis_can_be_cleared,
                configs_status=[
                    status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED,
                    status_utils.ConfigsStatus.CONFIGS_TAR_EXISTS,
                ],
                etc_status=[
                    status_utils.EtcStatus.ETC_TAR_PUSHED,
                    status_utils.EtcStatus.ETC_TAR_EXISTS,
                ],
                timeout=timeout,
            )
        if non_genesis_can_be_cleared:
            self.status.wait_for_nodes_to_match_status(
                action="clear on-node etc files",
                personas=non_genesis_can_be_cleared,
                app_status=[
                    status_utils.AppStatus.NOT_INSTALLED,
                    status_utils.AppStatus.NOT_REPORTING,
                ],
                etc_status=[
                    status_utils.EtcStatus.ETC_TAR_PUSHED,
                    status_utils.EtcStatus.ETC_TAR_EXISTS,
                ],
                timeout=timeout,
            )

        # Clear configs from file server
        if len(can_be_cleared) == len(self.all_personas):
            if not self.file_server_client.delete_all():
                # Don't raise error because the important piece (clearing nodes) is complete
                logger.error("Failed to clear file server")
        else:
            for persona in can_be_cleared:
                # Attempt to delete configs and etc regardless of bootstrap status
                self.file_server_client.delete_file(
                    self.get_configs_tar_name(persona=persona)
                )
                self.file_server_client.delete_file(
                    self.get_etc_tar_name(persona=persona)
                )

        # Check status post clear
        self.status.wait_for_nodes_to_match_status(
            action="clear",
            personas=can_be_cleared,
            configs_status=[
                status_utils.ConfigsStatus.CONFIGS_TAR_EXISTS,
                status_utils.ConfigsStatus.CONFIG_GEN_SUCCESS,
            ],
            etc_status=[status_utils.EtcStatus.ETC_TAR_EXISTS],
            timeout=timeout,
        )

        # Update Info In in deployment config
        self.update_metadata(
            {"last_clear_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S")}
        )

    def reset(
        self,
        nodes: List[str],
        force: bool = False,
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Reset all nodes (or a given subset) in the deployment.
        Args:
            nodes: List of nodes to be reset in the deployment
            force: Whether or not to force the operation
            timeout: Time in seconds to timeout if the command fails
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("reset")

        # Get the nodes that can be reset
        can_be_reset = self.status.get_nodes_that_match_status(
            action="reset",
            personas=nodes,
            configs_status=[
                status_utils.ConfigsStatus.DOWNLOADED_CONFIGS,
                status_utils.ConfigsStatus.EXTRACTED_CONFIGS,
            ],
            etc_status=[status_utils.EtcStatus.READY],
            force=force,
        )
        failed_to_reset = {}
        for node_name in can_be_reset:
            try:
                self.race_node_interface.clear_configs_and_etc(node_name)
                if not self.config["nodes"][node_name]["genesis"]:
                    self.race_node_interface.clear_artifacts(node_name)
                    self.race_node_interface.pull_configs(
                        deployment_name=self.config["name"],
                        persona=node_name,
                        etc_only=True,
                    )
                else:
                    self.race_node_interface.pull_configs(
                        deployment_name=self.config["name"],
                        persona=node_name,
                        etc_only=False,
                    )
            except Exception as error:
                failed_to_reset[node_name] = error

        if failed_to_reset:
            raise error_utils.RIB412(action="reset", reasons=failed_to_reset)

        # Check status post reset
        self.status.wait_for_nodes_to_match_status(
            action="reset",
            personas=can_be_reset,
            configs_status=[
                status_utils.ConfigsStatus.DOWNLOADED_CONFIGS,
                status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED,
                status_utils.ConfigsStatus.CONFIGS_TAR_EXISTS,
            ],
            etc_status=[status_utils.EtcStatus.READY],
            app_status=[
                status_utils.AppStatus.NOT_RUNNING,
                status_utils.AppStatus.NOT_INSTALLED,
            ],
            timeout=timeout,
        )

        # Update Info In in deployment config
        self.update_metadata(
            {"last_reset_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S")}
        )

    def kill(
        self,
        nodes: List[str],
        force: bool = False,
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Stop the RACE app on all nodes (or a given subset) in the deployment.
        Args:
            nodes: List of nodes to be killed in the deployment
            force: Whether or not to force the operation
            timeout: Time in seconds to timeout if the command fails
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("kill")

        # Get the nodes that can be killed
        can_be_killed = self.status.get_nodes_that_match_status(
            action="kill",
            personas=nodes,
            app_status=[status_utils.AppStatus.RUNNING],
            force=force,
        )

        failed_to_kill = {}
        for node_name in can_be_killed:
            try:
                self.race_node_interface.kill_app(node_name)
            except Exception as error:
                failed_to_kill[node_name] = error

        if failed_to_kill:
            raise error_utils.RIB412(action="kill", reasons=failed_to_kill)

        # Check status post stop
        self.status.wait_for_nodes_to_match_status(
            action="kill",
            personas=can_be_killed,
            app_status=[status_utils.AppStatus.NOT_RUNNING],
            timeout=timeout,
        )

        # Update Info In in deployment config
        # TODO: Refactor metadata, as last_kill_time may not make sense when because
        #       we only ever kill individual nodes, not the entire deployment
        self.update_metadata(
            {"last_kill_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S")}
        )

    def bootstrap_node(
        self,
        force: bool,
        introducer: str,
        target: str,
        passphrase: str,
        architecture: str,
        bootstrapChannelId: str = "",
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Bootstrap a non-RACE node into the RACE network, using an introducing node.
        Expected Args:
            force: Bypass precondition checks
            introducer: Node to act as the introducer of the new node
            target: Node to be introduced into the RACE network
            passphrase: Bootstrap passphrase
            boostrapChannelId: Preferred bootstrap channel
            architecture: Architecture of the node to introduce
            timeout: Time in seconds to timeout if the command fails
        Expected Return:
            N/A
        """
        self.status.verify_deployment_is_active("bootstrap node in")

        if not force and not self.config.artifact_manager_kits:
            raise error_utils.RIB338(self.config["name"])

        # Run preliminary type pair validation
        try:
            if introducer in self.client_personas and target in self.server_personas:
                raise error_utils.RIB339("client", introducer, "server", target)

            if introducer in self.server_personas and target in self.client_personas:
                raise error_utils.RIB339("server", introducer, "client", target)

        except error_utils.RIB339 as err:
            if force:
                logger.warning(err.msg)
            else:
                raise err from None

        # these functions raise an error if no nodes match the desired app state
        self.status.get_nodes_that_match_status(
            action="bootstrap via",
            personas=[introducer],
            race_status=[status_utils.RaceStatus.RUNNING],
            force=force,
        )
        self.status.get_nodes_that_match_status(
            action="bootstrap",
            personas=[target],
            app_status=[status_utils.AppStatus.NOT_INSTALLED],
            force=force,
        )

        if target in self.android_client_personas:
            platform = "android"
            node_type = "client"
        elif target in self.linux_client_personas:
            platform = "linux"
            node_type = "client"
        elif target in self.linux_server_personas:
            platform = "linux"
            node_type = "server"
        else:
            raise error_utils.RIB406(
                "Unknown Persona Bootstrap unsupported in 2.0.0"
            ) from None

        # try to infer architecture from node status
        nodePlatform, nodeArch = self.status.get_node_os_details(target)

        if not nodePlatform:
            nodePlatform = platform
        elif nodePlatform != platform:
            raise error_utils.RIB406(
                f"Detected platform {nodePlatform} differs from configured platform {platform}"
            )

        if not nodeArch:
            if architecture == "auto":
                raise error_utils.RIB406(
                    f"Unable to detect architecture for {target} automatically. Specify using --architecture"
                )
            nodeArch = architecture

        # Fix architecture name to canonical representation
        if nodeArch in ["x86_64", "x86", "amd64"]:
            nodeArch = "x86_64"
        elif nodeArch in ["arm64-v8a", "arm", "aarch64"]:
            nodeArch = "arm64-v8a"
        else:
            raise error_utils.RIB406(
                f"Unrecognized architecture for {target}: {nodeArch}"
            )

        if nodeArch != architecture and architecture != "auto":
            raise error_utils.RIB406(
                f"Detected architecture {nodeArch} differs from specified architecture {architecture}"
            )

        logger.info(
            f"Using architecture {nodePlatform}/{nodeArch} for bootstrapping target node {target}"
        )

        try:
            self.race_node_interface.prepare_to_bootstrap(
                introducer=introducer,
                target=target,
                platform=nodePlatform,
                architecture=nodeArch,
                node_type=node_type,
                passphrase=passphrase,
                bootstrapChannelId=bootstrapChannelId,
            )
        except Exception as error:
            logger.error(f"Unable to prepare bootstrap on {introducer}: {error}")
            raise error_utils.RIB406("Bootstrap failed") from None

        # Check status post bootstrap
        self.status.wait_for_nodes_to_match_status(
            action="bootstrap",
            personas=[target],
            app_status=[status_utils.AppStatus.RUNNING],
            race_status=[status_utils.RaceStatus.RUNNING],
            timeout=timeout,
        )

    ###
    # Get Deployment Status/Information Methods
    ###

    def get_etc_tar_name(self, persona: str, is_compressed: bool = True) -> str:
        """
        Purpose:
            construct the the etc file name based on deployment name and node info
        Args:
            persona: the persona of the node the tar is for
            is_compressed: whther or not the tar should be compressed
        Return:
            tar file name
        """
        name = f"{self.config['name']}_{persona}_etc.tar"
        if is_compressed:
            name = f"{name}.gz"
        return name

    def get_configs_tar_name(self, persona: str, is_compressed: bool = True) -> str:
        """
        Purpose:
            construct the the configs file name based on deployment name and node info
        Args:
            persona: the persona of the node the tar is for
            is_compressed: whther or not the tar should be compressed
        Return:
            tar file name
        """
        name = f"{self.config['name']}_{persona}_configs.tar"
        if is_compressed:
            name = f"{name}.gz"
        return name

    @abstractmethod
    def get_elasticsearch_hostname(self) -> List[str]:
        """
        Purpose:
            Get the hostname and port to access elasticsearch
        Expected Args:
            N/A
        Expected Return:
            elasticsearch hostname(s)
        """

    def get_range_name(self) -> Optional[str]:
        """
        Purpose:
            Get the range name associated with the deployment
        Args:
            N/A
        Return:
            range name
        """
        try:
            range_config_json = general_utils.load_file_into_memory(
                self.paths.files["race_config"], data_format="json"
            )
            return range_config_json["range"]["name"]
        except:
            return None

    ###
    # VoA methods
    ###

    def add_voa_rule(
        self, nodes: List[str], rule_action: str, **rule: voa_utils.VoaRule
    ) -> None:
        """
        Purpose:
            Add/update the VoA rule with the given Id
        Args:
            nodes: list of nodes on which action is to be invoked,
                or else all applicable nodes in the deployment
            rule_action: The specific voa action to perform (delay, drop, tamper, replay)

        Return:
            N/A
        """
        self.status.verify_deployment_is_active("add VoA rule to")

        # Get the nodes that are running
        running_nodes = self.status.get_nodes_that_match_status(
            action="add VoA rule on",
            personas=nodes,
            race_status=[
                status_utils.RaceStatus.RUNNING,
                status_utils.RaceStatus.NETWORK_MANAGER_NOT_READY,
            ],
        )

        failed_to_add = {}
        for node_name in running_nodes:
            try:
                self.race_node_interface.add_voa_rule(
                    node_name,
                    rule_action,
                    **rule,
                )
            except Exception as error:
                failed_to_add[node_name] = error

        if failed_to_add:
            raise error_utils.RIB412(action="add VoA rule on", reasons=failed_to_add)

    def apply_voa_config(
        self,
        nodes: List[str],
        voa_config_file: str,
    ) -> None:
        """
        Purpose:
            Apply a VoA config file
        Args:
            nodes: list of nodes on which action is to be invoked,
                or else all applicable nodes in the deployment
            voa_config_file: Path to file containing the VoA configuration

        Return:
            N/A
        """
        self.status.verify_deployment_is_active("apply VoA configuration to")

        voa_config = general_utils.load_file_into_memory(
            voa_config_file, data_format="json"
        )

        # Get the nodes that are running
        running_nodes = self.status.get_nodes_that_match_status(
            action="apply VoA configuration on",
            personas=nodes,
            race_status=[
                status_utils.RaceStatus.RUNNING,
                status_utils.RaceStatus.NETWORK_MANAGER_NOT_READY,
            ],
        )

        failed_to_apply = {}
        for node_name in running_nodes:
            try:
                self.race_node_interface.apply_voa_config(
                    node_name,
                    voa_config,
                )
            except Exception as error:
                failed_to_apply[node_name] = error

        if failed_to_apply:
            raise error_utils.RIB412(
                action="apply VoA configuration on", reasons=failed_to_apply
            )

    def delete_voa_rules(
        self,
        nodes: List[str],
        rule_id_list: List[str],
    ) -> None:
        """
        Purpose:
            Delete the VoA rule with the given Id
        Args:
            nodes: list of nodes on which action is to be invoked,
                or else all applicable nodes in the deployment
            rule_id_list: List of rule identifiers, or empty list if all rules
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("delete VoA rule(s) from")

        # Get the nodes that are running
        running_nodes = self.status.get_nodes_that_match_status(
            action="delete VoA rule(s) on",
            personas=nodes,
            race_status=[
                status_utils.RaceStatus.RUNNING,
                status_utils.RaceStatus.NETWORK_MANAGER_NOT_READY,
            ],
        )

        failed_to_delete = {}
        for node_name in running_nodes:
            try:
                self.race_node_interface.delete_voa_rules(node_name, rule_id_list)
            except Exception as error:
                failed_to_delete[node_name] = error

        if failed_to_delete:
            raise error_utils.RIB412(
                action="delete VoA rule(s) on", reasons=failed_to_delete
            )

    def voa_set_active_state(
        self,
        nodes: List[str],
        state: bool,
    ) -> None:
        """
        Purpose:
            Set the VoA state (active or not)
        Args:
            nodes: list of nodes on which action is to be invoked,
                or else all applicable nodes in the deployment
            state: the desired state
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("set VoA activation state for")

        # Get the nodes that are running
        running_nodes = self.status.get_nodes_that_match_status(
            action="set the VoA activation state on",
            personas=nodes,
            race_status=[
                status_utils.RaceStatus.RUNNING,
                status_utils.RaceStatus.NETWORK_MANAGER_NOT_READY,
            ],
        )

        failed_to_set = {}
        for node_name in running_nodes:
            try:
                self.race_node_interface.voa_set_active_state(node_name, state)
            except Exception as error:
                failed_to_set[node_name] = error

        if failed_to_set:
            raise error_utils.RIB412(
                action="set the VoA activation status on", reasons=failed_to_set
            )

    ###
    # Get App Status/Information Methods
    ###

    def get_recipient_sender_mapping(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        is_network_manager_bypass: bool = False,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Parse Sender/Recepient Lists/Dicts by taking in an specified
                sender/recipients, and understanding who can talk to who
        Args:
            sender: Node to act as sender (may or may not be set)
            recipient: Node to act as recipient (may or may not be set)
            is_network_manager_bypass: Allow connectivity between all nodes. Default is False
        Return:
            recipient_sender_mapping (Dict): Dict of senders and recipient pairs. Key
                is the recipient, and value is a list of senders
        Raises:
            error_utils.RIB321: No mapping found
        """

        # Create Objs for functionality
        senders: Dict[str, Any] = {}  # get senders and who they CAN send messages to
        recipient_sender_mapping: Dict[
            str, Any
        ] = {}  # get recipients and who they will receive from

        # Set Senders
        if sender:
            sender_keys = [sender]
        elif is_network_manager_bypass:
            # All Nodes can Send in network-manager-bypass
            sender_keys = self.personas
        else:
            # Only Clients can Send in non network-manager-bypass
            sender_keys = self.client_personas

        # Convert to Dict
        for sender_key in sender_keys:
            senders.setdefault(
                sender_key,
                self.get_available_recipients_by_sender(
                    sender_key, is_network_manager_bypass=is_network_manager_bypass
                ),
            )

        # Set Recipients
        if recipient:
            recipient_keys = [recipient]
        elif is_network_manager_bypass:
            # All Nodes can Receive in network-manager-bypass
            recipient_keys = self.personas
        else:
            # Only Clients can Receive in non network-manager-bypass
            recipient_keys = self.client_personas

        # Loop through Recipients and get who will send messages to them
        for recipient_key in recipient_keys:
            # Set Default for key (empty list)
            recipient_sender_mapping.setdefault(recipient_key, [])

            # Loop through senders and see who will send to the recipient
            for current_sender, sender_possible_recipients in senders.items():
                if recipient_key in sender_possible_recipients:
                    recipient_sender_mapping[recipient_key].append(current_sender)

            # Get rid of recipients with no senders
            if not recipient_sender_mapping[recipient_key]:
                del recipient_sender_mapping[recipient_key]

        # Verify that we found a sender/recipient (at least 1)
        if not recipient_sender_mapping:
            raise error_utils.RIB321()

        return recipient_sender_mapping

    def get_available_recipients_by_sender(
        self, sender: str, is_network_manager_bypass: bool = False
    ) -> List[str]:
        """
        Purpose:
            Get available recipients by a sender and mode
        Args:
            sender: Node to send the message from
            is_network_manager_bypass: Allow connectivity between all nodes. Default is False
        Return:
            available_recipients: List of available recipients
                for the specified sender
        Raises:
            N/A
        """

        # Get Available Nodes for Sending by Sender/Mode
        available_recipients = []
        if not sender:
            # Will be sending from all possible nodes, so depends on mode only
            if is_network_manager_bypass:
                available_recipients = self.personas
            else:
                available_recipients = self.client_personas
        elif "client" in sender:
            if is_network_manager_bypass:
                available_recipients = self.server_personas
            else:
                available_recipients = self.client_personas
        else:
            if is_network_manager_bypass:
                available_recipients = self.personas
            else:
                # Can't send from server when not in network-manager-bypass
                available_recipients = []

        # Make copy of recipients list before we modify it
        available_recipients = list(available_recipients)

        # Remove the sender from available recipients
        if sender in available_recipients:
            available_recipients.remove(sender)

        return available_recipients

    def validate_sender_recipient(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        is_network_manager_bypass: bool = False,
    ) -> None:
        """
        Purpose:
            Validate a sender and recipient for sending/recieving messages

            Feedback must be given about why a specified sender/recipient is invalid
        Args:
            sender: Node to send the message from
            recipient: Node to send the message to
            is_network_manager_bypass: Allow connectivity between all nodes. Default is False
        Return:
            N/A
        Raises:
            error_utils.RIB307: when sender/recipient is invalid
        """

        # Get Available Recipients for Sending by Sender/Mode
        available_nodes = self.get_available_recipients_by_sender(
            sender, is_network_manager_bypass=is_network_manager_bypass
        )

        # Get All Nodes for invalid node check
        all_nodes = self.personas

        # Check for Invalid Sender/Recipient
        error_reason = None
        if sender not in all_nodes:
            error_reason = "Sender is not a valid node"
        elif recipient not in all_nodes:
            error_reason = "Recipient is not a valid node"
        elif sender == recipient:
            error_reason = "Cannot send to self"
        elif recipient not in available_nodes:
            error_reason = ""

        if error_reason is not None:
            raise error_utils.RIB307(
                sender,
                recipient,
                available_nodes,
                is_network_manager_bypass,
                reason=error_reason,
            )

    ###
    # Message Sending/Receiving Methods
    ###

    def send_message(
        self,
        message_type: str,
        message_content: Optional[str] = None,
        message_period: Optional[int] = None,
        message_quantity: Optional[int] = None,
        message_size: Optional[int] = None,
        recipient: Optional[str] = None,
        sender: Optional[str] = None,
        test_id: str = "",
        network_manager_bypass_route: Optional[str] = "",
    ) -> Dict[str, Any]:
        """
        Purpose:
            Send a message between nodes in the deployment
        Args:
            message_type: Manual or Auto
            message_content: Content of message to be sent in manual mode
            message_period: Milliseconds to wait betwen sending messages in auto send mode
            message_quantity: Number of messages to send in auto send mode
            message_size: Size in bytes of message to auto generate in auto send mode
            recipient: Node to send the message to
            sender: Node to send the message from
            test_id: An identifier that will get passed and inserted into the message
            network_manager_bypass_route: Channel ID/Link ID/Connection ID to use for network-manager-bypass messaging
        Return:
            return the used recipient sender mapping, to enable proper verification of sent message receipt
        """
        self.status.verify_deployment_is_active("send messages in")

        is_network_manager_bypass = bool(network_manager_bypass_route)

        # Get the senders and recipients
        recipient_sender_mapping = self.get_recipient_sender_mapping(
            sender=sender,
            recipient=recipient,
            is_network_manager_bypass=is_network_manager_bypass,
        )

        # Validate all sender/recipient pairs before sending any messages
        requested_senders = set()
        for recipient, senders in recipient_sender_mapping.items():
            for sender in senders:
                self.validate_sender_recipient(
                    sender,
                    recipient,
                    is_network_manager_bypass=is_network_manager_bypass,
                )
                requested_senders.add(sender)

        can_send = self.status.get_nodes_that_match_status(
            action="send messages from",
            personas=requested_senders,
            race_status=[status_utils.RaceStatus.RUNNING],
        )
        # Prints out any receivers that aren't running (but won't fail)
        self.status.get_nodes_that_match_status(
            action="receive messages on",
            personas=recipient_sender_mapping.keys(),
            race_status=[status_utils.RaceStatus.RUNNING],
            require=Require.NONE,
        )

        # Loop through recipients and send messages
        failed_to_send = {}
        for recipient, senders in recipient_sender_mapping.items():
            for sender in senders:
                if sender not in can_send:
                    continue

                try:
                    if message_type == "manual":
                        if not message_content:
                            raise error_utils.RIB401(message_type, "message")

                        self.race_node_interface.send_manual_message(
                            sender=sender,
                            recipient=recipient,
                            message=message_content,
                            test_id=test_id,
                            network_manager_bypass_route=network_manager_bypass_route,
                        )
                    elif message_type == "auto":
                        if not message_size:
                            raise error_utils.RIB401(message_type, "message_size")
                        elif not message_quantity:
                            raise error_utils.RIB401(message_type, "message_quantity")
                        elif message_period is None:
                            raise error_utils.RIB401(message_type, "message_period")

                        self.race_node_interface.send_auto_message(
                            sender=sender,
                            recipient=recipient,
                            period=message_period,
                            quantity=message_quantity,
                            size=message_size,
                            test_id=test_id,
                            network_manager_bypass_route=network_manager_bypass_route,
                        )
                    else:
                        raise error_utils.RIB006(f"Cannot Send {message_type} Messages")
                except Exception as error:
                    failed_to_send[f"{sender} to {recipient}"] = error

        if failed_to_send:
            raise error_utils.RIB412(action="send message", reasons=failed_to_send)

        # returned so the next function can use recipient_sender_mapping
        return recipient_sender_mapping

    def send_plan(
        self,
        message_plan_file: str,
        start_time: int,
        network_manager_bypass_route: str = "",
        test_id: str = "",
    ) -> None:
        """
        Purpose:
            Send message plan to appropriate sender nodes in the deployment
        Args:
            message_plan_file: Path to file containing the test plan to send to nodes
            start_time: The time nodes will start sending messages, in milliseconds
            network_manager_bypass_route: Channel ID/Link ID/Connection ID to use for network-manager-bypass messaging
            test_id: An identifier that will get passed and inserted into the message
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("send message plan in")

        is_network_manager_bypass = bool(network_manager_bypass_route)

        plan = general_utils.load_file_into_memory(
            message_plan_file, data_format="json"
        )

        if logging.root.level < logging.INFO:
            click.echo("Test Plan:")
            click.echo(f"{plan}")

        requested_recipients = set()
        for sender, recipients in plan["messages"].items():
            for recipient, messages in recipients.items():
                if messages:
                    if logging.root.level < logging.DEBUG:
                        click.echo(
                            f"Validating ability to send messages from {sender} to {recipient}"
                        )
                    self.validate_sender_recipient(
                        sender,
                        recipient,
                        is_network_manager_bypass=is_network_manager_bypass,
                    )
                    requested_recipients.add(recipient)

        can_send = self.status.get_nodes_that_match_status(
            action="send messages from",
            personas=plan["messages"].keys(),
            race_status=[status_utils.RaceStatus.RUNNING],
        )
        # Prints out any receivers that aren't running (but won't fail)
        self.status.get_nodes_that_match_status(
            action="receive messages on",
            personas=requested_recipients,
            race_status=[status_utils.RaceStatus.RUNNING],
            require=Require.NONE,
        )

        # Loop through recipients and send messages
        failed_to_send = {}
        for sender, recipients in plan["messages"].items():
            if sender not in can_send:
                continue

            plan_for_sender = {
                "start-time": start_time,
                "test-id": test_id,
                "messages": recipients,
                "network-manager-bypass-route": network_manager_bypass_route or "",
            }

            if logging.root.level < logging.DEBUG:
                click.echo(f"Test Plan for {sender}:")
                click.echo(f"{plan_for_sender}")

            try:
                self.race_node_interface.send_message_plan(
                    sender=sender,
                    plan=plan_for_sender,
                )
            except Exception as error:
                failed_to_send[sender] = error

        if failed_to_send:
            raise error_utils.RIB412(action="send plan", reasons=failed_to_send)

    def open_network_manager_bypass_recv(
        self,
        recipient: str,
        sender: str,
        network_manager_bypass_route: Optional[str] = None,
    ) -> None:
        """
        Purpose:
            Open a temporary network-manager-bypass receive connection on the recipient node
        Args:
            recipient: Persona/node on which to open connection
            sender: Persona/node from which to receive
            network_manager_bypass_route: Channel ID/link ID for which to open a connection
        Return:
            N/A
        """
        self.status.verify_deployment_is_active(
            "open network-manager-bypass receive connection in"
        )

        can_open_recv = self.status.get_nodes_that_match_status(
            action="open network-manager-bypass receive connection",
            personas=[recipient],
            race_status=[
                status_utils.RaceStatus.RUNNING,
                status_utils.RaceStatus.NETWORK_MANAGER_NOT_READY,
            ],
        )

        for node_name in can_open_recv:
            self.race_node_interface.open_network_manager_bypass_recv(
                recipient=node_name,
                sender=sender,
                network_manager_bypass_route=network_manager_bypass_route,
            )

    ###
    # File Methods
    ###

    def create_directories(self) -> None:
        """
        Purpose:
            Create directories for the deployment
        Args:
            N/A
        Return:
            N/A
        """

        for dir in self.paths.dirs.values():
            os.makedirs(dir, exist_ok=True)

        for persona in self.personas:
            os.makedirs(os.path.join(self.paths.dirs["etc"], persona), exist_ok=True)

    def create_plugin_directories(self) -> None:
        """
        Purpose:
            Create directories necessary for the plugin artifacts in the deployment
        Args:
            N/A
        Return:
            N/A
        """
        # Make Base Dirs
        os.mkdir(self.paths.dirs["plugins"])
        os.mkdir(self.paths.dirs["distribution_artifacts"])

        for (
            platform,
            architecture,
            node_type,
        ) in self.paths.supported_platform_arch_node_type_combinations:
            # Make Platform/Node Type Dirs
            os.makedirs(
                self.paths.dirs[
                    self.paths.get_plugin_artifacts_base_dir_key(
                        platform, architecture, node_type
                    )
                ],
                exist_ok=True,
            )

            for ta in self.paths.tas:
                # Make TA Dirs
                os.makedirs(
                    self.paths.dirs[
                        self.paths.get_plugin_artifacts_ta_dir_key(
                            platform, architecture, node_type, ta
                        )
                    ],
                    exist_ok=True,
                )

    def update_metadata(self, new_metadata_values: Dict[str, Any]) -> None:
        """
        Purpose:
            Update the metadata of a deployment
        Args:
            new_metadata_values (Dict): Dict of metadata values to update
        Return:
            N/A
        Raises:
            Exception: When trying to set a metadata value that was not set previously
            Exception: Loading a file failes (corrupt configs)
            Exception: writing to file (issues with I/O)
        """

        # Load the existing metadata file into memory from stored file
        existing_metadata_values = general_utils.load_file_into_memory(
            self.paths.files["metadata"], data_format="json"
        )

        # Overwrite Each Value as passed in
        for metadata_key, new_metadata_value in new_metadata_values.items():
            if metadata_key not in existing_metadata_values:
                logger.warning(
                    f"Trying to set metadata key {metadata_key}, doesnt exist"
                )
            existing_metadata_values[metadata_key] = new_metadata_value

        # Persist to the stored metadata file
        general_utils.write_data_to_file(
            self.paths.files["metadata"],
            existing_metadata_values,
            data_format="json",
            overwrite=True,
        )

        if self.config.log_metadata_to_es:
            try:
                warnings.filterwarnings("ignore", category=ElasticsearchWarning)
                es = Elasticsearch(self.get_elasticsearch_hostname())
                esIndex = self.config.es_metadata_index
                elasticsearch_utils.log_deployment_metadata(
                    es, self.config["name"], new_metadata_values, esIndex
                )
            except Exception as err:
                logger.debug(
                    f"Failed to log deployment meta-data to elasticsearch: {err}"
                )

    @classmethod
    def update_configs(cls, file, new_config_values: Dict[str, Any]):
        """
        purpose:
            update configs of a deployment
        Args:
            new_config_value: dict of config values to update
            file: path to file to be updated
        return: N/A
        Raises:
            Exception: When trying to set a value that was not set previously
            Exception: Loading a file failes (corrupt configs)
            Exception: writing to file (issues with I/O)
        """

        # using file instead of self to allow change to be made
        # before the get_existing deployment call. ex see copy()
        existing_configs = general_utils.load_file_into_memory(file, data_format="json")

        # Overwrite Each Value as passed in
        for config_key, new_config_value in new_config_values.items():
            if config_key not in existing_configs:
                logger.warning(f"Trying to set config key {config_key}, doesnt exist")
            existing_configs[config_key] = new_config_value

        # Persist to the stored metadata file
        general_utils.write_data_to_file(
            file,
            existing_configs,
            data_format="json",
            overwrite=True,
        )

    def runtime_configs(
        self,
        config_group: str,
        config_key: str,
        config_value: str,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Purpose:
            Update runtime configs like Logging and OpenTracing
        Args:
            config_group: Config Group (i.e. Logging, OpenTracing, etc.)
            config_key: Key of config option in json file
            config_value: Value to update the config option to
        Return:
            N/A
        Raises:
            error_utils.RIB323: legacy configs that are incompatible
            Exception: Loading a file failes (corrupt configs)
            Exception: writing to file (issues with I/O)
            Exception: Key missing that we are trying to set
        """
        file = (
            f"{self.paths.dirs['global_configs']}/{self.paths.filenames[config_group]}"
        )

        # Deployments made before this functionality was implmented will not have
        # the config file
        if not os.path.isfile(file):
            raise error_utils.RIB323(
                self.config["name"], self.rib_mode, "update configs"
            )

        # Get the config file
        config = general_utils.load_file_into_memory(file, data_format="json")

        config_utils.check_valid_config_options(config_group, config_key, config_value)

        # This case should never happen if config_utils is maintained with config file changes
        if config_key not in config.keys():
            raise Exception(f"Trying to set config key {config_key}, doesnt exist")

        config[config_key] = config_value

        # Persist to Disk
        general_utils.write_data_to_file(
            file, config, data_format="json", overwrite=True
        )

    ###
    # Loader/Finder Methods
    ###

    @classmethod
    def get_active(
        cls, rib_mode: Optional[str]
    ) -> Dict[str, Union[Optional[str], Exception]]:
        """
        Purpose:
            Get the active deployments as a kev-value-pair where key is the deployment
            type and value is either the name of the active deployment, None if there is
            no active deployment, or an Exception if an error occurred while getting the
            active deployment. Optionally filter the type of deployment you want to
            check by passing the `rib_mode` argument.

        Args:
            rib_mode (Optional[str]): The deployment type to filter for, or None for all
            deployment types.

        Returns:
            Dict[str, Union[Optional[str], Exception]]: A dict where the keys are the
                deployment type and the value is either the name of the active
                deployment, None if there is no active deployment, or an Exception
                if an error occurred while getting the active deployment.
        """

        active_deployments = {}
        for deployment_type in general_utils.get_all_subclasses(RibDeployment):
            if not deployment_type.rib_mode:
                # If the deployment type's rib mode is None, it's an abstract class
                # and will not have active deployments
                continue

            if rib_mode and rib_mode != deployment_type.rib_mode:
                # Skipping modes that are not specified
                continue

            # Getting the active deployment if possible or reporting error
            try:
                active_deployment = deployment_type.get_active()
            except Exception as error:
                active_deployment = error

            active_deployments[deployment_type.rib_mode] = active_deployment

        return active_deployments

    @classmethod
    def remove_legacy_deployment(cls, name: str) -> None:
        """
        Purpose:
            Forcibly removes a legacy deployment created by an older version of RiB
        Args:
            name: Deployment name
        Return:
            N/A
        """

        deployment_dir = os.path.join(cls.pathsClass.dirs["mode"], name)
        if os.path.isdir(deployment_dir):
            shutil.rmtree(deployment_dir)

    @classmethod
    def deployment_exists(cls, name: str) -> bool:
        """
        Purpose:
            Checks if a deployment exists with the given name on disk. This does not attempt to load
            it, so it is possible that the deployment is not compatible with the current version of
            RiB.
        Args:
            name: Deployment name
        Return:
            True if a deployment exists with the given name
        """

        deployment_dir = os.path.join(cls.pathsClass.dirs["mode"], name)
        return os.path.isdir(deployment_dir)

    @classmethod
    def get_deployment(cls, name: str) -> "RibDeployment":
        """
        Purpose:
            Get a deployment if it exists
        Args:
            name: Name of the deployment
        Returns:
            deployment: Deployment Obj. will depend on the class that makes the call
        """

        if not name:
            raise Exception("No deployment name specified")

        config = cls.load_config(name)
        metadata = cls.load_metadata(name)
        return cls(config=config, metadata=metadata)

    @classmethod
    def get_defined_deployments(cls) -> DefinedDeployments:
        """
        Purpose:
            Get all deployments defined on the local machine
        Args:
            N/A
        Return
            Lists of compatible and incompatible deployments
        """

        compatible = set()
        incompatible = set()

        for name in os.listdir(cls.pathsClass.dirs["mode"]):
            if os.path.isdir(os.path.join(cls.pathsClass.dirs["mode"], name)):
                try:
                    cls.get_deployment(name)
                    compatible.add(name)
                except:
                    incompatible.add(
                        IncompatibleDeployment(
                            name=name,
                            rib_version=cls.get_compatible_rib_version_for(name),
                        )
                    )

        return DefinedDeployments(
            compatible=compatible,
            incompatible=incompatible,
        )

    @classmethod
    def get_compatible_rib_version_for(cls, name: str) -> str:
        """
        Purpose:
            Reads the deployment's config and metadata to determine
            what version of RiB is compatible with the deployment
        Args:
            name: Deployment name
        Return:
            Compatible RiB version
        """

        try:
            config = cls.load_config_json(name)
            if "rib_version" in config:
                return config["rib_version"]
        except:
            pass

        # Legacy deployments stored the RiB version in the metadata
        try:
            metadata = cls.load_metadata_json(name)
            if "rib_version" in metadata:
                return metadata["rib_version"]
        except:
            pass

        return "unknown"

    @classmethod
    def get_deployments(cls, ignore_invalid: bool = False) -> List[object]:
        """
        Purpose:
            Get all deployments for a specific mode
        Args:
            N/A
        Return:
            deployments: List of deployment objects
        """

        # Get all dirs in the deployment dir and try and load them
        possible_deployments = []
        for deployment_name in os.listdir(cls.pathsClass.dirs["mode"]):
            # Blacklist some directories
            if deployment_name in (".gitignore", ".DS_Store", "templates"):
                continue

            # Try to get the deployments, if a deployment throws and exception, ignore
            # it and continue building a list
            try:
                possible_deployments.append(cls.get_deployment(deployment_name))
            except Exception as err:
                # Check to see if invalid deployments are ignored
                if ignore_invalid:
                    continue
                raise err

        # Check to see if dirs are properly loaded
        deployments = [
            deployment
            for deployment in possible_deployments
            if deployment
            and isinstance(deployment, cls)  # Verify deployment is as expected
        ]

        return deployments

    @classmethod
    def load_config_json(cls, name: str) -> Dict[str, Any]:
        """
        Purpose:
            Load deployment config for the deployment. Config is loaded from the
            deployment config file that is saved with each deployment
        Args:
            name: Name of the deployment
        Return:
            config: Config of the deployment
        """

        # Check Deployment Config Files Exists
        config_file = (
            f"{cls.pathsClass.dirs['mode']}/{name}/{cls.pathsClass.filenames['config']}"
        )
        if not os.path.isfile(config_file):
            raise Exception("Deployment config file does not exist")

        return general_utils.load_file_into_memory(config_file, data_format="json")

    @classmethod
    def load_config(cls, name: str) -> BaseDeploymentConfig:
        """
        Purpose:
            Load deployment config for the deployment. Config is loaded from the
            deployment config file that is saved with each deployment
        Args:
            name: Name of the deployment
        Return:
            config: Config of the deployment
        """
        return cls.config_class.parse_obj(cls.load_config_json(name))

    @classmethod
    def load_metadata_json(cls, name: str) -> Dict[str, Any]:
        """
        Purpose:
            Load deployment metadata for the deployment. Metadata is loaded from the
            deployment metadata file that is saved with each deployment
        Args:
            name: Name of the deployment
        Return:
            metadata: Metadata for the deployment
        """

        # Check Deployment Metadata Files Exists
        metadata_file = f"{cls.pathsClass.dirs['mode']}/{name}/{cls.pathsClass.filenames['metadata']}"
        if not os.path.isfile(metadata_file):
            raise Exception("Deployment metadata file does not exist")

        return general_utils.load_file_into_memory(metadata_file, data_format="json")

    @classmethod
    def load_metadata(cls, name: str) -> DeploymentMetadata:
        """
        Purpose:
            Load deployment metadata for the deployment. Metadata is loaded from the
            deployment metadata file that is saved with each deployment
        Args:
            name: Name of the deployment
        Return:
            metadata: Metadata for the deployment
        """
        return DeploymentMetadata.parse_obj(cls.load_metadata_json(name))

    ###
    # Range Config Parsing Methods
    ###

    class RangeConfigPersonas(NamedTuple):
        """RACE node personas from a range config"""

        android_client_personas: Mapping[str, NodeConfig]
        linux_client_personas: Mapping[str, NodeConfig]
        linux_server_personas: Mapping[str, NodeConfig]

    ###
    # Generate/Load Config Methods
    ###

    @classmethod
    def generate_base_config(
        cls,
        name: str,
        rib_mode: str,
        # artifacts
        race_core: plugin_utils.KitSource,
        android_app: plugin_utils.KitConfig,
        linux_app: plugin_utils.KitConfig,
        registry_app: Optional[plugin_utils.KitConfig],
        node_daemon: plugin_utils.KitConfig,
        network_manager_kit: plugin_utils.KitConfig,
        channels_to_kits: Mapping[str, str],
        comms_kits: List[plugin_utils.KitConfig],
        artifact_manager_kits: List[plugin_utils.KitConfig],
        # images
        android_x86_64_client_image: Optional[str],
        android_arm64_v8a_client_image: Optional[str],
        linux_x86_64_client_image: Optional[str],
        linux_arm64_v8a_client_image: Optional[str],
        linux_x86_64_server_image: Optional[str],
        linux_arm64_v8a_server_image: Optional[str],
        registry_x86_64_client_image: Optional[str],
        registry_arm64_v8a_client_image: Optional[str],
        # range-config
        range_config: dict,
        disable_config_encryption: bool = False,
        disabled_channels: Optional[List[str]] = None,
    ) -> BaseDeploymentConfig:
        """
        Purpose:
            Create the base deployment configuration from the given common deployment creation
            parameters. Validation will be performed to ensure all required parameters have been
            specified and result in a valid deployment configuration.
        Args:
            name: Deployment name
            rib_mode: RiB deployment mode
            race_core: RACE core source
            android_app: Android client app config
            linux_app: Linux app config
            registry_app: Registry App config
            node_daemon: RACE Node Daemon config
            network_manager_kit: Network manager kit config
            channels_to_kits: Map of channel name to kit name
            comms_kits: Comms kit configs
            artifact_manager_kits: Artifact manager kit configs
            android_client_image: Android client Docker image
            linux_client_image: Linux client Docker image
            linux_server_image: Linux server Docker image
            range_config: Range-configuration
        """

        nodes = {}
        for race_node in range_config["range"]["RACE_nodes"]:
            nodes[race_node["name"]] = NodeConfig(
                platform=race_node["platform"],
                architecture=race_node.get("architecture", "x86_64"),
                node_type=race_node["type"],
                genesis=race_node.get("genesis", True),
                gpu=False,
                bridge=race_node.get("bridge", False),
            )

        images = []
        if android_x86_64_client_image:
            images.append(
                ImageConfig(
                    tag=android_x86_64_client_image,
                    platform="android",
                    architecture="x86_64",
                    node_type="client",
                )
            )
        if android_arm64_v8a_client_image:
            images.append(
                ImageConfig(
                    tag=android_arm64_v8a_client_image,
                    platform="android",
                    architecture="arm64-v8a",
                    node_type="client",
                )
            )
        if linux_x86_64_client_image:
            images.append(
                ImageConfig(
                    tag=linux_x86_64_client_image,
                    platform="linux",
                    architecture="x86_64",
                    node_type="client",
                )
            )
        if linux_arm64_v8a_client_image:
            images.append(
                ImageConfig(
                    tag=linux_arm64_v8a_client_image,
                    platform="linux",
                    architecture="arm64-v8a",
                    node_type="client",
                )
            )
        if linux_x86_64_server_image:
            images.append(
                ImageConfig(
                    tag=linux_x86_64_server_image,
                    platform="linux",
                    architecture="x86_64",
                    node_type="server",
                )
            )
        if linux_arm64_v8a_server_image:
            images.append(
                ImageConfig(
                    tag=linux_arm64_v8a_server_image,
                    platform="linux",
                    architecture="arm64-v8a",
                    node_type="server",
                )
            )
        if registry_x86_64_client_image:
            images.append(
                ImageConfig(
                    tag=registry_x86_64_client_image,
                    platform="linux",
                    architecture="x86_64",
                    node_type="registry",
                )
            )
        if registry_arm64_v8a_client_image:
            images.append(
                ImageConfig(
                    tag=registry_arm64_v8a_client_image,
                    platform="linux",
                    architecture="arm64-v8a",
                    node_type="registry",
                )
            )

        if not disabled_channels:
            disabled_channels = []
        comms_channels = [
            ChannelConfig(
                name=channel_name,
                kit_name=kit_name,
                enabled=channel_name not in disabled_channels,
            )
            for channel_name, kit_name in channels_to_kits.items()
        ]

        base_config = BaseDeploymentConfig(
            name=name,
            mode=rib_mode,
            rib_version=cls.rib_config.RIB_VERSION,
            race_core=race_core,
            android_app=android_app,
            linux_app=linux_app,
            registry_app=registry_app,
            node_daemon=node_daemon,
            network_manager_kit=network_manager_kit,
            comms_channels=comms_channels,
            comms_kits=comms_kits,
            artifact_manager_kits=artifact_manager_kits,
            nodes=nodes,
            images=images,
            race_encryption_type="ENC_NONE" if disable_config_encryption else "ENC_AES",
        )

        return base_config

    ###
    # Assertion Functions
    ###

    @classmethod
    def get_existing_deployment_or_fail(cls, name, rib_mode):
        """
        Purpose:
            Use name and mode to get existing deployment or fail
        Args:
            name (String): Name of the deployment
            rib_mode (String): RiB Mode of deployment
        Return:
            deployment (Deployment Obj): Obj representation of the deployment
        """

        rib_deployment_cls = cls.get_deployment_class(rib_mode)

        try:
            return rib_deployment_cls.get_deployment(name)
        except:
            try:
                available_deployments = rib_deployment_cls.get_deployments(
                    ignore_invalid=True
                )
            except Exception:
                # Failed to get available deployments, print that deployment doesn't
                # exist and move on
                raise error_utils.RIB302(name, []) from None

            if not available_deployments:
                raise error_utils.RIB300()

            raise error_utils.RIB302(name, available_deployments) from None

    @classmethod
    def ensure_deployment_not_existing_or_fail(cls, name, rib_mode):
        """
        Purpose:
            Use name and mode to get existing deployment, fail if it exists
        Args:
            name (String): Name of the deployment
            rib_mode (String): RiB Mode of deployment
        Return:
            N/A
        """

        rib_deployment_cls = cls.get_deployment_class(rib_mode)
        if rib_deployment_cls.deployment_exists(name):
            raise error_utils.RIB309(name, rib_mode) from None

    @classmethod
    def ensure_deployment_not_existing_or_remove(
        cls, name: str, rib_mode: str, force: bool
    ):
        """
        Purpose:
            Use name and mode to get potentially existing deployment, if it exists try to remove it
            force enabled or fail
        Args:
            name: Deployment name
            rib_mode: RiB deployment mode
            force: Whether to force removal of the deployment, if it exists
        Return:
            N/A
        """

        rib_deployment_cls = cls.get_deployment_class(rib_mode)
        if rib_deployment_cls.deployment_exists(name):
            if not force:
                raise error_utils.RIB309(name, rib_mode) from None

            logger.info(f"Removing Existing Deployment: {name} ({rib_mode})")

            # Try to load it
            deployment = None
            try:
                deployment = rib_deployment_cls.get_deployment(name)
            except:
                # It's a legacy deployment, remove by brute force.
                # TODO: shouldn't the force flag override this check?
                click.confirm(
                    (
                        f"This {rib_mode} Deployment was created with an older version of RiB. "
                        "Are you sure you want to forcibly remove it?"
                    ),
                    abort=True,
                )
                rib_deployment_cls.remove_legacy_deployment(name)

            if deployment:
                deployment.remove()

    ###
    # Reporting Functions
    ###

    @classmethod
    def print_active_deployments(cls, rib_mode: Optional[str]) -> None:
        """
        Purpose:
            Get and format print the active deployments.

            Note: AWS cannot print active deployments, blacklisting them for now, but
                we even need to think if its possible to ever get this data and what it
                means
        Args:
            rib_mode (Optional[str]): The deployment type, or None to print active
                deployments for all types.
        Returns:
            N/A
        """

        # Getting active deployments for each class
        active_deployments = cls.get_active(rib_mode)

        # Setting rib_mode Blacklist, aws does not work
        rib_mode_blacklist = ["aws"]

        if rib_mode:
            if rib_mode in rib_mode_blacklist:
                raise error_utils.RIB001(
                    f"Getting active deployment for {rib_mode} mode not yet supported"
                )
            print(active_deployments[rib_mode])
        else:
            # Inline function to format the name of a deployment.
            def format_name(name: str) -> str:
                if isinstance(name, Exception):
                    return "ERROR (see below)"
                return name if name else "no active deployment"

            # Print titles for columns.
            print("{:10s} {:s}".format("mode", "name"))

            # Print the deployment type and name in columns.
            for deployment_type, name in sorted(active_deployments.items()):
                if deployment_type in rib_mode_blacklist:
                    continue
                print("{:10s} {:s}".format(deployment_type, format_name(name)))

            # Print any errors.
            errors = [
                error
                for error in active_deployments.values()
                if isinstance(error, Exception)
            ]
            if errors:
                print(errors)

    ##
    # Plugin related functions
    ##
    @staticmethod
    def merge_fulfilled_requests(
        network_manager_request: List[dict], fulfilled_requests: List[List[dict]]
    ) -> List[dict]:
        """
        Purpose:
            given two fulfilled_requests.json, merge into one list
        Args:
            network_manager_request
            fulfilled_requests
        Returns:
            merged_list
        """
        # turn network_manager_request into {link_hash, link}
        network_manager_fulfilled_request_map = {}
        for link in network_manager_request:
            network_manager_fulfilled_request_map_key = (
                RibDeployment.link_hash_function(link)
            )
            link["channels"] = []  # clear out channels list
            network_manager_fulfilled_request_map[
                network_manager_fulfilled_request_map_key
            ] = link

        # loop through channels and add to
        for channel_fulfilled_request in fulfilled_requests:
            for link in channel_fulfilled_request:
                network_manager_fulfilled_request_map_key = (
                    RibDeployment.link_hash_function(link)
                )
                if len(link.get("channels")) > 0:
                    channel_name = link.get("channels")[0]
                    if (
                        network_manager_fulfilled_request_map_key
                        in network_manager_fulfilled_request_map
                    ):
                        network_manager_fulfilled_request_map[
                            network_manager_fulfilled_request_map_key
                        ].get("channels").append(channel_name)
                    else:
                        raise Exception(
                            "Comms config gen created a link that was not requested or modified identifying details of the link such as groupId, sender, or recipients"
                        )

        return list(network_manager_fulfilled_request_map.values())

    @staticmethod
    def link_hash_function(link: dict) -> str:
        """
        Purpose:
            Determine unique hash of a link. This function assumes no two links have the exact same
            sender and list of recipients. There can be multiple channels that create their own
            instantiation of a link, but the sender/recipient pairing is what defines the link.
        Args:
            link (dict): Dictionary of link specific fields
        Returns:
            link_hash (str): unique id for link
        """
        groupId = link.get("groupId")
        details = str(link.get("details"))
        sender = link.get("sender")
        recipients = link.get("recipients")
        recipients.sort()
        "-".join(recipients)
        return f"groupId-{groupId}-details-{details}-sender-{sender}-recipients-{recipients}"

    def create_user_responses(
        self, user_responses_by_plugin_id: Dict[str, Dict[str, Dict[str, str]]]
    ) -> None:
        """
        Purpose:
            Re-structures the node-specific user responses for each plugin into node-specific
            files with responses per plugin ID.

            Additionally, common (not plugin-specific) responses will be added for each node.

            For example, given the following input data:
            {
                "PluginId1": {
                    "race-node-00001": { "prompt-a": "response-x" },
                    "race-node-00002": { "prompt-a": "response-y" }
                },
                "PluginId2": {
                    "race-node-00001": { "prompt-b": "response-z" },
                    "race-node-00002": { "prompt-b": "response-z" }
                }
            }

            The following will be written to user-responses/race-node-00001.json:
            {
                "Common": { "key-a": "response-a" },
                "PluginId1": { "prompt-a": "response-x" },
                "PluginId2": { "prompt-b": "response-z" }
            }
            And the following will be written to user-responses/race-node-00002.json:
            {
                "Common": { "key-a": "response-b" },
                "PluginId1": { "prompt-a": "response-y" },
                "PluginId2": { "prompt-b": "response-z" }
            }
        Args:
            user_responses_by_plugin_id: Map of plugin IDs to maps of personas to maps of prompts to responses
        Return:
            N/A
        """

        user_responses_by_persona = {}

        for (
            pluginId,
            responses_by_persona,
        ) in user_responses_by_plugin_id.items():
            for persona, responses in responses_by_persona.items():
                user_responses_by_persona.setdefault(persona, {})
                user_responses_by_persona[persona][pluginId] = responses

        range_config = general_utils.load_file_into_memory(
            self.paths.files["race_config"], data_format="json"
        )

        for node in range_config["range"]["RACE_nodes"]:
            isUiEnabled = node.get("uiEnabled", False)
            persona = node["name"]
            user_responses = user_responses_by_persona.get(persona, {})
            user_responses["Common"] = {
                "hostname": persona,
                "env": node.get("environment", "any"),
            }

            # TODO: make this configurable? or do we not really care for test deployments?
            user_responses["sdk"] = {"passphrase": "race1234"}

            user_responses_file_name = "user-responses.json"
            if isUiEnabled:
                user_responses_file_name = "disabled-user-responses.json"

            general_utils.write_data_to_file(
                f"{self.paths.dirs['etc']}/{persona}/{user_responses_file_name}",
                user_responses,
                data_format="json",
                overwrite=True,
            )

    def get_app_for_node(self, persona: str):
        """
        Purpose:
            Determine which app the node should be running
        Args:
            persona (str): the node to get the app of
        Returns:
            app_to_run (str): which app to run (key in the deployment config)
        """
        app_to_run = "unknown"
        if self.config["nodes"][persona]["platform"] == "android":
            app_to_run = "android_app"
        elif self.config["nodes"][persona]["platform"] == "linux":
            if self.config["nodes"][persona]["node_type"] == "registry":
                app_to_run = "registry_app"
            else:
                app_to_run = "linux_app"
        return app_to_run

    def set_timezone(
        self,
        nodes: Optional[List[str]] = None,
        zone: Optional[str] = None,
        local_time: Optional[int] = None,
    ) -> None:
        """
        Purpose:
            Timezone change function, to be called from click
            local_time and zone are mutually exclusive input params
        Args:
            nodes: personas of nodes to be updated
            zone: name of wanted timezone
            local_time: local 0-24 hour time of wanted timezone
        Returns:
            NA
        """
        nodes = self.status.get_nodes_that_match_status(
            action="set-timezone",
            personas=nodes,
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            app_status=[
                status_utils.AppStatus.NOT_INSTALLED,
                status_utils.AppStatus.NOT_RUNNING,
            ],
        )

        # now is used later to calculate time change, if necessary
        now_utc = general_utils.get_current_utc_time()

        # need to calculate offset if given time
        if local_time:
            # now will use utc since rib is on utc
            offset = local_time - now_utc.hour

            # this is required to guarantee same return every single time the command is run
            sorted_zones = list(pytz.all_timezones_set)
            sorted_zones.sort()

            logger.info(f"New offset from utc is {offset} hours")
            utc_offset = timedelta(hours=offset, minutes=0)

            for tz in map(pytz.timezone, sorted_zones):
                # if/when a match is found,
                if now_utc.astimezone(tz).utcoffset() == utc_offset:
                    zone = tz.zone
                    logger.debug(f"{zone} will be written as new timezone")
                    break
            # offset wasn't found in timezone set
            if not zone:
                raise error_utils.RIB352()

        for node in nodes:
            self.race_node_interface.set_timezone(persona=node, specified_zone=zone)
        logger.info(
            f"New node(s) local time is {datetime.now(pytz.timezone(zone)).isoformat()}, {zone}"
        )

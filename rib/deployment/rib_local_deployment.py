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
        The RibLocalDeployment Class is a representation of RiB Deployments on
        a local machine
"""


# Python Library Imports
import click
import copy
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import subprocess

# Local Python Library Imports
import rib.deployment.rib_deployment_artifacts as deployment_artifacts
from rib.config import rib_host_env
from rib.deployment.paths.rib_local_deployment_paths import RibLocalDeploymentPaths
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.status.rib_deployment_status import Require
from rib.deployment.rib_deployment_config import (
    DeploymentMetadata,
    LocalDeploymentConfig,
)
from rib.deployment.status.rib_local_deployment_status import RibLocalDeploymentStatus
from rib.utils import (
    docker_utils,
    docker_compose_utils,
    error_utils,
    file_server_utils,
    general_utils,
    network_utils,
    plugin_utils,
    race_node_utils,
    range_config_utils,
    status_utils,
)


logger = logging.getLogger(__name__)


class RibLocalDeployment(RibDeployment):
    """
    Purpose:
        The RibLocalDeployment Class is a representation of RiB Deployments on
        a local machine
    """

    ###
    # Class Attributes
    ###

    pathsClass = RibLocalDeploymentPaths

    # Rib Information
    # TODO: can we change this name to something like `deployment_type`? Or even just
    #   `type`? The current name `rib_mode` isn't as descriptive and implies the
    #   setting is something global across RiB.
    rib_mode = "local"

    config_class = LocalDeploymentConfig

    ###
    # Instance attributes
    ###

    config: LocalDeploymentConfig

    ###
    # Lifecycle Methods
    ###

    def __init__(
        self, config: LocalDeploymentConfig, metadata: DeploymentMetadata
    ) -> None:
        """
        Purpose:
            Initialize the local deployment object.
        Args:
            config: Base deployment configuration
            metadata: Deployment metadata
        Returns:
            RibLocalDeployment (RibLocalDeployment Obj): Generated Object
        """
        # Call Parent Init
        super().__init__(config=config, metadata=metadata)

        self.paths = RibLocalDeploymentPaths(self.config["name"])

    def __repr__(self) -> str:
        """
        Purpose:
            Representation of the RibLocalDeployment object.
        Args:
            N/A
        Returns:
            RibLocalDeployment (String): String representation of RibLocalDeployment
        """

        return f"<RibLocalDeployment {self.config['name']}>"

    ###
    # Create Deployment Methods
    ###

    @classmethod
    def create(
        cls,
        create_command: str,
        deployment_name: str,
        # range-config
        range_config: Optional[str],
        no_config_gen: bool,
        disable_config_encryption: bool,
        race_log_level: Optional[str],
        # Artifacts
        race_core: plugin_utils.KitSource,
        android_app: plugin_utils.KitSource,
        linux_app: plugin_utils.KitSource,
        registry_app: Optional[plugin_utils.KitSource],
        node_daemon: plugin_utils.KitSource,
        network_manager_kit: plugin_utils.KitSource,
        comms_channels: List[str],
        comms_kits: List[plugin_utils.KitSource],
        artifact_manager_kits: List[plugin_utils.KitSource],
        # node counts
        android_client_count: int,
        linux_client_count: int,
        linux_server_count: int,
        race_node_arch: str,
        android_client_uninstalled_count: int = 0,
        linux_client_uninstalled_count: int = 0,
        linux_server_uninstalled_count: int = 0,
        android_client_bridge_count: int = 0,
        linux_client_bridge_count: int = 0,
        linux_server_bridge_count: int = 0,
        registry_client_count: int = 0,
        registry_client_uninstalled_count: int = 0,
        gpu_registry_client_count: int = 0,
        android_client_enable_ui_for: Optional[List[str]] = None,
        # images
        android_client_image: Optional[str] = None,
        linux_client_image: Optional[str] = None,
        linux_server_image: Optional[str] = None,
        registry_client_image: Optional[str] = None,
        # artifacts
        cache: plugin_utils.CacheStrategy = plugin_utils.CacheStrategy.AUTO,
        fetch_plugins_on_start: bool = False,
        disabled_channels: Optional[List[str]] = None,
        # Local Env
        enable_gpu: Optional[bool] = False,
        android_client_accel: bool = False,
        tmpfs_size: Optional[int] = None,
        disable_elasticsearch_volume_mounts: Optional[bool] = False,
        disable_open_tracing: Optional[bool] = False,
    ) -> None:
        """
        Purpose:
            Create a local deployment. This will include making directory structure,
            creating configs for stubs, creating AES keys, and creating image of network.

            Note: Init will initialize a deployment object. This can
            be loaded from a file or from command line args (or other means
            if testing). But a NEW deployment needs to be "created", in that
            its files, structure, etc need to be created and persisted
            on disk. This is the method to do so
        Args:
            name: Name of the deployment
            enable_gpu: Enable GPU device access for RACE nodes
            cache: Plugin caching strategy
            fetch_plugins_on_start: Enable fetching of plugins from artifact managers on application start
        Return:
            N/A
        """

        if range_config:
            range_config_json = general_utils.load_file_into_memory(
                range_config, data_format="json"
            )
        else:
            range_config_json = range_config_utils.create_local_range_config(
                name=deployment_name,
                android_client_count=android_client_count,
                android_client_arch=race_node_arch,
                android_client_uninstalled_count=android_client_uninstalled_count,
                android_client_bridge_count=android_client_bridge_count,
                android_ui_enabled_patterns=android_client_enable_ui_for,
                linux_client_count=linux_client_count,
                linux_client_arch=race_node_arch,
                linux_client_uninstalled_count=linux_client_uninstalled_count,
                linux_client_bridge_count=linux_client_bridge_count,
                linux_server_count=linux_server_count,
                linux_server_arch=race_node_arch,
                linux_server_uninstalled_count=linux_server_uninstalled_count,
                linux_server_bridge_count=linux_server_bridge_count,
                registry_client_count=registry_client_count,
                registry_client_arch=race_node_arch,
                registry_client_uninstalled_count=registry_client_uninstalled_count,
                gpu_registry_client_count=gpu_registry_client_count,
            )

        any_android = any(
            [
                x.get("platform") == "android"
                for x in range_config_json["range"]["RACE_nodes"]
            ]
        )

        kits = deployment_artifacts.download_deployment_kits(
            cache=cache,
            race_core=race_core,
            android_app=android_app if any_android else None,
            linux_app=linux_app,
            node_daemon=node_daemon,
            registry_app=registry_app,
            network_manager_kit=network_manager_kit,
            comms_channels=comms_channels,
            comms_kits=comms_kits,
            artifact_manager_kits=artifact_manager_kits,
        )

        base_config = RibLocalDeployment.generate_base_config(
            name=deployment_name,
            rib_mode=cls.rib_mode,
            # artifacts
            race_core=race_core,
            android_app=kits.android_app_config,
            linux_app=kits.linux_app_config,
            registry_app=kits.registry_app_config,
            node_daemon=kits.node_daemon_config,
            network_manager_kit=kits.network_manager_kit_config,
            channels_to_kits=kits.channels_to_kits,
            comms_kits=kits.comms_kits_config,
            artifact_manager_kits=kits.artifact_manager_kits_config,
            # images
            android_x86_64_client_image=android_client_image,
            android_arm64_v8a_client_image=android_client_image,
            linux_x86_64_client_image=linux_client_image,
            linux_arm64_v8a_client_image=linux_client_image,
            linux_x86_64_server_image=linux_server_image,
            linux_arm64_v8a_server_image=linux_server_image,
            registry_x86_64_client_image=registry_client_image,
            registry_arm64_v8a_client_image=registry_client_image,
            # range-config
            range_config=range_config_json,
            disable_config_encryption=disable_config_encryption,
            disabled_channels=disabled_channels,
        )

        # Parse config, create instance, and create
        deployment_config = LocalDeploymentConfig(
            **base_config.dict(),
            android_container_acceleration=android_client_accel,
            host_env_config=rib_host_env.get_rib_env_config(),
            tmpfs_size=tmpfs_size,
        )

        rib_instance_tag = os.environ.get("RIB_INSTANCE_TAG", "")
        rib_container_info = docker_utils.get_container_info(
            "race-in-the-box" + rib_instance_tag
        )
        deployment_metadata = DeploymentMetadata(
            rib_image=rib_container_info["image"],
            create_command=create_command,
            create_date=general_utils.get_current_time(),
            race_core_cache=kits.race_core_cache,
            android_app_cache=kits.android_app_cache,
            linux_app_cache=kits.linux_app_cache,
            registry_app_cache=kits.registry_app_cache,
            node_daemon_cache=kits.node_daemon_cache,
            network_manager_kit_cache=kits.network_manager_kit_cache,
            comms_kits_cache=kits.comms_kits_cache,
            artifact_manager_kits_cache=kits.artifact_manager_kits_cache,
        )
        # Create Instance of Deployment Object, then create deployment files/configs
        deployment = RibLocalDeployment(
            config=deployment_config,
            metadata=deployment_metadata,
        )

        try:
            # Prepare the Dir Structure
            deployment.create_directories()

            # Get Plugins
            deployment.get_plugins(
                cache=cache,
                race_core_cache=kits.race_core_cache,
                android_app_cache=kits.android_app_cache,
                linux_app_cache=kits.linux_app_cache,
                registry_app_cache=kits.registry_app_cache,
                node_daemon_cache=kits.node_daemon_cache,
                network_manager_kit_cache=kits.network_manager_kit_cache,
                comms_kits_cache=kits.comms_kits_cache,
                artifact_manager_kits_cache=kits.artifact_manager_kits_cache,
            )

            # Write deployment Config/Metadata to file
            general_utils.write_data_to_file(
                deployment.paths.files["config"],
                deployment.config.dict(),
                data_format="json",
                overwrite=True,
            )
            general_utils.write_data_to_file(
                deployment.paths.files["metadata"],
                deployment.metadata.dict(),
                data_format="json",
                overwrite=True,
            )

            if range_config:
                # Verify range config file exists
                shutil.copy(
                    range_config,
                    deployment.paths.files["race_config"],
                    follow_symlinks=True,
                )
            else:
                general_utils.write_data_to_file(
                    deployment.paths.files["race_config"],
                    range_config_json,
                    data_format="json",
                    overwrite=True,
                )

            # Error if there is no bootstrap comms channel but a bootstrap node is present
            comms_channel_info = deployment.get_deployment_channels_list()
            if (
                deployment.bootstrap_client_personas
                or deployment.linux_bootstrap_server_personas
            ):
                plugin_utils.verify_bootstrap_channel_present(comms_channel_info)

            # Build Docker Compose
            docker_compose_data = deployment.generate_docker_compose_data(
                enable_gpu=enable_gpu,
                mount_plugins=not fetch_plugins_on_start,
                disable_elasticsearch_volume_mounts=disable_elasticsearch_volume_mounts,
            )
            general_utils.write_data_to_file(
                deployment.paths.files["docker_compose"],
                docker_compose_data,
                data_format="yaml",
                overwrite=True,
            )

            # Copy dns proxy configs
            shutil.copytree(
                f"{deployment.paths.dirs['templates']}/../../common/templates/dnsproxy",
                deployment.paths.dirs["dnsproxy"],
                dirs_exist_ok=True,
            )

            # Copy VPN Configs
            shutil.copytree(
                f"{deployment.paths.dirs['templates']}/../../common/templates/vpn",
                deployment.paths.dirs["vpn"],
                dirs_exist_ok=True,
            )

            # Create Global Etc files (files for testing only)
            deployment.create_global_etc_files(
                disable_open_tracing=disable_open_tracing
            )

            # Create Configs/Data and Write Them
            deployment.create_global_configs_and_data(
                fetch_plugins_on_start=fetch_plugins_on_start,
                log_level=race_log_level,
            )

            if deployment.config.artifact_manager_kits:
                deployment.create_distribution_artifacts()

        except Exception as err:
            deployment.remove(force=True)
            raise err

        # Calling generate configs after deployment is created so that if there are errors when
        # generating configs, nothing is deleted and they can be fixed manually
        # Skipped if --no-config-gen is true
        if no_config_gen:
            logger.info("Skipping config gen...")
        else:
            try:
                deployment.generate_plugin_or_channel_configs()
            except Exception as err:
                # TODO: this isn't a question, and we do nothing with the response.
                click.confirm(
                    "Deployment created but config generation failed. Deployment will not run successfully.",
                )
                logger.warning(
                    f"Deployment created but config generation failed. Please manually verify or replace configs in {deployment.paths.dirs['race_configs']} or retry config generation with 'rib deployment {deployment.rib_mode} config generate --name={deployment.config['name']} -v --force' to get more debug information",
                )
                raise err

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
            kit_cache: Kit download cache metadata
        Expected Return:
            N/A
        """
        logger.debug(f"Copying kit {kit_name} from {kit_cache.cache_path}")

        self.copy_plugin_support_files_into_deployment(kit_name, kit_cache.cache_path)
        self.copy_plugin_artifacts_into_deployment(
            kit_name, kit_type, kit_cache.cache_path
        )

    def generate_docker_compose_data(
        self,
        enable_gpu: Optional[bool] = False,
        skip_nodes: bool = False,
        mount_plugins: bool = False,
        disable_elasticsearch_volume_mounts: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Based on the number of clients/servers, the specified versions for
            client/server, and other variable (none ATM), create a docker
            file (also from templates stored) in the same directory as this script
            to run a version of the RACE network.
        Args:
            enable_gpu: Enable GPU device access for RACE nodes
            skip_nodes: Omit RACE nodes from docker-compose configuration
            mount_plugins: Mount the network manager & comms plugin dirs into each node
            disable_elasticsearch_volume_mounts: Disable volume mounts for elasticsearch (Fixes deployments on hosts with permissions issues, the downside is trace data is ephemeral)
        Return:
            docker_compose_data (Dict): Dict representation of the resulting
                Docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        docker_compose_data = {
            "version": {},
            "x-logging": {},
            "networks": {},
            "services": {},
        }

        # Load Base Values
        docker_compose_data.update(
            general_utils.load_file_into_memory(
                f"{compose_template_dir}/version.yml", data_format="yaml"
            )
        )
        docker_compose_data.update(
            general_utils.load_file_into_memory(
                f"{compose_template_dir}/logging.yml", data_format="yaml"
            )
        )
        docker_compose_data.update(
            general_utils.load_file_into_memory(
                f"{compose_template_dir}/networks.yml", data_format="yaml"
            )
        )

        # Load Services
        service_depends_on = ""

        # Add Opentracing services
        service_template = f"{compose_template_dir}/open-tracing.yml"
        docker_compose_data["services"].update(
            general_utils.format_yaml_template(service_template)
        )
        # Remove Opentracing volume mounts if user requested
        if disable_elasticsearch_volume_mounts:
            # delete the elasticsearch volumes key
            del docker_compose_data["services"]["elasticsearch"]["volumes"]

        # Add OpenVPN services
        service_template = f"{compose_template_dir}/vpn.yml"
        docker_compose_data["services"].update(
            general_utils.format_yaml_template(service_template)
        )

        # Add orchestration services
        orchestration_service_template = (
            f"{compose_template_dir}/orchestration-services.yml"
        )
        docker_compose_data["services"].update(
            general_utils.format_yaml_template(orchestration_service_template)
        )

        # This is broken out sice GPU deployments do not use compose for nodes. This
        # Function is called by both local and localGpu deployments
        if not skip_nodes:
            self.generate_docker_compose_data_for_nodes(
                docker_compose_data=docker_compose_data,
                service_depends_on=service_depends_on,
                enable_gpu=enable_gpu,
                mount_plugins=mount_plugins,
            )

        return docker_compose_data

    def generate_docker_compose_data_for_nodes(
        self,
        docker_compose_data: Dict[str, Any],
        service_depends_on: str,
        enable_gpu: Optional[bool] = False,
        mount_plugins: bool = False,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Based on the number of clients/servers, the specified versions for
            client/server, and other variable (none ATM), create a docker
            file (also from templates stored) in the same directory as this script
            to run a version of the RACE network.

            Will generate node configs only
        Args:
            docker_compose_data: base compose data to append to
            service_depends_on: a string if the nodes depend on other services
            enable_gpu: Enable GPU device access for RACE nodes
            mount_plugins: Mount the network manager & comms plugin dirs into each node
        Return:
            N/A (The docker_compose_data is edited by reference)
        """

        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Set Override command, as older versions of RiB need this
        tmpfs_mount = ""
        if self.config["tmpfs_size"]:
            tmpfs_mount = general_utils.load_file_into_memory(
                f"{compose_template_dir}/tmpfs.yml", data_format="string"
            ).format(tmpfs_size_bytes=self.config["tmpfs_size"])

        # Global Node Configs
        global_node_configs = {
            "api_socket_internal": self.ports["race_api_port"],
            "service_depends_on": service_depends_on,
            "tmpfs_mount": tmpfs_mount,
            "override_env_variables": "",
            "override_port_mappings": "",
            "override_vars": "",
        }

        if enable_gpu:
            gpu_capability = general_utils.load_file_into_memory(
                f"{compose_template_dir}/gpu-capability.yml", data_format="yaml"
            )

        # fmt: off
        linux_node_service_template = f"{compose_template_dir}/linux-node.yml"
        for server_name in self.linux_server_personas:
            server_details = self.config["nodes"][server_name]
            architecture = server_details["architecture"]

            # Do not create compose for bridge nodes
            if server_details["bridge"]:
                continue

            # Needs to be quoted so YAML doesn't turn it into a boolean
            uninstall = '"no"' if server_details["genesis"] else '"yes"'

            node_config = copy.deepcopy(global_node_configs)


            node_config.update(
                {
                    "node_name": server_name,
                    "node_type": "server",
                    "image": self.linux_x86_64_server_image if architecture == "x86_64" else self.linux_arm64_v8a_server_image,
                    "uninstall_race": uninstall,
                    "optional_depends_on": "",  # No depends_on for linux servers
                    "race_encryption_type": self.config["race_encryption_type"],
                    # "memory_limit": self.run_info.get("resource_limits", {}).get("memory_limit_per_node", "512M"),
                    # "cpu_limit": self.run_info.get("resource_limits", {}).get("cpu_limit_per_node", "0.5"),
                }
            )

            node_service = general_utils.format_yaml_template(
                linux_node_service_template, node_config
            )

            if server_details["genesis"]:
                node_service[server_name]["volumes"].extend([
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-server/artifact-manager/:/usr/local/lib/race/artifact-manager",
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-server/core:/usr/local/lib/race/core",
                ])
                if mount_plugins:
                    node_service[server_name]["volumes"].extend([
                        f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-server/network-manager/:/usr/local/lib/race/network-manager",
                        f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-server/comms/:/usr/local/lib/race/comms",
                    ])
            else:
                node_service[server_name]["volumes"].extend([
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-server/core/race-daemon:/usr/local/lib/race/core/race-daemon",
                ])

            if enable_gpu:
                node_service[server_name].update(copy.deepcopy(gpu_capability))
                # Temporary fix for CUDA issue in base image (see RACE2-2146 for more info)
                node_service[server_name]["environment"]["LD_LIBRARY_PATH"] =\
                    "/usr/local/lib/:/usr/lib/jvm/java-1.8.0-openjdk-amd64/jre/lib/amd64/server/"

            docker_compose_data["services"].update(node_service)

        # If acceleration is enabled, give containers access to the /dev/kvm device so the
        # Android emulators can take advantage of qemu hardware acceleration
        devices = 'devices:\n    - "/dev/kvm:/dev/kvm"' if self.config["android_container_acceleration"] else ""
        # Needs to be quoted so YAML doesn't turn it into a boolean
        hw_accel = '"on"' if self.config["android_container_acceleration"] else '"off"'
        container_vnc_port = self.ports['vnc_port']

        # Creating a map for depends_on chaining clients so that the android
        # clients start up staggared. Setting to 3 at a time based on some
        # testing before 1.4.0 release. we may be able to start out more at
        # the same time, but this seems to be a good start. of note, depends
        # on will not wait for the container to be fully healthy, so this
        # does not mean only 3 containers are booting at a time
        depends_on_map: Dict[int, Optional[str]] = {}
        depends_on_modulo = 3
        for idx in range(depends_on_modulo):
            depends_on_map.setdefault(idx, None)

        client_id = 0
        for client_name in self.android_client_personas:
            client_details = self.config["nodes"][client_name]
            architecture = client_details["architecture"]
            client_id += 1

            # Do not create compose for bridge nodes
            if client_details["bridge"]:
                continue

            # Needs to be quoted so YAML doesn't turn it into a boolean
            uninstall = '"no"' if client_details["genesis"] else '"yes"'

            node_config = copy.deepcopy(global_node_configs)

            # Use modulo logic to chain client 1->4->7, client 2->5->8, etc
            # clients 1,2,3 have no depends on
            depends_on_idx = client_id % depends_on_modulo
            if not depends_on_map.get(depends_on_idx, None):
                depends_on_map[depends_on_idx] = client_name
                depends_on = ""
            else:
                depends_on = "depends_on:\n    - " + depends_on_map[depends_on_idx]
                depends_on_map[depends_on_idx] = client_name

            host_vnc_port = self.ports["client_start_port_vnc"] + client_id
            node_config.update(
                {
                    "node_name": client_name,
                    "node_type": "client",
                    "uninstall_race": uninstall,
                    "override_env_variables": f"HW_ACCEL: {hw_accel}",
                    "override_port_mappings": f'ports:\n    - "{host_vnc_port}:{container_vnc_port}"',
                    "optional_depends_on": depends_on,
                    "override_vars": devices,
                    "image": self.android_x86_64_client_image if architecture == "x86_64" else self.android_arm64_v8a_client_image,
                    "race_encryption_type": self.config["race_encryption_type"],
                    # "memory_limit": self.run_info.get("resource_limits", {}).get("memory_limit_per_node", "512M"),
                    # "cpu_limit": self.run_info.get("resource_limits", {}).get("cpu_limit_per_node", "0.5"),
                }
            )

            node_service = general_utils.format_yaml_template(
                linux_node_service_template, node_config
            )

            if client_details["genesis"]:
                node_service[client_name]["volumes"].extend([
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/android-{architecture}-client/artifact-manager/:/android/{architecture}/lib/race/artifact-manager",
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/android-{architecture}-client/core:/android/{architecture}/lib/race/core",
                ])
                if mount_plugins:
                    node_service[client_name]["volumes"].extend([
                        f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/android-{architecture}-client/network-manager/:/android/{architecture}/lib/race/network-manager",
                        f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/android-{architecture}-client/comms/:/android/{architecture}/lib/race/comms",
                    ])
            else:
                node_service[client_name]["volumes"].extend([
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/android-{architecture}-client/core/race-daemon:/android/{architecture}/lib/race/core/race-daemon",
                ])

            if enable_gpu:
                node_service[client_name].update(copy.deepcopy(gpu_capability))
                # Temporary fix for CUDA issue in base image (see RACE2-2146 for more info)
                node_service[client_name]["environment"]["LD_LIBRARY_PATH"] =\
                    "/usr/local/lib/:/usr/lib/jvm/java-1.8.0-openjdk-amd64/jre/lib/amd64/server/"

            docker_compose_data["services"].update(node_service)

        # Registries have the same artifacts as clients
        for client_name in self.linux_client_personas + self.registry_personas:
            client_details = self.config["nodes"][client_name]
            architecture = client_details["architecture"]
            
            # Do not create compose for bridge nodes
            if client_details["bridge"]:
                continue

            # Needs to be quoted so YAML doesn't turn it into a boolean
            uninstall = '"no"' if client_details["genesis"] else '"yes"'

            node_config = copy.deepcopy(global_node_configs)

            node_config.update(
                {
                    "node_name": client_name,
                    "node_type": "client",
                    "image": self.linux_x86_64_client_image if architecture == "x86_64" else self.linux_arm64_v8a_client_image,
                    "uninstall_race": uninstall,
                    "optional_depends_on": "",  # No depends_on for linux clients
                    "race_encryption_type": self.config["race_encryption_type"],
                    # "memory_limit": self.run_info.get("resource_limits", {}).get("memory_limit_per_node", "512M"),
                    # "cpu_limit": self.run_info.get("resource_limits", {}).get("cpu_limit_per_node", "0.5"),
                }
            )

            node_service = general_utils.format_yaml_template(
                linux_node_service_template, node_config
            )


            if client_details["genesis"]:
                node_service[client_name]["volumes"].extend([
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-client/artifact-manager/:/usr/local/lib/race/artifact-manager",
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-client/core:/usr/local/lib/race/core",
                ])
                if mount_plugins:
                    node_service[client_name]["volumes"].extend([
                        f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-client/network-manager/:/usr/local/lib/race/network-manager",
                        f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-client/comms/:/usr/local/lib/race/comms",
                    ])
            else:
                node_service[client_name]["volumes"].extend([
                    f"${{HOST_RIB_STATE_PATH}}/deployments/local/${{DEPLOYMENT_NAME}}/plugins/linux-{architecture}-client/core/race-daemon:/usr/local/lib/race/core/race-daemon",
                ])
            
            if enable_gpu:
                node_service[client_name].update(copy.deepcopy(gpu_capability))
                # Temporary fix for CUDA issue in base image (see RACE2-2146 for more info)
                node_service[client_name]["environment"]["LD_LIBRARY_PATH"] =\
                    "/usr/local/lib/:/usr/lib/jvm/java-1.8.0-openjdk-amd64/jre/lib/amd64/server/"

            docker_compose_data["services"].update(node_service)
        # fmt: on

    def generate_plugin_or_channel_configs(
        self,
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
            Handle interation between network manager and comms config generation
        Args:
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

        # Set Default val if None
        comms_custom_args_map = (
            [] if comms_custom_args_map is None else comms_custom_args_map
        )

        self._generate_plugin_or_channel_configs(
            force=force,
            local=True,
            network_manager_custom_args=network_manager_custom_args,
            comms_custom_args_map=comms_custom_args_map,
            artifact_manager_custom_args_map=artifact_manager_custom_args_map,
            timeout=timeout,
            max_iterations=max_iterations,
            skip_config_tar=skip_config_tar,
        )

    def create_directories(self) -> None:
        """
        Purpose:
            Create directories for the deployment
        Args:
            N/A
        Return:
            N/A
        """
        super().create_directories()

        # Make Elasticsearch Dirs and set permissions
        # elasticsearch runs with uid 1000 inside container
        # chmod to allow ES use directory as necessary
        if "elasticsearch" in self.paths.dirs:
            os.chmod(self.paths.dirs["elasticsearch"], 0o777)

    ###
    # Setup/Teardown Deployment Methods
    ###

    def _generate_docker_compose_env_vars(self) -> None:
        """
        Purpose:
            Generate a set of enviroment variables for use by docker-compose up.
        """

        return {
            "HOST_RIB_STATE_PATH": self.rib_config.HOST_RIB_STATE_PATH,
            "DEPLOYMENT_NAME": self.config["name"],
        }

    def up(
        self,
        last_up_command: str = None,
        force: bool = False,
        nodes: Optional[List[str]] = None,
        no_publish: bool = False,
        timeout: int = 300,
        verbose: int = 0,
    ) -> None:
        """
        Purpose:
            Setup and Stage a Local deployment.

            This will docker-compose up applicable containers for the deployment, volume
            mount all necessary paths (specified by the user or deployment configs),
            and the Flask API for communicating with nodes is running
            and expecting requests.

            This does NOT start the RACE app on the nodes.
        Args:
            last_up_command: The command (CLI) that upped the deployment
            force: Whether or not to force the operation
            nodes: Optional list of nodes to be stood up, or else all applicable nodes in
                the deployment
            no_publish: If True, configs will not be published after upping
            timeout: Time in seconds to timeout if the command fails
            verbose: set level of verbosity
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("stand up", none_ok=True)

        # If no nodes specified, stand up all RACE nodes
        nodes_to_up = nodes or self.managed_personas

        # Get the containers that can be stood up
        can_be_upped = self.status.get_containers_that_match_status(
            action="stand up",
            names=nodes_to_up,
            container_status=[
                status_utils.ContainerStatus.EXITED,
                status_utils.ContainerStatus.NOT_PRESENT,
            ],
            force=force,
            verbosity=verbose,
        )

        # Check if this is first call to stand up any container
        first_call_to_up = not self.status.get_containers_that_match_status(
            action="",
            names=self.managed_personas,
            container_status=[status_utils.ContainerStatus.RUNNING],
            require=Require.NONE,
            quiet=True,
        )

        # Start external services if first up
        # Starting before nodes to give time for services to start before using
        # them
        if first_call_to_up:
            logger.info("Starting deployment services")
            can_be_upped.update(self.aux_services)
            self.call_external_services_script(action="Start", verbose=verbose)

        # Verify that global configs are valid
        global_config_dir = self.paths.dirs.get("global_configs")
        self.validate_global_configs(
            global_config_dir,
            require_global_config_plugins=False,
        )

        # Build Env to Pass Subprocess
        env = self._generate_docker_compose_env_vars()
        env.update(dict(os.environ))  # Make a copy of the current environment

        docker_compose_utils.run_docker_compose_up(
            self.config["name"],
            self.config["mode"],
            self.paths.files["docker_compose"],
            env=env,
            services=can_be_upped,
            timeout=timeout,
            verbosity=verbose,
        )

        # Check status post up
        self.status.wait_for_containers_to_match_status(
            action="stand up",
            names=can_be_upped,
            container_status=[status_utils.ContainerStatus.RUNNING],
            timeout=timeout,
        )
        self.status.wait_for_nodes_to_match_status(
            action="stand up",
            personas=can_be_upped - set(self.aux_services),
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            timeout=timeout,
        )
        if first_call_to_up:
            self.status.wait_for_services_to_match_status(
                action="stand up",
                parent_status=[status_utils.ParentStatus.ALL_RUNNING],
                timeout=timeout,
            )

        # Set Daemon Config
        for node_name in nodes_to_up:
            executable_to_run = ""
            if node_name in self.linux_personas:
                app_manifest = general_utils.load_file_into_memory(
                    f'{self.paths.dirs["plugins"]}/{self.config[self.get_app_for_node(node_name)].name}/app-manifest.json',
                    "json",
                )
                executable_to_run = app_manifest["executable"]
            self.race_node_interface.set_daemon_config(
                deployment_name=self.config["name"],
                persona=node_name,
                genesis=self.config["nodes"][node_name]["genesis"],
                app=executable_to_run,
            )

        # Upload the RACE configs to the file server.
        if not no_publish:
            require = Require.ANY if first_call_to_up else Require.NONE
            self.upload_configs(nodes=nodes, timeout=timeout, require=require)

            # Call the node daemon to trigger a pull of the configs from the file server.
            # Only call nodes that have been up'd with this call.
            nodes_with_configs_pushed = self.status.get_nodes_that_match_status(
                action="pull configs",
                personas=nodes_to_up,
                configs_status=[status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED],
                force=force,
                verbosity=verbose,
            )
            for node_name in nodes_to_up:
                pull_etc_only = (
                    False if node_name in nodes_with_configs_pushed else True
                )
                self.race_node_interface.pull_configs(
                    deployment_name=self.config["name"],
                    persona=node_name,
                    etc_only=pull_etc_only,
                )
            self.status.wait_for_nodes_to_match_status(
                action="pull configs",
                personas=nodes_to_up,
                app_status=[
                    status_utils.AppStatus.NOT_RUNNING,
                    status_utils.AppStatus.NOT_INSTALLED,
                ],
                # Only checking Etc, not Configs but configs are pulled after etc so
                # this should be ok. We can split this into a check for genesis nodes and then
                # non-genesis nodes in the future
                etc_status=[status_utils.EtcStatus.READY],
                timeout=timeout,
            )

        # Update Config
        self.update_metadata(
            {
                "last_up_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
                "last_up_command": last_up_command,
            }
        )

    def down(
        self,
        last_down_command: Optional[str] = None,
        force: bool = False,
        nodes: Optional[List[str]] = None,
        timeout: int = 300,
        verbose: int = 0,
    ) -> None:
        """
        Purpose:
            Teardown and Clean a Local deployment.

            This will takedown any containers running for the
            deployment, and the API will no longer be running for communicating with
            the nodes.

            This does NOT stop the RACE app on the nodes.
        Args:
            last_down_command: The command (CLI) that downed the deployment
            force: Whether or not to force the operation
            nodes: Optional list of nodes to be torn down, or else all applicable nodes in
                the deployment
            timeout: Time in seconds to timeout if the command fails
            verbose: Enable verbose output
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("tear down", none_ok=force)

        # If no nodes specified, tear down all RACE nodes
        nodes_to_down = nodes or self.managed_personas

        # Get the containers that can be torn down
        can_be_downed = self.status.get_nodes_that_match_status(
            action="tear down",
            personas=nodes_to_down,
            app_status=[
                status_utils.AppStatus.NOT_REPORTING,
                status_utils.AppStatus.NOT_INSTALLED,
                status_utils.AppStatus.NOT_RUNNING,
            ],
            force=force,
            verbosity=verbose,
        )
        can_be_downed = self.status.get_containers_that_match_status(
            action="tear down",
            names=can_be_downed,
            container_status=[
                status_utils.ContainerStatus.EXITED,
                status_utils.ContainerStatus.STARTING,
                status_utils.ContainerStatus.RUNNING,
                status_utils.ContainerStatus.UNHEALTHY,
            ],
            force=force,
            verbosity=verbose,
        )
        already_down = self.status.get_containers_that_match_status(
            action="",
            names=self.managed_personas,
            container_status=[status_utils.ContainerStatus.NOT_PRESENT],
            require=Require.NONE,
            quiet=True,
        )

        # Build Env to Pass Subprocess
        env = self._generate_docker_compose_env_vars()
        env.update(dict(os.environ))  # Make a copy of the current environment

        # If this includes the last RACE node to be torn down, stop all services
        last_call_to_down = can_be_downed.union(already_down) == set(
            self.managed_personas
        )

        if last_call_to_down:
            # Make sure no bridged nodes are still running (if there are any)
            if self.bridge_personas:
                self.status.get_nodes_that_match_status(
                    action="tear down",
                    personas=self.bridge_personas,
                    daemon_status=[status_utils.DaemonStatus.NOT_REPORTING],
                    force=force,
                    require=Require.ALL,
                    quiet=True,
                )
            logger.info("Stopping deployment services")
            can_be_downed.update(self.aux_services)

        docker_compose_utils.run_docker_compose_stop(
            self.config["name"],
            self.paths.files["docker_compose"],
            env=env,
            services=can_be_downed,
            timeout=timeout,
            verbosity=verbose,
        )
        docker_compose_utils.run_docker_compose_remove(
            self.config["name"],
            self.paths.files["docker_compose"],
            env=env,
            services=can_be_downed,
            timeout=timeout,
            verbosity=verbose,
        )

        # Check status post down
        self.status.wait_for_containers_to_match_status(
            action="tear down",
            names=can_be_downed,
            container_status=[status_utils.ContainerStatus.NOT_PRESENT],
            timeout=timeout,
        )
        self.status.wait_for_nodes_to_match_status(
            action="tear down",
            personas=can_be_downed - set(self.aux_services),
            daemon_status=[status_utils.DaemonStatus.NOT_REPORTING],
            timeout=timeout,
        )

        if last_call_to_down:
            # if we're taking everything down, down external services
            self.call_external_services_script(action="Stop", verbose=verbose)
            self.status.wait_for_services_to_match_status(
                action="tear down",
                parent_status=[status_utils.ParentStatus.ALL_DOWN],
                timeout=timeout,
            )

        # Update Info In in deployment config
        self.update_metadata(
            {
                "last_down_command": last_down_command,
                "last_down_time": datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
            }
        )

    ###
    # Remote Interface Methods
    ###

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
        return race_node_utils.RaceNodeInterface()

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
        return file_server_utils.FileServerClient()

    def get_vpn_ip_address(self) -> str:
        """
        Purpose:
            Get the IP address of the VPN server to be configured in bridged nodes
        Args:
            N/A
        Return:
            VPN server IP address
        """
        return network_utils.get_lan_ip()

    ###
    # Setup/Teardown App Methods
    ###

    def get_external_service_script_paths(self, script_name: str) -> Dict[str, str]:
        """
        Purpose:
            Get the paths for all external service scripts of a given name
            Excludes the paths of any channels that do not have all required scripts
        Args:
            script_name: the name of the script to find
        Return:
            Dict[channel_name (str), script_path (str)]
        """
        scripts = {}
        for channel in self.config.comms_channels:
            if channel.name in self._external_services:
                external_services_script = (
                    f"{self._external_services[channel.name]}/{script_name}"
                )
                scripts["Comms (" + channel.name + ")"] = external_services_script

        for kit in self.config.artifact_manager_kits:
            if kit.name in self._external_services:
                external_services_script = (
                    f"{self._external_services[kit.name]}/{script_name}"
                )
                scripts[f"ArtifactManager ({kit.name})"] = external_services_script
        return scripts

    def call_external_services_script(self, action: str, verbose: int = 0) -> None:
        """
        Purpose:
            Call <action>_external_services script for all channels
        Args:
            action (str): defines the action script to call (<action>_external_services.sh)
            verbose (int): level of verbosity for output
        Return:
            N/A
        """
        capture_output = True
        if verbose > 0:
            capture_output = False

        script_to_call = f"{action.lower()}_external_services.sh"
        scripts = self.get_external_service_script_paths(script_to_call)

        for channel in scripts:
            print(f"{channel} {action} External Services")
            if os.path.exists(scripts[channel]):
                cmd = ["bash", scripts[channel]]
                cmd_as_str = " ".join(cmd)
                if verbose > 0:
                    print(f"{action} External Services Command: {cmd_as_str}")
                try:
                    subprocess.run(cmd, check=True, capture_output=capture_output)
                except subprocess.CalledProcessError as err:
                    logger.error(
                        f"Error occurred while calling {cmd_as_str} : {str(err)}"
                    )
                    raise err  # TODO: use RiB exception instead?
            elif verbose > 0:
                logger.warning(
                    f"Warning: no external services script found at {scripts[channel]}. Please check if this channel/plugin requires external services."
                )

    ###
    # Get Deployment Status/Information Methods
    ###

    def get_status(self):
        """Get the Status Object for the deployment"""
        return RibLocalDeploymentStatus(self)

    def get_elasticsearch_hostname(self) -> List[str]:
        """
        Purpose:
            Get the hostname and port to access elasticsearch
        Expected Args:
            N/A
        Expected Return:
            elasticsearch hostname(s)
        """
        return ["elasticsearch:9200"]

    ###
    # Config Methods
    ###

    @classmethod
    def get_active(cls) -> Optional[str]:
        """Get the name of the active deployment, or None if no deployment is active.

        Returns:
            Optional[str]: The name of the active deployment, or None if no deployment is active.
        """

        all_containers = docker_utils.get_all_container_names()

        active_deployments = set()
        for container_name in all_containers:
            deployment_name = docker_utils.get_container_label(
                container_name, cls.DEPLOYMENT_NAME_CONTAINER_LABEL_KEY
            )
            deployment_type = docker_utils.get_container_label(
                container_name, cls.DEPLOYMENT_TYPE_CONTAINER_LABEL_KEY
            )

            # Continue if deployment does not have name/type. External
            # services will not have labels
            if not deployment_name or not deployment_type:
                continue

            elif deployment_type == "local":
                active_deployments.add(deployment_name)

        active_deployments.discard(None)

        if len(active_deployments) > 1:
            raise error_utils.RIB324(active_deployments, cls.rib_mode)

        return active_deployments.pop() if active_deployments else None

    ###
    # Artifact-distribution related methods
    ###

    def upload_artifacts(self, timeout: int = 120) -> None:
        """
        Purpose:
            Upload distributable artifacts
        Expected Args:
            timeout: Time in seconds to timeout if the command fails
        Expected Return:
            N/A
        """

        for kit in self.config.artifact_manager_kits:
            upload_script = f'{self.paths.dirs["plugins"]}/{kit.name}/runtime-scripts/upload_artifacts.sh'

            cmd = [
                "bash",
                upload_script,
                f'--artifacts-dir={self.paths.dirs["distribution_artifacts"]}',
                f'--config-dir={self.paths.dirs["artifact_manager_configs_base"]}/{kit.name}',
            ]
            logger.trace(f"Executing command: {' '.join(cmd)}")

            capture_output = True
            if logging.root.level > logging.INFO:
                capture_output = False

            start_time = time.time()

            subprocess.run(
                cmd, check=True, capture_output=capture_output, timeout=timeout
            )

            stop_time = time.time()
            duration = timedelta(seconds=stop_time - start_time)
            logger.trace(f"{kit.name} upload_artifacts.sh took {duration} to execute")

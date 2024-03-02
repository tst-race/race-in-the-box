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
        The RibAwsDeployment Class is a representation of RiB Deployments on
        AWS resources
"""

# Python Library Imports
import logging
import os
import click
import shutil
import time
from datetime import timedelta
from functools import cached_property
from typing import Any, Dict, List, Optional

# Local Python Library Imports
import rib.deployment.rib_deployment_artifacts as deployment_artifacts
from rib.aws_env.rib_aws_env import RibAwsEnv
from rib.aws_env.rib_aws_env_status import AwsComponentStatus
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.status.rib_aws_deployment_status import RibAwsDeploymentStatus
from rib.deployment.paths.rib_aws_deployment_paths import RibAwsDeploymentPaths
from rib.deployment.status.rib_deployment_status import Require
from rib.deployment.rib_deployment_config import (
    AwsDeploymentConfig,
    DeploymentMetadata,
)
from rib.utils import (
    docker_utils,
    file_server_utils,
    general_utils,
    race_node_utils,
    plugin_utils,
    range_config_utils,
)
from rib.utils import aws_topology_utils, error_utils, status_utils


logger = logging.getLogger(__name__)


class RibAwsDeployment(RibDeployment):
    """
    Purpose:
        The RibAwsDeployment Class is a representation of RiB Deployments on
        AWS resources
    """

    ###
    # Class Attributes
    ###

    # Rib Information
    rib_mode = "aws"

    config_class = AwsDeploymentConfig

    pathsClass = RibAwsDeploymentPaths

    ###
    # Static/class methods
    ###

    @classmethod
    def create(
        cls,
        create_command: str,
        name: str,
        aws_env_name: str,
        force: bool,
        # topology
        topology_file: Optional[str],
        colocate_clients_and_servers: bool,
        # config
        fetch_plugins_on_start: bool,
        no_config_gen: bool,
        disabled_channels: Optional[List[str]],
        disable_config_encryption: bool,
        race_log_level: Optional[str],
        # artifacts
        cache: plugin_utils.CacheStrategy,
        race_core: plugin_utils.KitSource,
        android_app: plugin_utils.KitSource,
        linux_app: plugin_utils.KitSource,
        registry_app: Optional[plugin_utils.KitSource],
        node_daemon: plugin_utils.KitSource,
        network_manager_kit: plugin_utils.KitSource,
        comms_channels: List[str],
        comms_kits: List[plugin_utils.KitSource],
        artifact_manager_kits: List[plugin_utils.KitSource],
        # images
        android_client_image: Optional[str],
        linux_client_image: Optional[str],
        linux_server_image: Optional[str],
        bastion_image: Optional[str],
        registry_client_image: Optional[str],
        # range-config
        range_config: Optional[str],
        # node counts
        android_client_count: int,
        android_client_uninstalled_count: int,
        android_client_bridge_count: int,
        android_client_arch: str,
        android_client_enable_ui_for: Optional[List[str]],
        linux_client_count: int,
        linux_client_uninstalled_count: int,
        linux_client_bridge_count: int,
        linux_gpu_client_count: int,
        linux_client_arch: str,
        linux_server_count: int,
        linux_server_uninstalled_count: int,
        linux_server_bridge_count: int,
        linux_gpu_server_count: int,
        linux_server_arch: str,
        registry_client_count: int,
        registry_client_uninstalled_count: int,
        registry_client_arch: str,
        gpu_registry_client_count: int,
    ) -> None:
        # Make sure AWS environment exists
        aws_env = RibAwsEnv.get_aws_env_or_fail(aws_env_name)

        # Make sure deployment doesn't already exist (or remove it if force)
        RibAwsDeployment.ensure_deployment_not_existing_or_remove(
            name, cls.rib_mode, force=force
        )

        if range_config:
            range_config_json = general_utils.load_file_into_memory(
                range_config, data_format="json"
            )
        else:
            range_config_json = range_config_utils.create_local_range_config(
                name=name,
                android_client_count=android_client_count,
                android_client_uninstalled_count=android_client_uninstalled_count,
                android_client_bridge_count=android_client_bridge_count,
                android_client_arch=android_client_arch,
                android_ui_enabled_patterns=android_client_enable_ui_for,
                linux_client_count=linux_client_count,
                linux_client_uninstalled_count=linux_client_uninstalled_count,
                linux_client_bridge_count=linux_client_bridge_count,
                linux_gpu_client_count=linux_gpu_client_count,
                linux_client_arch=linux_client_arch,
                linux_server_count=linux_server_count,
                linux_server_uninstalled_count=linux_server_uninstalled_count,
                linux_server_bridge_count=linux_server_bridge_count,
                linux_gpu_server_count=linux_gpu_server_count,
                linux_server_arch=linux_server_arch,
                registry_client_count=registry_client_count,
                registry_client_uninstalled_count=registry_client_uninstalled_count,
                gpu_registry_client_count=gpu_registry_client_count,
                registry_client_arch=registry_client_arch,
            )

        depl_node_counts = aws_topology_utils.get_node_counts_from_range_config(
            range_config_json
        )

        if topology_file:
            topology = aws_topology_utils.read_topology_from_file(topology_file)
            if not aws_topology_utils.is_topology_compatible_with(
                topology=topology,
                max_instance_counts=aws_env.instance_counts,
                min_node_counts=depl_node_counts,
            ):
                raise error_utils.RIB725(aws_env_name, topology_file)

        else:
            topology = aws_topology_utils.create_topology_from_instance_counts(
                instance_counts=aws_env.instance_counts,
                node_counts=depl_node_counts,
                colocate_clients_and_servers=colocate_clients_and_servers,
            )

        if (
            depl_node_counts.android_arm64_clients
            or depl_node_counts.android_x86_64_clients
        ) and not android_client_image:
            raise error_utils.RIB308(
                name,
                "Deployment must include an Android client image (--android-client-image)",
            )

        if (
            depl_node_counts.linux_arm64_clients
            or depl_node_counts.linux_gpu_arm64_clients
            or depl_node_counts.linux_x86_64_clients
            or depl_node_counts.linux_gpu_x86_64_clients
        ) and not linux_client_image:
            raise error_utils.RIB308(
                name,
                "Deployment must include a Linux client image (--linux-client-image)",
            )

        if (
            depl_node_counts.linux_arm64_servers
            or depl_node_counts.linux_gpu_arm64_servers
            or depl_node_counts.linux_x86_64_servers
            or depl_node_counts.linux_gpu_x86_64_servers
        ) and not linux_server_image:
            raise error_utils.RIB308(
                name,
                "Deployment must include a Linux server image (--linux-server-image)",
            )

        kits = deployment_artifacts.download_deployment_kits(
            cache=cache,
            race_core=race_core,
            android_app=android_app,
            linux_app=linux_app,
            node_daemon=node_daemon,
            registry_app=registry_app,
            network_manager_kit=network_manager_kit,
            comms_channels=comms_channels,
            comms_kits=comms_kits,
            artifact_manager_kits=artifact_manager_kits,
        )

        base_config = RibAwsDeployment.generate_base_config(
            name=name,
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
            # TODO allow separate arm and x86 images
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
        config = AwsDeploymentConfig(
            **base_config.dict(),
            aws_env_name=aws_env_name,
            bastion_image=bastion_image,
        )

        rib_instance_tag = os.environ.get("RIB_INSTANCE_TAG", "")
        rib_container_info = docker_utils.get_container_info(
            "race-in-the-box" + rib_instance_tag
        )
        metadata = DeploymentMetadata(
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

        deployment = RibAwsDeployment(config=config, metadata=metadata)
        deployment.create_directories()
        deployment.copy_templates()

        # Get Plugins.
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

        general_utils.write_data_to_file(
            deployment.paths.files["config"],
            config.dict(),
            data_format="json",
            overwrite=True,
        )

        general_utils.write_data_to_file(
            deployment.paths.files["metadata"],
            metadata.dict(),
            data_format="json",
            overwrite=True,
        )

        if range_config:
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

        aws_topology_utils.write_topology_to_file(
            topology, deployment.paths.files["node_topology"]
        )

        # Bootstrap check needs to be done here in case the deployment was created with a
        # range config rather than node counts. It's still in the command when possible to
        # avoid wasting time with range_config parsing and other initialization.
        if deployment.bootstrap_client_personas:
            comms_channel_info = deployment.get_deployment_channels_list()
            plugin_utils.verify_bootstrap_channel_present(comms_channel_info)

        # Copy VPN Configs
        shutil.copytree(
            f"{deployment.paths.dirs['templates']}/../../common/templates/vpn",
            os.path.join(deployment.paths.dirs["base"], "vpn"),
        )

        # Copy VPN Configs
        shutil.copytree(
            f"{deployment.paths.dirs['templates']}/../../common/templates/dnsproxy",
            os.path.join(deployment.paths.dirs["base"], "dnsproxy"),
        )

        deployment.create_distribution_artifacts()
        deployment.create_mounted_artifacts()
        deployment.generate_docker_compose_files(topology)
        deployment.create_global_etc_files()
        deployment.create_global_configs_and_data(
            fetch_plugins_on_start=fetch_plugins_on_start,
            log_level=race_log_level,
        )

        if no_config_gen:
            logger.info("Skipping plugin config generation")
        else:
            try:
                deployment.generate_plugin_or_channel_configs()
            except Exception as err:
                click.confirm(
                    "Deployment created but config generation failed. Deployment will not run successfully.",
                )
                logger.warning(
                    f"Deployment created but config generation failed. Please manually verify or replace configs in {deployment.paths.dirs['race_configs']} or retry config generation with 'rib deployment {cls.rib_mode} config generate --name={deployment.config['name']} -v --force' to get more debug information"
                )

    ###
    # Instance attributes
    ###

    config: AwsDeploymentConfig

    def get_status(self):
        """Get the Status Object for the deployment"""
        return RibAwsDeploymentStatus(self)

    ###
    # Lifecycle Methods
    ###

    def __init__(
        self, config: AwsDeploymentConfig, metadata: DeploymentMetadata
    ) -> None:
        """
        Purpose:
            Initialize the AWS deployment object.
        Args:
            config: Base deployment configuration
            metadata: Deployment metadata
        Returns:
            N/A
        """

        # Call Parent Init
        super().__init__(config=config, metadata=metadata)

        self.paths = RibAwsDeploymentPaths(self.config["name"])

        self.config = config

        self.aux_services = self.aux_services + ["rib-bastion"]

    ###
    # Instance properties
    ###

    @cached_property
    def _aws_env(self) -> RibAwsEnv:
        """Host AWS environment"""
        return RibAwsEnv.get_aws_env_or_fail(self.config["aws_env_name"])

    @cached_property
    def linux_gpu_client_personas(self) -> List[str]:
        """List of GPU-enabled Linux client node personas"""
        return self.cached_node_lists["gpu_client_personas"]

    @cached_property
    def linux_non_gpu_client_personas(self) -> List[str]:
        """List of non-GPU-enabled Linux client node personas"""
        return list(
            set(self.linux_client_personas)
            - set(self.cached_node_lists["gpu_client_personas"])
        )

    @cached_property
    def gpu_registry_personas(self) -> List[str]:
        """List of GPU-enabled Registry node personas"""
        return self.cached_node_lists["gpu_registry_client_personas"]

    @cached_property
    def non_gpu_registry_personas(self) -> List[str]:
        """List of non-GPU-enabled Registry node personas"""
        return list(
            set(self.registry_personas)
            - set(self.cached_node_lists["gpu_registry_client_personas"])
        )

    @cached_property
    def linux_gpu_server_personas(self) -> List[str]:
        """List of GPU-enabled Linux server node personas"""
        return self.cached_node_lists["gpu_server_personas"]

    @cached_property
    def linux_non_gpu_server_personas(self) -> List[str]:
        """List of non-GPU-enabled Linux server node personas"""
        return list(
            set(self.linux_server_personas)
            - set(self.cached_node_lists["gpu_server_personas"])
        )

    def get_race_image(self, platform: str, arch: str, node_type: str) -> str:
        """
        Purpose:
            Get the RACE node image for a particular node class
        Args:
            platform: Node platform (linux or android)
            arch: Node architecture (x86_64 or arm64)
            node_type: Node type (client or server)
        Return:
            RACE node image name
        """

        race_images = {
            "android": {
                "x86_64": {"client": self.android_x86_64_client_image},
                "arm64": {"client": self.android_arm64_v8a_client_image},
            },
            "linux": {
                "x86_64": {
                    "client": self.linux_x86_64_client_image,
                    "server": self.linux_x86_64_server_image,
                },
                "arm64": {
                    "client": self.linux_arm64_v8a_client_image,
                    "server": self.linux_arm64_v8a_server_image,
                },
            },
        }

        return race_images[platform][arch][node_type]

    def get_elasticsearch_hostname(self) -> List[str]:
        """
        Purpose:
            Get the hostname and port to access elasticsearch
        Expected Args:
            N/A
        Expected Return:
            elasticsearch hostname(s)
        """
        return [f"{self._aws_env.get_cluster_manager_ip()}:9200"]

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
            {} if comms_custom_args_map is None else comms_custom_args_map
        )

        self._generate_plugin_or_channel_configs(
            force=force,
            local=True,  # force local flag since external services won't be in range-config
            network_manager_custom_args=network_manager_custom_args,
            comms_custom_args_map=comms_custom_args_map,
            artifact_manager_custom_args_map=artifact_manager_custom_args_map,
            timeout=timeout,
            max_iterations=max_iterations,
            skip_config_tar=skip_config_tar,
        )

    ###
    # File Methods
    ###

    def copy_templates(self) -> None:
        """
        Purpose:
            Copies all template files into the deployment
        """
        for dir_to_copy in ["ansible"]:
            shutil.copytree(
                os.path.join(self.paths.dirs["templates"], dir_to_copy),
                os.path.join(self.paths.dirs["base"], dir_to_copy),
                dirs_exist_ok=True,
            )

    def generate_docker_compose_files(
        self, topology: aws_topology_utils.NodeInstanceTopology
    ) -> None:
        """
        Purpose:
            Generate necessary docker compose files to stand up the network
        Args:
            topology: Node instance topology
        Return:
            N/A
        """

        personas = aws_topology_utils.Personas()
        for persona, node in self.config["nodes"].items():
            arch = node["architecture"]
            # Don't distribute bridged nodes
            if arch == "auto":
                continue
            personas.get(
                node["platform"],
                node["gpu"],
                "arm64" if arch == "arm64-v8a" else arch,
                # Registries are a subclass of Clients
                node["node_type"] if node["node_type"] != "registry" else "client",
            ).append(persona)

        distribution = aws_topology_utils.distribute_personas_to_instances(
            personas, topology
        )
        aws_topology_utils.write_distribution_to_file(
            distribution, self.paths.files["node_distribution"]
        )

        # Build Shared Docker Compose Data
        common_docker_compose_data = self.generate_common_docker_compose_data()

        # Build Docker Compose Files for Android Node Instances
        for arch in ["arm64", "x86_64"]:
            for num, manifest in enumerate(distribution.get("android", False, arch)):
                android_node_docker_compose_data = (
                    self.generate_android_node_docker_compose_data(manifest, arch)
                )
                android_node_docker_compose_data.update(common_docker_compose_data)

                general_utils.write_data_to_file(
                    f"{self.paths.dirs['docker_compose']}/android-{arch}-nodes-{num}.yml",
                    android_node_docker_compose_data,
                    data_format="yaml",
                    overwrite=True,
                )

        # Build Docker Compose Files for GPU Node Instances
        for arch in ["arm64", "x86_64"]:
            for num, manifest in enumerate(distribution.get("linux", True, arch)):
                gpu_node_docker_compose_data = (
                    self.generate_gpu_node_docker_compose_data(manifest, arch)
                )
                gpu_node_docker_compose_data.update(common_docker_compose_data)
                general_utils.write_data_to_file(
                    f"{self.paths.dirs['docker_compose']}/linux-gpu-{arch}-nodes-{num}.yml",
                    gpu_node_docker_compose_data,
                    data_format="yaml",
                    overwrite=True,
                )

        # Build Docker Compose Files for Linux Node Instances
        for arch in ["arm64", "x86_64"]:
            for num, manifest in enumerate(distribution.get("linux", False, arch)):
                linux_node_docker_compose_data = (
                    self.generate_linux_node_docker_compose_data(manifest, arch)
                )
                linux_node_docker_compose_data.update(common_docker_compose_data)
                general_utils.write_data_to_file(
                    f"{self.paths.dirs['docker_compose']}/linux-{arch}-nodes-{num}.yml",
                    linux_node_docker_compose_data,
                    data_format="yaml",
                    overwrite=True,
                )

        # Build RACE Services Docker Compose Data
        opentracing_docker_compose_data = (
            self.generate_opentracing_docker_compose_data()
        )
        opentracing_docker_compose_data.update(common_docker_compose_data)

        general_utils.write_data_to_file(
            f"{self.paths.dirs['docker_compose']}/opentracing.yml",
            opentracing_docker_compose_data,
            data_format="yaml",
            overwrite=True,
        )

        # Build RACE Services Docker Compose Data
        vpn_docker_compose_data = self.generate_vpn_docker_compose_data()
        vpn_docker_compose_data.update(common_docker_compose_data)

        general_utils.write_data_to_file(
            f"{self.paths.dirs['docker_compose']}/vpn.yml",
            vpn_docker_compose_data,
            data_format="yaml",
            overwrite=True,
        )

        # Build Bastion Docker Compose Data
        bastion_docker_compose_data = self.generate_bastion_docker_compose_data()
        bastion_docker_compose_data.update(common_docker_compose_data)

        general_utils.write_data_to_file(
            f"{self.paths.dirs['docker_compose']}/bastion.yml",
            bastion_docker_compose_data,
            data_format="yaml",
            overwrite=True,
        )

        # Build Orchestration Services Docker Compose Data
        orchestration_service_docker_compose_data = (
            self.generate_orchestration_service_docker_compose_data()
        )
        orchestration_service_docker_compose_data.update(common_docker_compose_data)

        general_utils.write_data_to_file(
            f"{self.paths.dirs['docker_compose']}/orchestration.yml",
            orchestration_service_docker_compose_data,
            data_format="yaml",
            overwrite=True,
        )

    def generate_common_docker_compose_data(self) -> Dict[str, Any]:
        """
        Purpose:
            Create docker compose data that is common to the services, nodes,
            and bastion docker compose files.
        Args:
            N/A
        Return:
            common_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        common_docker_compose_data = {"version": {}, "x-logging": {}, "networks": {}}

        # Load Base Values
        common_docker_compose_data.update(
            general_utils.load_file_into_memory(
                f"{compose_template_dir}/version.yml", data_format="yaml"
            )
        )
        common_docker_compose_data.update(
            general_utils.load_file_into_memory(
                f"{compose_template_dir}/logging.yml", data_format="yaml"
            )
        )
        common_docker_compose_data.update(
            general_utils.load_file_into_memory(
                f"{compose_template_dir}/networks.yml", data_format="yaml"
            )
        )

        return common_docker_compose_data

    def generate_android_node_docker_compose_data(
        self,
        manifest: aws_topology_utils.NodeInstanceManifest,
        arch: str,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Use the given RACE node manifest to create a docker-compose file for
            Android RACE nodes
        Args:
            manifest: RACE node manifest
            arch: Host architecture
        Return:
            node_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data (including any co-located Linux nodes)
        node_docker_compose_data = self.generate_linux_node_docker_compose_data(
            manifest, arch
        )

        # VNC Port
        base_vnc_port = 5901

        # TODO, discuss this. My understanding was both android emulators
        # require priviledged
        privileged = True
        # Cuttlefish emulator used for ARM clients requires privileged mode
        # privileged = self.android_clients.get("arch") == "arm"

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

        client_bootstrap_volumes = [
            {
                "type": "bind",
                "source": f"/race/android-{arch}-client/core/race-daemon",
                "target": f"/android/{arch}/lib/race/core/race-daemon",
            }
        ]
        client_genesis_volumes = []
        for ta in ["artifact-manager", "network-manager", "comms", "core"]:
            client_genesis_volumes.append(
                {
                    "type": "bind",
                    "source": f"/race/android-{arch}-client/{ta}",
                    "target": f"/android/{arch}/lib/race/{ta}",
                }
            )

        for client_id, client_persona in enumerate(manifest.android_clients):
            # Use modulo logic to chain client 1->4->7, client 2->5->8, etc
            # clients 1,2,3 have no depends on
            depends_on_idx = client_id % depends_on_modulo
            if not depends_on_map.get(depends_on_idx, None):
                depends_on_map[depends_on_idx] = client_persona
                depends_on = ""
            else:
                depends_on = "depends_on:\n    - " + depends_on_map[depends_on_idx]
                depends_on_map[depends_on_idx] = client_persona

            # Cuttlefish starts the VNC server on port `6444 + CUTTLEFISH_INSTANCE - 1`,
            # whereas for x86_64 we start the VNC server on port 5901
            internal_vnc_port = 5901 if arch == "x86_64" else 6444 + client_id

            node_docker_compose_data["services"].update(
                general_utils.format_yaml_template(
                    f"{compose_template_dir}/android-node.yml",
                    {
                        "node_name": client_persona,
                        "node_type": "client",
                        "image": self.get_race_image("android", arch, "client"),
                        "external_vnc_port": base_vnc_port + client_id,
                        "internal_vnc_port": internal_vnc_port,
                        # Cuttlefish instance num is 1-based, enumerate's index is 0-based
                        "instance_num": client_id + 1,
                        # When there are less than about 5 Android clients, it is faster to start
                        # them all at once than to spread them out with a startup delay. With 10
                        # Android clients starting all at once, they eventually all startup
                        # correctly, but perhaps not as efficiently. It doesn't seem worth it right
                        # now to use a non-zero startup delay since most performers will be running
                        # with only a few Android clients.
                        "startup_delay": 0,  # 60 * client_id,
                        "privileged": privileged,
                        "optional_depends_on": depends_on,
                        "race_encryption_type": self.config["race_encryption_type"],
                    },
                )
            )

            # Set UNINSTALL_RACE env var appropriately so non-genesis nodes will uninstall/delete
            # all RACE artifacts when the container is started
            if client_persona in self.android_genesis_client_personas:
                uninstall = "no"
                node_docker_compose_data["services"][client_persona]["volumes"].extend(
                    client_genesis_volumes
                )
            else:
                uninstall = "yes"
                node_docker_compose_data["services"][client_persona]["volumes"].extend(
                    client_bootstrap_volumes
                )
            node_docker_compose_data["services"][client_persona]["environment"][
                "UNINSTALL_RACE"
            ] = uninstall

        return node_docker_compose_data

    def generate_gpu_node_docker_compose_data(
        self,
        manifest: aws_topology_utils.NodeInstanceManifest,
        arch: str,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Use the given RACE node manifest to create a docker-compose file for
            GPU-enabled Linux RACE nodes
        Args:
            manifest: RACE node manifest
            arch: Host architecture
        Return:
            node_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data (including any co-located Linux nodes)
        node_docker_compose_data = self.generate_linux_node_docker_compose_data(
            manifest, arch
        )

        server_bootstrap_volumes = [
            {
                "type": "bind",
                "source": f"/race/linux-{arch}-server/core/race-daemon",
                "target": "/usr/local/lib/race/core/race-daemon",
            }
        ]
        server_genesis_volumes = []
        for ta in ["artifact-manager", "network-manager", "comms", "core"]:
            server_genesis_volumes.append(
                {
                    "type": "bind",
                    "source": f"/race/linux-{arch}-server/{ta}",
                    "target": f"/usr/local/lib/race/{ta}",
                }
            )

        for server_persona in manifest.linux_gpu_servers:
            node_docker_compose_data["services"].update(
                general_utils.format_yaml_template(
                    f"{compose_template_dir}/gpu-node.yml",
                    {
                        "node_name": server_persona,
                        "image": self.get_race_image("linux", arch, "server"),
                        "optional_depends_on": "",  # No depends_on for gpu servers
                        "race_encryption_type": self.config["race_encryption_type"],
                    },
                )
            )

            # Set UNINSTALL_RACE env var appropriately so non-genesis nodes will uninstall/delete
            # all RACE artifacts when the container is started
            if server_persona in self.linux_genesis_server_personas:
                uninstall = "no"
                node_docker_compose_data["services"][server_persona]["volumes"].extend(
                    server_genesis_volumes
                )
            else:
                uninstall = "yes"
                node_docker_compose_data["services"][server_persona]["volumes"].extend(
                    server_bootstrap_volumes
                )
            node_docker_compose_data["services"][server_persona]["environment"][
                "UNINSTALL_RACE"
            ] = uninstall

        client_bootstrap_volumes = [
            {
                "type": "bind",
                "source": f"/race/linux-{arch}-client/core/race-daemon",
                "target": "/usr/local/lib/race/core/race-daemon",
            }
        ]
        client_genesis_volumes = []
        for ta in ["artifact-manager", "network-manager", "comms", "core"]:
            client_genesis_volumes.append(
                {
                    "type": "bind",
                    "source": f"/race/linux-{arch}-client/{ta}",
                    "target": f"/usr/local/lib/race/{ta}",
                }
            )

        for client_persona in manifest.linux_gpu_clients:
            node_docker_compose_data["services"].update(
                general_utils.format_yaml_template(
                    f"{compose_template_dir}/gpu-node.yml",
                    {
                        "node_name": client_persona,
                        "image": self.get_race_image("linux", arch, "client"),
                        "optional_depends_on": "",  # No depends_on for gpu clients
                        "race_encryption_type": self.config["race_encryption_type"],
                    },
                )
            )

            # Set UNINSTALL_RACE env var appropriately so non-genesis nodes will uninstall/delete
            # all RACE artifacts when the container is started
            if client_persona in self.linux_genesis_client_personas:
                uninstall = "no"
                node_docker_compose_data["services"][client_persona]["volumes"].extend(
                    client_genesis_volumes
                )
            else:
                uninstall = "yes"
                node_docker_compose_data["services"][client_persona]["volumes"].extend(
                    client_bootstrap_volumes
                )
            node_docker_compose_data["services"][client_persona]["environment"][
                "UNINSTALL_RACE"
            ] = uninstall

        return node_docker_compose_data

    def generate_linux_node_docker_compose_data(
        self,
        manifest: aws_topology_utils.NodeInstanceManifest,
        arch: str,
    ) -> Dict[str, Any]:
        """
        Purpose:
            Use the given RACE node manifest to create a docker-compose file for
            Linux RACE nodes (non-GPU)
        Args:
            manifest: RACE node manifest
            arch: Host architecture
        Return:
            node_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        node_docker_compose_data = {"services": {}}

        server_bootstrap_volumes = [
            {
                "type": "bind",
                "source": f"/race/linux-{arch}-server/core/race-daemon",
                "target": "/usr/local/lib/race/core/race-daemon",
            }
        ]
        server_genesis_volumes = []
        for ta in ["artifact-manager", "network-manager", "comms", "core"]:
            server_genesis_volumes.append(
                {
                    "type": "bind",
                    "source": f"/race/linux-{arch}-server/{ta}",
                    "target": f"/usr/local/lib/race/{ta}",
                }
            )

        for server_persona in manifest.linux_servers:
            server_docker_compose_data = general_utils.format_yaml_template(
                f"{compose_template_dir}/linux-node.yml",
                {
                    "node_name": server_persona,
                    "node_type": "server",
                    "image": self.get_race_image("linux", arch, "server"),
                    "optional_depends_on": "",  # No depends_on for linux servers
                    "race_encryption_type": self.config["race_encryption_type"],
                },
            )

            # Set UNINSTALL_RACE env var appropriately so non-genesis nodes will uninstall/delete
            # all RACE artifacts when the container is started
            if server_persona in self.linux_genesis_server_personas:
                uninstall = "no"
                server_docker_compose_data[server_persona]["volumes"].extend(
                    server_genesis_volumes
                )
            else:
                uninstall = "yes"
                server_docker_compose_data[server_persona]["volumes"].extend(
                    server_bootstrap_volumes
                )
            server_docker_compose_data[server_persona]["environment"][
                "UNINSTALL_RACE"
            ] = uninstall

            node_docker_compose_data["services"].update(server_docker_compose_data)

        client_bootstrap_volumes = [
            {
                "type": "bind",
                "source": f"/race/linux-{arch}-client/core/race-daemon",
                "target": "/usr/local/lib/race/core/race-daemon",
            }
        ]
        client_genesis_volumes = []
        for ta in ["artifact-manager", "network-manager", "comms", "core"]:
            client_genesis_volumes.append(
                {
                    "type": "bind",
                    "source": f"/race/linux-{arch}-client/{ta}",
                    "target": f"/usr/local/lib/race/{ta}",
                }
            )

        for client_persona in manifest.linux_clients:
            client_docker_compose_data = general_utils.format_yaml_template(
                f"{compose_template_dir}/linux-node.yml",
                {
                    "node_name": client_persona,
                    "node_type": "client",
                    "image": self.get_race_image("linux", arch, "client"),
                    "optional_depends_on": "",  # No depends_on for linux clients
                    "race_encryption_type": self.config["race_encryption_type"],
                },
            )

            # Set UNINSTALL_RACE env var appropriately so non-genesis nodes will uninstall/delete
            # all RACE artifacts when the container is started
            if client_persona in self.linux_genesis_client_personas:
                uninstall = "no"
                client_docker_compose_data[client_persona]["volumes"].extend(
                    client_genesis_volumes
                )
            else:
                uninstall = "yes"
                client_docker_compose_data[client_persona]["volumes"].extend(
                    client_bootstrap_volumes
                )
            client_docker_compose_data[client_persona]["environment"][
                "UNINSTALL_RACE"
            ] = uninstall

            node_docker_compose_data["services"].update(client_docker_compose_data)

        return node_docker_compose_data

    def generate_bastion_docker_compose_data(self) -> Dict[str, Any]:
        """
        Purpose:
            Create the Bastion docker compose file
        Args:
            N/A
        Return:
            bastion_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        bastion_docker_compose_data = {"services": {}}

        # Add Bastion Service
        bastion_docker_compose_data["services"].update(
            general_utils.format_yaml_template(
                f"{compose_template_dir}/bastion.yml",
                {
                    "image": self.config["bastion_image"],
                    "remote_username": self._aws_env.config.remote_username,
                },
            )
        )

        return bastion_docker_compose_data

    def generate_opentracing_docker_compose_data(self) -> Dict[str, Any]:
        """
        Purpose:
            Based on opentracing settings, create a docker-compose
            file to run a version of the RACE network.

            Note: this will include elasticsearch, kibana, and jaeger UI
        Args:
            N/A
        Return:
            opentracing_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        opentracing_docker_compose_data = {"services": {}}

        # Add Opentracing services
        opentracing_docker_compose_data["services"].update(
            general_utils.format_yaml_template(
                f"{compose_template_dir}/open-tracing.yml"
            )
        )

        return opentracing_docker_compose_data

    def generate_vpn_docker_compose_data(self) -> Dict[str, Any]:
        """
        Purpose:
            Based on vpn settings, create a docker-compose
            file to run a version of the RACE network.

            Note: this will include elasticsearch, kibana, and jaeger UI
        Args:
            N/A
        Return:
            vpn_docker_compose_data (Dict): Dict representation of the resulting
                docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        vpn_docker_compose_data = {"services": {}}

        # Add Opentracing services
        vpn_docker_compose_data["services"].update(
            general_utils.format_yaml_template(f"{compose_template_dir}/vpn.yml")
        )

        return vpn_docker_compose_data

    def generate_orchestration_service_docker_compose_data(self) -> Dict[str, Any]:
        """
        Purpose:
            Create docker-compose services for RiB orchestration services
            (redis, file server, etc.)
        Args:
            N/A
        Return:
            Dict representation of the resulting docker-compose file
        """
        # Template Dirs
        compose_template_dir = f"{self.paths.dirs['templates']}/docker-compose"

        # Create Base Compose Data
        orchestration_service_docker_compose_data = {"services": {}}

        # Add Orchestration services
        orchestration_service_docker_compose_data["services"].update(
            general_utils.format_yaml_template(
                f"{compose_template_dir}/orchestration-services.yml"
            )
        )

        return orchestration_service_docker_compose_data

    def create_mounted_artifacts(self) -> None:
        """
        Purpose:
            Create archive of all artifacts to be mounted into node containers
        Args:
            N/A
        Return:
            N/A
        """

        for (
            platform,
            architecture,
            node_type,
        ) in self.paths.supported_platform_arch_node_type_combinations:
            if node_type == "registry":
                continue
            platform_artifacts_path = self.paths.dirs[
                self.paths.get_plugin_artifacts_base_dir_key(
                    platform, architecture, node_type
                )
            ]
            if os.path.isdir(platform_artifacts_path):
                output_file = f'{self.paths.dirs["mounted_artifacts"]}/{platform}-{architecture}-{node_type}.tar.gz'
                general_utils.tar_directory(platform_artifacts_path, output_file)

    ###
    # Setup/Teardown Deployment Methods
    ###

    def _verify_env_is_ready(self, action: str) -> None:
        """
        Purpose:
            Checks if the host AWS environment is ready to be used.
        Args:
            action: Action being performed
        Return:
            True if the
        """
        status_report = self._aws_env.get_status_report()
        if status_report.status != AwsComponentStatus.READY:
            raise error_utils.RIB340(
                deployment_name=self.config["name"],
                aws_env_name=self.config["aws_env_name"],
                action=action,
                aws_env_status=status_report.status,
            )

    def up(
        self,
        last_up_command: str,
        docker_token: Optional[str],
        docker_user: Optional[str],
        dry_run: bool = False,
        no_publish: bool = False,
        force: bool = False,
        timeout: int = 3_600,
        verbosity: int = 0,
    ) -> None:
        """
        Purpose:
            Stand up a RACE deployment on the host AWS environment.

            This will upload all configs, docker-compose files, and scripts specific to the
            deployment. Then all containers for the deployment will be started.

            This does NOT start the RACE app on the nodes.
        Args:
            last_up_command: The command (CLI) that upped the deployment
            docker_token: Authentication token for docker registry access
            docker_user: Username for docker registry access
            dry_run: Run ansible in check mode
            no_publish: If True, configs will not be published after upping
            force: Whether or not to force the operation
            timeout: Time in seconds to timeout if the command fails
            verbosity: Playbook output verbosity
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("stand up", none_ok=True)

        if not force:
            self._verify_env_is_ready("stand up")
            # Make sure no containers are up yet
            self.status.get_containers_that_match_status(
                action="stand up",
                names=self.managed_personas + self.aux_services,
                container_status=[status_utils.ContainerStatus.NOT_PRESENT],
                require=Require.ALL,
                force=force,
                verbosity=verbosity,
            )

        self.update_metadata(
            {
                "last_up_command": last_up_command,
                "last_up_time": general_utils.get_current_time(),
            }
        )

        # Plugin configs to be uploaded (currently only artifact manager plugins require
        # uploaded configs)
        plugin_configs = {
            kit.name: os.path.join(
                self.paths.dirs["artifact_manager_configs_base"], kit.name
            )
            for kit in self.config.artifact_manager_kits
        }

        # Plugin runtime-scripts to be uploaded (currently only artifact manager plugins have
        # runtime-scripts)
        plugin_runtime_scripts = {
            kit.name: os.path.join(
                self.paths.dirs["plugins"], kit.name, "runtime-scripts"
            )
            for kit in self.config.artifact_manager_kits
        }

        self._aws_env.run_playbook(
            dry_run=dry_run,
            playbook_file=self.paths.files["ansible_stand_up_playbook"],
            playbook_vars={
                "dataEtcDir": self.paths.dirs["etc"],
                "deploymentName": self.config["name"],
                "distArtifactsDir": self.paths.dirs["distribution_artifacts"],
                "dockerComposeDir": self.paths.dirs["docker_compose"],
                "dockerRegistry": self.rib_config.CONTAINER_REGISTRY_URL,
                "dockerToken": docker_token or "",
                "dockerUsername": docker_user or "",
                "externalServices": self._external_services,
                "mountArtifactsDir": self.paths.dirs["mounted_artifacts"],
                "pluginConfigDirs": plugin_configs,
                "pluginRuntimeScripts": plugin_runtime_scripts,
                "distVpnDir": str(os.path.join(self.paths.dirs["base"], "vpn")),
                "distDnsProxyDir": str(
                    os.path.join(self.paths.dirs["base"], "dnsproxy")
                ),
            },
            timeout=timeout,
            verbosity=verbosity,
        )

        # Check status post up
        self.status.wait_for_containers_to_match_status(
            action="stand up",
            names=self.managed_personas + self.aux_services,
            container_status=[status_utils.ContainerStatus.RUNNING],
            timeout=timeout,
        )
        self.status.wait_for_nodes_to_match_status(
            action="stand up",
            personas=self.managed_personas,
            daemon_status=[status_utils.DaemonStatus.RUNNING],
            timeout=timeout,
        )
        self.status.wait_for_services_to_match_status(
            action="stand up",
            parent_status=[status_utils.ParentStatus.ALL_RUNNING],
            timeout=timeout,
        )

        # Set Daemon Config
        for node_name in self.managed_personas:
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
            self.upload_configs(timeout=timeout, require=Require.NONE)

            # Call the node daemon to trigger a pull of the configs from the file server.
            nodes_with_configs_pushed = self.status.get_nodes_that_match_status(
                action="pull configs",
                personas=self.managed_personas,
                configs_status=[status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED],
                force=force,
                verbosity=verbosity,
            )
            for node_name in self.managed_personas:
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
                personas=self.managed_personas,
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

    def down(
        self,
        last_down_command: str,
        dry_run: bool = False,
        force: bool = False,
        purge: bool = False,
        timeout: int = 600,
        verbosity: int = 0,
    ) -> None:
        """
        Purpose:
            Teardown and clean the deployment.

            This will stop and remove any containers running.
        Args:
            last_down_command: The command (CLI) that downed the deployment
            dry_run: Run ansible in check mode
            force: Whether or not to force the operation
            purge: Whether to purge all data and images from the host environment
            timeout: Time in seconds to timeout if the command fails
            verbose: Enable verbose output
            verbosity: Playbook output verbosity
        Return:
            N/A
        """
        self.status.verify_deployment_is_active("tear down", none_ok=force)

        # Make sure all apps are stopped/can be torn down
        self.status.get_nodes_that_match_status(
            action="tear down",
            personas=self.managed_personas,
            app_status=[
                status_utils.AppStatus.NOT_REPORTING,
                status_utils.AppStatus.NOT_INSTALLED,
                status_utils.AppStatus.NOT_RUNNING,
            ],
            require=Require.ALL,
            force=force,
            quiet=True,
        )
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

        self.update_metadata(
            {
                "last_down_command": last_down_command,
                "last_down_time": general_utils.get_current_time(),
            }
        )

        self._aws_env.run_playbook(
            dry_run=dry_run,
            playbook_file=self.paths.files["ansible_tear_down_playbook"],
            playbook_vars={
                "externalServices": self._external_services,
                "purgeAllData": purge,
            },
            timeout=timeout,
            verbosity=verbosity,
        )

        # Check status post down
        self.status.wait_for_containers_to_match_status(
            action="tear down",
            names=self.managed_personas + self.aux_services,
            container_status=[status_utils.ContainerStatus.NOT_PRESENT],
            timeout=timeout,
        )
        self.status.wait_for_nodes_to_match_status(
            action="tear down",
            personas=self.managed_personas,
            daemon_status=[status_utils.DaemonStatus.NOT_REPORTING],
            timeout=timeout,
        )
        self.status.wait_for_services_to_match_status(
            action="tear down",
            parent_status=[status_utils.ParentStatus.ALL_DOWN],
            timeout=timeout,
        )

    ###
    # Remote Interface/Client Methods
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
        return race_node_utils.RaceNodeInterface(self._aws_env.get_cluster_manager_ip())

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
        return file_server_utils.FileServerClient(
            f"http://{self._aws_env.get_cluster_manager_ip()}:3453"
        )

    def get_vpn_ip_address(self) -> str:
        """
        Purpose:
            Get the IP address of the VPN server to be configured in bridged nodes
        Args:
            N/A
        Return:
            VPN server IP address
        """
        return self._aws_env.get_cluster_manager_ip()

    ###
    # Plugin Methods
    ###

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

    def upload_artifacts(self, timeout: int = 600) -> None:
        """
        Purpose:
            Upload distributable artifacts
        Expected Args:
            timeout: Time in seconds to timeout if the command fails
        Expected Return:
            N/A
        """

        for kit in self.config.artifact_manager_kits:
            plugin_name = kit.name
            upload_script = f"/data/runtime-scripts/{plugin_name}/upload_artifacts.sh"

            cmd = [
                "bash",
                upload_script,
                "--artifacts-dir=/data/dist/",
                f"--config-dir=/data/configs/{plugin_name}",
            ]
            cmd_as_str = " ".join(cmd)
            logger.trace(f"Executing command: {cmd_as_str}")

            start_time = time.time()

            self._aws_env.run_remote_command(
                command=cmd_as_str,
                check_exit_status=True,
                role=RibAwsEnv.BASTION_ROLE,
                timeout=timeout,
            )

            stop_time = time.time()
            duration = timedelta(seconds=stop_time - start_time)
            logger.trace(
                f"{plugin_name} upload_artifacts.sh took {duration} to execute"
            )

    ###
    # Status Methods
    ###

    def get_active(self) -> Optional[str]:
        """
        Purpose:
            Get the name of the active deployment on the host AWS environment, or None if no
            deployment is active

            Note/TODO: This is an instance method while get_active is a classmethod in the
            base class. this will be addressed in 2.2.0+
        Args:
            N/A
        Returns:
            Active deployment name, if any is active
        """
        return self._aws_env.get_active_deployment()

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
    RiB AWS environment
"""

# Python Library Imports
import json
import logging
import os
import paramiko
import requests
import shutil
import socket
from functools import cached_property
from typing import (
    Any,
    Collection,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    TypedDict,
    get_type_hints,
)

# Local Python Library Imports
from rib.aws_env import rib_aws_env_files
from rib.aws_env.rib_aws_env_config import (
    AwsEnvConfig,
    AwsEnvMetadata,
    Ec2InstanceConfig,
    Ec2InstanceDetails,
    Ec2InstanceGroupConfig,
)
from rib.aws_env.rib_aws_env_files import AwsEnvFiles
from rib.aws_env.rib_aws_env_status import (
    ActiveAwsEnvs,
    AwsComponentStatus,
    AwsEnvComponentStatus,
    AwsEnvStatus,
    ContainerRuntimeInfo,
    Ec2InstanceRuntimeInfo,
    IncompatibleAwsEnv,
    LocalAwsEnvs,
    StatusReport,
    convert_cf_status_to_enum,
    convert_ec2_status_to_enum,
    convert_efs_status_to_enum,
    create_parent_report,
    get_parent_status,
)
from rib.utils import (
    ansible_utils,
    aws_topology_utils,
    aws_utils,
    docker_utils,
    error_utils,
    general_utils,
    network_utils,
    rib_utils,
    ssh_utils,
    system_utils,
    threading_utils,
)


###
# Globals
###


logger = logging.getLogger(__name__)


###
# Types
###


class RemoteCommandResult(TypedDict):
    success: bool
    stdout: Iterable[str]
    stderr: Iterable[str]


class RibAwsEnv:
    """
    Purpose:
        RiB AWS environment
    """

    # Class constants
    BASTION_ROLE = "bastion"
    CLUSTER_MANAGER_ROLE = "cluster-manager"
    SERVICE_HOST_ROLE = "service-host"
    LINUX_ARM_NODE_HOST_ROLE = "linux-arm64-node-host"
    LINUX_x86_NODE_HOST_ROLE = "linux-x86-64-node-host"
    LINUX_GPU_ARM_NODE_HOST_ROLE = "linux-gpu-arm64-node-host"
    LINUX_GPU_x86_NODE_HOST_ROLE = "linux-gpu-x86-64-node-host"
    ANDROID_ARM_NODE_HOST_ROLE = "android-arm64-node-host"
    ANDROID_x86_NODE_HOST_ROLE = "android-x86-64-node-host"

    ###
    # Static/class methods
    ###

    @classmethod
    def aws_env_exists(cls, name: str) -> bool:
        """
        Purpose:
            Checks if an AWS environment exists with the given name on disk. This does
            not attempt to load it, so it is possible that the env is not compatible
            with the current version of RiB.
        Args:
            name: AWS environment name
        Return:
            True if an AWS environment exists with the given name
        """

        env_dir = os.path.join(rib_aws_env_files.root_dir, name)
        return os.path.isdir(env_dir)

    @classmethod
    def _load_aws_env(cls, name: str) -> "RibAwsEnv":
        """
        Purpose:
            Loads the AWS environment with the given name from disk
        Args:
            name: AWS environment name
        Return:
            AWS environment
        """
        env_files = AwsEnvFiles(name)
        config = env_files.read_config()
        metadata = env_files.read_metadata()
        return RibAwsEnv(config=config, files=env_files, metadata=metadata)

    @classmethod
    def load_aws_env(cls, name: str, quiet: bool = False) -> Optional["RibAwsEnv"]:
        """
        Purpose:
            Loads the AWS environment with the given name from disk
        Args:
            name: AWS environment name
            quiet: Whether to suppress load error logging
        Return:
            AWS environment, if successfully loaded
        """

        try:
            return cls._load_aws_env(name)
        except Exception as err:
            if not quiet:
                logger.debug(f"Unable to load AWS environment {name}: {err}")
            return None

    @classmethod
    def get_aws_env_or_fail(cls, name: str) -> "RibAwsEnv":
        """
        Purpose:
            Loads the AWS environment with the given name from disk, raising an
            exception if the AWS environment does not exist
        Args:
            name: AWS environment name
        Return:
            AWS environment
        """

        try:
            return cls._load_aws_env(name)
        except Exception as err:
            logger.error(f"Unable to load AWS env {name}: {err}")
            aws_envs = cls.get_local_aws_envs()
            if not aws_envs.compatible:
                raise error_utils.RIB708() from None
            raise error_utils.RIB709(name, aws_envs.compatible) from None

    @classmethod
    def get_local_aws_envs(cls) -> LocalAwsEnvs:
        """
        Purpose:
            Get all AWS environments on the local machine
        Args:
            N/A
        Return:
            Local AWS environment names
        """

        compatible = set()
        incompatible = set()

        for name in os.listdir(rib_aws_env_files.root_dir):
            if os.path.isdir(os.path.join(rib_aws_env_files.root_dir, name)):
                env = cls.load_aws_env(name, quiet=True)
                if env:
                    compatible.add(name)
                else:
                    incompatible.add(
                        IncompatibleAwsEnv(
                            name=name,
                            rib_version=cls.get_compatible_rib_version_for(name),
                        )
                    )

        return LocalAwsEnvs(
            compatible=compatible,
            incompatible=incompatible,
        )

    @classmethod
    def get_compatible_rib_version_for(cls, name: str) -> str:
        """
        Purpose:
            Reads the AWS environment's config and metadata to determine
            what version of RiB is compatible with the AWS environment
        Args:
            name: AWS environment name
        Return:
            Compatible RiB version
        """
        env_files = AwsEnvFiles(name)
        try:
            config = env_files.read_config_dict()
            if "rib_version" in config:
                return config["rib_version"]
        except:
            pass

        # Legacy AWS envs stored the RiB version in the metadata
        try:
            metadata = env_files.read_metadata()
            if "rib_version" in metadata:
                return metadata["rib_version"]
        except:
            pass

        return "unknown"

    @classmethod
    def get_active_aws_envs(cls) -> ActiveAwsEnvs:
        """
        Purpose:
            Gets the names of all active AWS environments

            Because AWS costs money for the user, this is a simple way of identifying stacks that
            are running to at least give a simple way for users to find what envs have some
            resources running just in case.
        Args:
            N/A
        Return:
            Active AWS environment names
        """

        # Connect AWS session
        aws_session = aws_utils.connect_aws_session_with_profile()

        # Get all Cloudformation Stacks
        found_cf_stacks = aws_utils.get_cf_stacks(aws_session)

        # Filter out cloudformation based on a tag we set for all RiB Stacks
        filtered_cf_stacks = aws_utils.filter_cf_stacks_by_tags_and_state(
            found_cf_stacks, tags={"Creator": "rib"}, state="CREATE_COMPLETE"
        )

        # Finding Known AWS Envs for Reporting
        local_aws_envs = cls.get_local_aws_envs()
        local_aws_env_names = local_aws_envs.compatible
        for incompatible_local_aws_env in local_aws_envs.incompatible:
            local_aws_env_names.add(incompatible_local_aws_env.name)

        # Filtering found vs known
        owned_aws_env_names = set()
        not_owned_aws_env_names = set()
        for _, filtered_cf_stack in filtered_cf_stacks.items():
            aws_env_name = filtered_cf_stack["tags"].get("AwsEnvName", "Unknown")

            if aws_env_name in local_aws_env_names:
                owned_aws_env_names.add(aws_env_name)
            else:
                not_owned_aws_env_names.add(aws_env_name)

        return ActiveAwsEnvs(
            owned=owned_aws_env_names,
            unowned=not_owned_aws_env_names,
        )

    @classmethod
    def remove_legacy_aws_env(cls, name: str) -> None:
        """
        Purpose:
            Forcibly removes a legacy AWS environment created by an older version of
            RiB
        Args:
            name: AWS environment name
        Return:
            N/A
        """

        env_dir = os.path.join(rib_aws_env_files.root_dir, name)
        if os.path.isdir(env_dir):
            shutil.rmtree(env_dir)

    @classmethod
    def create(
        cls,
        aws_env_name: str,
        create_command: str,
        instance_counts: aws_topology_utils.InstanceCounts,
        instance_ebs_sizes: aws_topology_utils.InstanceEbsSizes,
        instance_type_names: aws_topology_utils.InstanceTypeNames,
        remote_username: str,
        region: str,
        ssh_key_name: str,
    ) -> None:
        """
        Purpose:
            Creates a new AWS environment
        Args:
            aws_env_name: Name of the AWS environment
            create_command: RiB command used to create the AWS environment
            instance_counts: Numbers of EC2 instances
            instance_ebs_sizes: Sizes of instance EBS volumes
            instance_type_names: Names of EC2 instance types
            remote_username: Username to use for SSH connections to EC2 instances
            region: AWS region in which to create all AWS resources
            ssh_key_name: Name of the SSH key-pair to use
        Return:
            N/A
        """

        rib_config = rib_utils.load_race_global_configs()
        rib_aws_preferences = aws_utils.get_rib_aws_preferences()

        # Validate instance arch/metal/gpu compatibility
        aws_topology_utils.get_instance_type_details(
            instance_type_names, instance_counts
        )

        files = AwsEnvFiles(aws_env_name)
        files.create_directories()
        files.copy_templates()

        config = AwsEnvConfig(
            name=aws_env_name,
            rib_version=rib_config.RIB_VERSION,
            ssh_key_name=ssh_key_name,
            remote_username=remote_username,
            region=region,
            cluster_manager=Ec2InstanceConfig(
                instance_type=instance_type_names.cluster_manager_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_x86_64_ami", rib_config.LINUX_x86_64_AMI
                ),  # TODO do we need to support arm cluster managers?
                ebs_size=instance_ebs_sizes.cluster_manager_instance_ebs_size_gb,
            ),
            service_host=Ec2InstanceConfig(
                instance_type=instance_type_names.service_host_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_x86_64_ami", rib_config.LINUX_x86_64_AMI
                ),  # TODO do we need to support arm service hosts?
                ebs_size=instance_ebs_sizes.service_host_instance_ebs_size_gb,
            ),
            android_arm64_hosts=Ec2InstanceGroupConfig(
                instance_count=instance_counts.android_arm64_instances,
                instance_type=instance_type_names.android_arm64_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_arm64_ami", rib_config.LINUX_ARM64_AMI
                ),
                ebs_size=instance_ebs_sizes.android_instance_ebs_size_gb,
            ),
            android_x86_64_hosts=Ec2InstanceGroupConfig(
                instance_count=instance_counts.android_x86_64_instances,
                instance_type=instance_type_names.android_x86_64_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_x86_64_ami", rib_config.LINUX_x86_64_AMI
                ),
                ebs_size=instance_ebs_sizes.android_instance_ebs_size_gb,
            ),
            linux_arm64_hosts=Ec2InstanceGroupConfig(
                instance_count=instance_counts.linux_arm64_instances,
                instance_type=instance_type_names.linux_arm64_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_arm64_ami", rib_config.LINUX_ARM64_AMI
                ),
                ebs_size=instance_ebs_sizes.linux_instance_ebs_size_gb,
            ),
            linux_x86_64_hosts=Ec2InstanceGroupConfig(
                instance_count=instance_counts.linux_x86_64_instances,
                instance_type=instance_type_names.linux_x86_64_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_x86_64_ami", rib_config.LINUX_x86_64_AMI
                ),
                ebs_size=instance_ebs_sizes.linux_instance_ebs_size_gb,
            ),
            linux_gpu_arm64_hosts=Ec2InstanceGroupConfig(
                instance_count=instance_counts.linux_gpu_arm64_instances,
                instance_type=instance_type_names.linux_gpu_arm64_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_gpu_arm64_ami", rib_config.LINUX_GPU_ARM64_AMI
                ),
                ebs_size=instance_ebs_sizes.linux_gpu_instance_ebs_size_gb,
            ),
            linux_gpu_x86_64_hosts=Ec2InstanceGroupConfig(
                instance_count=instance_counts.linux_gpu_x86_64_instances,
                instance_type=instance_type_names.linux_gpu_x86_64_instance_type_name,
                instance_ami=rib_aws_preferences.get(
                    "linux_gpu_x86_64_ami", rib_config.LINUX_GPU_x86_64_AMI
                ),
                ebs_size=instance_ebs_sizes.linux_gpu_instance_ebs_size_gb,
            ),
        )
        files.write_config(config)

        files.actuate_yaml_template(files.ansible_inventory_file, config.dict())

        rib_instance_tag = os.environ.get("RIB_INSTANCE_TAG", "")
        rib_container_info = docker_utils.get_container_info(
            "race-in-the-box" + rib_instance_tag
        )

        metadata = AwsEnvMetadata(
            rib_image=rib_container_info["image"],
            create_command=create_command,
            create_date=general_utils.get_current_time(),
            last_provision_command=None,
            last_provision_time=None,
            last_unprovision_command=None,
            last_unprovision_time=None,
        )

        aws_env = RibAwsEnv(config=config, files=files, metadata=metadata)
        aws_env._update_metadata(metadata)

    ###
    # Instance attributes
    ###

    config: AwsEnvConfig
    metadata: AwsEnvMetadata
    files: AwsEnvFiles

    def __init__(
        self, config: AwsEnvConfig, files: AwsEnvFiles, metadata: AwsEnvMetadata
    ) -> None:
        """
        Purpose:
            Initialize the AWS environment object
        Args:
            config: AWS environment configuration
            files: AWS environment files
            metadata: AWS environment metadata
        Return:
            N/A
        """

        self.config = config
        self.files = files
        self.metadata = metadata

        self._ssh_clients: Dict[str, paramiko.SSHClient] = {}

    ###
    # Internal helper methods
    ###

    def _connect_ssh_client(
        self,
        hostname: str,
        port: int,
        username: str,
    ) -> paramiko.SSHClient:
        """
        Purpose:
            Create, or return an already-existing, an SSH client to the specified remote host.

            If no client has yet been created for the specific username@hostname:port, or if the
            existing client is no longer connected, the client will be created.
        Args:
            hostname: Remote hostname (or IP address)
            port: SSH server port
            username: Remote username
        Return:
            SSH client
        """
        key = f"{username}@{hostname}:{port}"
        if (key not in self._ssh_clients) or not ssh_utils.check_ssh_client_connected(
            self._ssh_clients[key]
        ):
            self._ssh_clients[key] = ssh_utils.connect_ssh_client(
                hostname=hostname,
                port=port,
                ssh_key=self._ssh_key,
                username=username,
            )
        return self._ssh_clients[key]

    def _is_ec2_instances_cache_valid(
        self, instances: Mapping[str, Collection[str]]
    ) -> bool:
        """
        Purpose:
            Checks if the given cached instance details are valid.

            Only the cluster manager's IP address is verified to still be valid.
        Args:
            instances: Mapping of role to collections of IP addresses
        Return:
            True if instance details are still valid
        """
        cluster_manager_instances = instances.get(self.CLUSTER_MANAGER_ROLE)
        if cluster_manager_instances:
            cluster_manager_ip = cluster_manager_instances[0]
            try:
                # Use kibana as the test HTTP endpoint since there's no ping function readily
                # available (would require additional packages installed)
                result = requests.get(f"http://{cluster_manager_ip}:9200", timeout=0.05)
                return result.status_code == 200
            except Exception:
                return False
        return False

    def _get_ec2_instance_ips(
        self, force_refresh: bool = False, validate: bool = True
    ) -> Mapping[str, Collection[Ec2InstanceDetails]]:
        """
        Purpose:
            Get all EC2 instances in the running AWS environment.

            The instance details are cached. If the cluster manager IP address is still pingable,
            then it is assumed that the cache is valid. If no cached data exists or if the cluster
            manager IP is not pingable, a refresh is performed and a lookup of EC2 instances is
            performed.
        Args:
            force_refresh: Force a re-lookup of all EC2 instances from AWS
            validate: Validate cached IP address
        Return:
            Mapping of roles to collection of EC2 instance details
        """
        cache = self.files.read_cache()
        if (
            force_refresh
            or not cache.get("instances")
            or (validate and not self._is_ec2_instances_cache_valid(cache["instances"]))
        ):
            all_instances = aws_utils.get_ec2_instances(self._aws_session)

            instances = {}
            for role, _ in self._ec2_instance_roles:
                instances[role] = [
                    details["addresses"]["public"]["ip"]
                    for details in aws_utils.filter_ec2_instances_by_tags_and_state(
                        all_instances,
                        state="running",
                        tags={
                            "AwsEnvName": self.config.name,
                            "ClusterRole": role,
                        },
                    ).values()
                ]

            cache["instances"] = instances
            self.files.write_cache(cache)

        return cache["instances"]

    def _is_active(self) -> bool:
        """
        Purpose:
            Checks if the AWS environment is currently active in AWS
        Args:
            N/A
        Return:
            True if the AWS environment is active in AWS
        """
        active_envs = self.get_active_aws_envs()
        # Impossible be calling this instance method but think the env is unowned, so we only check
        # the active owned envs
        return self.config.name in active_envs.owned

    def _is_in_use(self) -> bool:
        """
        Purpose:
            Checks if the AWS environment is currently in use by any deployment; that is, there are
            containers currently running on any of the EC2 instances
        Args:
            N/A
        Return:
            True if the AWS environment is in use by a deployment
        """

        all_instances = aws_utils.get_ec2_instances(self._aws_session)
        instances = aws_utils.filter_ec2_instances_by_tags_and_state(
            all_instances,
            state="running",
            tags={"AwsEnvName": self.config.name},
        )
        for instance in instances.values():
            try:
                ssh_client = self._connect_ssh_client(
                    hostname=instance["addresses"]["public"]["ip"],
                    username=self.config.remote_username,
                    port=self._rib_config.RACE_AWS_MANAGE_SSH_PORT,
                )
                (stdout, _) = ssh_utils.run_ssh_command(
                    ssh_client,
                    "curl --unix-socket /var/run/docker.sock http://localhost/v1.41/containers/json",
                )
                for line in stdout:
                    if '"State":"running"' in line:
                        return True
            except Exception as err:
                logger.warning(f"Unable to establish SSH connection: {repr(err)}")

        return False

    def _update_metadata(self, metadata_vars: Mapping[str, Any]) -> None:
        """
        Purpose:
            Updates the metadata of the current AWS environment
        Args:
            metadata_vars: Dictionary of update metadata properties
        Return:
            N/A
        """

        allowed_keys = get_type_hints(AwsEnvMetadata).keys()
        for key, value in metadata_vars.items():
            if key not in allowed_keys:
                raise error_utils.RIB700(f"Attempt to set invalid metadata key: {key}")
            self.metadata[key] = value
        self.files.write_metadata(self.metadata)

    def _update_name(self, name: str) -> None:
        """
        Purpose:
            Updates all files where the AWS environment name is been written with the new name

            Files that require name updates include:
                * config
                * metadata
                * ansible dynamic inventory
        Args:
            name: New AWS environment name
        Return:
            N/A
        """

        old_name = self.config.name

        self.config.name = name
        self.files.write_config(self.config)

        self._update_metadata(
            {
                "create_command": self.metadata["create_command"].replace(
                    f" --name={old_name} ", f" --name={name} "
                )
            }
        )

        self.files.actuate_yaml_template(
            file_path=self.files.ansible_inventory_file,
            template_vars=self.config.dict(),
            template_file_path=rib_aws_env_files.template_ansible_inventory_file,
        )

    ###
    # Properties
    ###

    @cached_property
    def instance_counts(self) -> aws_topology_utils.InstanceCounts:
        """Instance counts in the env"""
        return aws_topology_utils.InstanceCounts(
            android_arm64_instances=self.config.android_arm64_hosts.instance_count,
            android_x86_64_instances=self.config.android_x86_64_hosts.instance_count,
            linux_gpu_arm64_instances=self.config.linux_gpu_arm64_hosts.instance_count,
            linux_gpu_x86_64_instances=self.config.linux_gpu_x86_64_hosts.instance_count,
            linux_arm64_instances=self.config.linux_arm64_hosts.instance_count,
            linux_x86_64_instances=self.config.linux_x86_64_hosts.instance_count,
        )

    @cached_property
    def _aws_session(self) -> "boto3.session.Session":
        """Connected AWS session"""
        return aws_utils.connect_aws_session_with_profile()

    @cached_property
    def _cloudformation_stacks(self) -> List[str]:
        """List of CloudFormation stack names"""
        stacks = [
            f"race-{self.config.name}-network",
            f"race-{self.config.name}-efs",
            f"race-{self.config.name}-{self.CLUSTER_MANAGER_ROLE}",
            f"race-{self.config.name}-{self.SERVICE_HOST_ROLE}",
        ]

        if self.config.linux_arm64_hosts.instance_count:
            stacks.append(f"race-{self.config.name}-{self.LINUX_ARM_NODE_HOST_ROLE}")
        if self.config.linux_x86_64_hosts.instance_count:
            stacks.append(f"race-{self.config.name}-{self.LINUX_x86_NODE_HOST_ROLE}")

        if self.config.linux_gpu_arm64_hosts.instance_count:
            stacks.append(
                f"race-{self.config.name}-{self.LINUX_GPU_ARM_NODE_HOST_ROLE}"
            )
        if self.config.linux_gpu_x86_64_hosts.instance_count:
            stacks.append(
                f"race-{self.config.name}-{self.LINUX_GPU_x86_NODE_HOST_ROLE}"
            )

        if self.config.android_arm64_hosts.instance_count:
            stacks.append(f"race-{self.config.name}-{self.ANDROID_ARM_NODE_HOST_ROLE}")
        if self.config.android_x86_64_hosts.instance_count:
            stacks.append(f"race-{self.config.name}-{self.ANDROID_x86_NODE_HOST_ROLE}")

        return stacks

    @cached_property
    def _ec2_instance_roles(self) -> List[Tuple[str, int]]:
        """List of EC2 instance cluster roles (name, count)"""
        roles = [
            (self.CLUSTER_MANAGER_ROLE, 1),
            (self.SERVICE_HOST_ROLE, 1),
        ]

        if self.config.linux_arm64_hosts.instance_count:
            roles.append(
                (
                    self.LINUX_ARM_NODE_HOST_ROLE,
                    self.config.linux_arm64_hosts.instance_count,
                )
            )
        if self.config.linux_x86_64_hosts.instance_count:
            roles.append(
                (
                    self.LINUX_x86_NODE_HOST_ROLE,
                    self.config.linux_x86_64_hosts.instance_count,
                )
            )

        if self.config.linux_gpu_arm64_hosts.instance_count:
            roles.append(
                (
                    self.LINUX_GPU_ARM_NODE_HOST_ROLE,
                    self.config.linux_gpu_arm64_hosts.instance_count,
                )
            )
        if self.config.linux_gpu_x86_64_hosts.instance_count:
            roles.append(
                (
                    self.LINUX_GPU_x86_NODE_HOST_ROLE,
                    self.config.linux_gpu_x86_64_hosts.instance_count,
                )
            )

        if self.config.android_arm64_hosts.instance_count:
            roles.append(
                (
                    self.ANDROID_ARM_NODE_HOST_ROLE,
                    self.config.android_arm64_hosts.instance_count,
                )
            )
        if self.config.android_x86_64_hosts.instance_count:
            roles.append(
                (
                    self.ANDROID_x86_NODE_HOST_ROLE,
                    self.config.android_x86_64_hosts.instance_count,
                )
            )

        return roles

    @cached_property
    def _efs_volumes(self) -> List[str]:
        """List of EFS volume names"""
        return [
            f"race-{self.config.name}-DataFileSystem",
        ]

    @cached_property
    def _rib_config(self) -> rib_utils.Config:
        """RiB configuration"""
        return rib_utils.load_race_global_configs()

    @cached_property
    def _ssh_key(self) -> None:
        """SSH key, loaded into memory"""
        return ssh_utils.get_rib_ssh_key()

    ###
    # Local disk/configuration manipulation methods
    ###

    def rename(self, name: str) -> None:
        """
        Purpose:
            Rename the AWS environment

            This operation is not forcible because it would be possible to leave orphaned resources
            running in AWS.
        Args:
            name: New AWS environment name
        Return:
            N/A
        """

        if self._is_active():
            raise error_utils.RIB724(self.config.name, "rename")

        self._update_name(name)

        # Move the files after updating the name
        new_files = AwsEnvFiles(name)
        shutil.move(self.files.base_dir, new_files.base_dir)

    def copy(self, name: str, force: bool = False) -> None:
        """
        Purpose:
            Creates a copy of the AWS environment

            This operation is forcible since the action is non-destructive, however we still check
            the status to make sure we're not in a weird state or corrupt before copying.
        Args:
            name: Destination AWS environment name
            force: Bypass precondition checks and force the operation
        Return:
            N/A
        """

        if not force and self._is_active():
            raise error_utils.RIB724(self.config.name, "copy")

        # Copy the files first, then update the name
        new_files = AwsEnvFiles(name)
        shutil.copytree(self.files.base_dir, new_files.base_dir)

        copied_env = self.get_aws_env_or_fail(name)
        copied_env._update_name(name)

    def remove(self, force: bool = False) -> None:
        """
        Purpose:
            Removes the AWS environment

            NOTE: it is not intended that CLI users can force a removal as this can
            leave orphaned resources running in AWS. The argument is supported in order
            to remove corrupted environments.
        Args:
            force: Bypass precondition checks and force the operation
        """

        if not force and self._is_active():
            raise error_utils.RIB724(self.config.name, "remove")

        shutil.rmtree(self.files.base_dir)

    ###
    # Status & info reporting methods
    ###

    def _get_cloudformation_status(self) -> StatusReport:
        """
        Purpose:
            Determines the status of all CloudFormation stacks in this AWS environment.
        Args:
            N/A
        Return:
            CloudFormation stack status report
        """

        all_stacks = aws_utils.get_cf_stacks(self._aws_session)

        children = {}
        for stack_name in self._cloudformation_stacks:
            if stack_name in all_stacks:
                children[stack_name] = StatusReport(
                    status=convert_cf_status_to_enum(all_stacks[stack_name]["status"]),
                    reason=all_stacks[stack_name]["status_reason"],
                )
            else:
                children[stack_name] = StatusReport(
                    status=AwsComponentStatus.NOT_PRESENT,
                )

        return create_parent_report(children)

    def _get_host_requirements_status(self, instance: Dict[str, Any]) -> StatusReport:
        """
        Purpose:
            Determines the readiness of the specified instance to participate in a RACE deployment
        Args:
            instance: EC2 instance data
        Return:
            Host requirements status report
        """

        children = {}

        try:
            # Verify SSH connectivity
            ssh_client = self._connect_ssh_client(
                hostname=instance["addresses"]["public"]["ip"],
                username=self.config.remote_username,
                port=self._rib_config.RACE_AWS_MANAGE_SSH_PORT,
            )
            children["ssh"] = StatusReport(status=AwsComponentStatus.READY)

            # Verify Docker Swarm is active
            (stdout, _) = ssh_utils.run_ssh_command(
                ssh_client, "docker info --format '{{.Swarm.LocalNodeState}}'"
            )
            if "inactive" in stdout:
                children["docker"] = StatusReport(
                    status=AwsComponentStatus.NOT_READY,
                    reason="Docker swarm is not active",
                )
            else:
                children["docker"] = StatusReport(status=AwsComponentStatus.READY)

            # Verify data mount point
            (stdout, _) = ssh_utils.run_ssh_command(ssh_client, "mountpoint /data")
            if "/data is a mountpoint" in stdout:
                children["data_mount"] = StatusReport(
                    status=AwsComponentStatus.READY,
                )
            else:
                children["data_mount"] = StatusReport(
                    status=AwsComponentStatus.NOT_READY
                )

        except (
            socket.timeout,
            paramiko.ssh_exception.NoValidConnectionsError,
        ) as _:
            children["ssh"] = StatusReport(
                status=AwsComponentStatus.NOT_READY,
                reason="SSH timeout/no connection",
            )
        except paramiko.ssh_exception.AuthenticationException as err:
            children["ssh"] = StatusReport(
                status=AwsComponentStatus.ERROR,
                reason=f"Invalid SSH credentials: {repr(err)}",
            )
        except Exception as err:
            children["ssh"] = StatusReport(
                status=AwsComponentStatus.ERROR,
                reason=f"Unhandled SSH error: {repr(err)}",
            )

        return create_parent_report(children)

    def _get_ec2_instance_status(self, instance: Dict[str, Any]) -> StatusReport:
        """
        Purpose:
            Determines the EC2 instance status
        Args:
            instance: EC2 instance data
        Return:
            EC2 instance status report
        """

        children = {
            "EC2_state": StatusReport(
                status=convert_ec2_status_to_enum(instance["state"]["Name"]),
            ),
        }

        if children["EC2_state"]["status"] == AwsComponentStatus.READY:
            children["host_requirements"] = self._get_host_requirements_status(instance)

        return create_parent_report(children)

    def _get_ec2_role_status(
        self, role: str, expected_count: int, all_instances: Dict[str, Any]
    ) -> StatusReport:
        """
            Determines the status of all EC2 instances in this AWS environment
            for the given cluster role
        Args:
            role: Cluster role
            expected_count: Expected number of instances
            all_instances: All EC2 instances found in AWS
        Return:
            EC2 instance role status report
        """

        instances = aws_utils.filter_ec2_instances_by_tags_and_state(
            all_instances,
            tags={
                "AwsEnvName": self.config.name,
                "ClusterRole": role,
            },
        )

        if len(instances) == 0:
            return StatusReport(status=AwsComponentStatus.NOT_PRESENT)

        children = {}
        for instance in instances.values():
            name = instance["addresses"]["public"]["dns"]
            if not name:
                name = instance["id"]
            children[name] = self._get_ec2_instance_status(instance)

        # Make sure we don't have extra instances running (READY or NOT_READY), but previously
        # stopped instances may still exist in a NOT_PRESENT state
        num_ready = len(
            [
                child
                for child in children.values()
                if child["status"] == AwsComponentStatus.READY
            ]
        )
        num_not_ready = len(
            [
                child
                for child in children.values()
                if child["status"] == AwsComponentStatus.NOT_READY
            ]
        )
        num_running = num_ready + num_not_ready
        reason = None
        if num_running > expected_count:
            status = AwsComponentStatus.ERROR
            reason = f"Expected {expected_count} instances but found {num_running}"
        elif num_ready == expected_count:
            status = AwsComponentStatus.READY
        else:
            status = get_parent_status([child["status"] for child in children.values()])

        return StatusReport(status=status, children=children, reason=reason)

    def _get_ec2_status(self) -> StatusReport:
        """
        Purpose:
            Determines the status of all EC2 instances in this AWS environment
        Args:
            N/A
        Return:
            EC2 instance status report
        """

        all_instances = aws_utils.get_ec2_instances(self._aws_session)

        children = {}
        for role, count in self._ec2_instance_roles:
            children[role] = self._get_ec2_role_status(
                role=role,
                expected_count=count,
                all_instances=all_instances,
            )

        return create_parent_report(children)

    def _get_efs_status(self) -> StatusReport:
        """
        Purpose:
            Determines the status of all EFS volumes in this AWS environment
        Args:
            N/A
        Return:
            EFS volume status report
        """

        all_volumes = aws_utils.get_efs_filesystems(self._aws_session)

        children = {}
        for efs_name in self._efs_volumes:
            if efs_name in all_volumes:
                children[efs_name] = StatusReport(
                    status=convert_efs_status_to_enum(all_volumes[efs_name]["state"]),
                )
            else:
                children[efs_name] = StatusReport(status=AwsComponentStatus.NOT_PRESENT)

        return create_parent_report(children)

    def get_status_report(self) -> AwsEnvStatus:
        """
        Purpose:
            Creates a status report for the AWS environment
        Args:
            N/A
        Return:
            AWS environment status report
        """
        components = AwsEnvComponentStatus(
            cloud_formation=self._get_cloudformation_status(),
            ec2_instance=self._get_ec2_status(),
            efs=self._get_efs_status(),
        )

        return AwsEnvStatus(
            status=get_parent_status(
                [child["status"] for child in components.values()]
            ),
            components=components,
        )

    def get_runtime_info(self) -> Dict[str, List[Ec2InstanceRuntimeInfo]]:
        """
        Purpose:
            Obtains runtime information about all instances in the AWS environment
        Args:
            N/A
        Return:
            Dictionary of instance roles to lists of instance runtime info
        """

        # Get running container status from all hosts in the environment
        all_container_results = self.run_remote_command(
            "curl --silent --unix-socket /var/run/docker.sock http://localhost/v1.41/containers/json",
        )

        all_instances = aws_utils.get_ec2_instances(self._aws_session)

        runtime_info = {}
        for role, _ in self._ec2_instance_roles:
            runtime_info[role] = []

            role_container_results = all_container_results.get(role, {})
            instances = aws_utils.filter_ec2_instances_by_tags_and_state(
                all_instances,
                state="running",
                tags={
                    "AwsEnvName": self.config.name,
                    "ClusterRole": role,
                },
            )
            for instance in instances.values():
                containers = {}
                try:
                    instance_container_results = role_container_results.get(
                        instance["addresses"]["public"]["ip"]
                    )
                    if (
                        instance_container_results
                        and instance_container_results["success"]
                    ):
                        stdout = "\n".join(instance_container_results["stdout"])
                        container_status_json = json.loads(stdout)
                        for container in container_status_json:
                            try:
                                container_name = container["Names"][0]
                                containers[container_name] = ContainerRuntimeInfo(
                                    state=container.get("State", "not running"),
                                    status=container.get("Status", ""),
                                    deployment_name=container.get("Labels", {}).get(
                                        "race.rib.deployment-name", ""
                                    ),
                                )
                            except Exception as err:
                                logger.warning(
                                    f"Unexpected JSON for container: {container}"
                                )
                except Exception as err:
                    logger.warning(
                        f"Bad container status on {instance['addresses']['public']['dns']}: {err}"
                    )

                runtime_info[role].append(
                    Ec2InstanceRuntimeInfo(
                        public_dns=instance["addresses"]["public"]["dns"],
                        public_ip=instance["addresses"]["public"]["ip"],
                        private_dns=instance["addresses"]["private"]["dns"],
                        private_ip=instance["addresses"]["private"]["ip"],
                        # Filter out low-level tags that begin with "aws:"
                        tags={
                            tag[0]: tag[1]
                            for tag in instance["tags"].items()
                            if not tag[0].startswith("aws:")
                        },
                        containers=containers,
                    )
                )

        return runtime_info

    def get_active_deployment(self) -> Optional[str]:
        """
        Purpose:
            Get the name of the active deployment, or None if no deployment is active on this host
            environment
        Args:
            N/A
        Return:
            Name of active deployment, if any
        """

        active_deployments = set()

        all_container_results = self.run_remote_command(
            "curl --silent --unix-socket /var/run/docker.sock http://localhost/v1.41/containers/json",
        )
        for instances in all_container_results.values():
            for instance_container_results in instances.values():
                if instance_container_results and instance_container_results["success"]:
                    stdout = "\n".join(instance_container_results["stdout"])
                    container_status_json = json.loads(stdout)
                    for container in container_status_json:
                        deployment_name = container.get("Labels", {}).get(
                            "race.rib.deployment-name", ""
                        )
                        if deployment_name:
                            active_deployments.add(deployment_name)

        if len(active_deployments) > 1:
            rib_mode = "aws"
            if active_deployments:
                rib_mode = list(active_deployments)[0].rib_mode
            raise error_utils.RIB324(active_deployments, rib_mode)

        return active_deployments.pop() if active_deployments else None

    ###
    # Environment manipulation methods
    ###

    def provision(
        self,
        provision_command: str,
        current_username: str,
        dry_run: bool = False,
        force: bool = False,
        timeout: int = 600,
        verbosity: int = 0,
    ) -> None:
        """
        Purpose:
            Creates and provisions all AWS resources necessary to host a RACE AWS deployment

            This will:
                * Create the VPC, subnets, and security groups
                * Create EFS volumes
                    * Data (configs)
                * Create EC2 instances
                    * A single cluster manager instance
                    * A single services host instance
                    * An Android node host instance autoscale group, if needed
                    * A GPU node host instance autoscale group, if needed
                    * A Linux node host instance autoscale group, if needed
        Args:
            provision_command: RiB command used to provision the AWS environment
            current_username: Username of the current RiB user
            dry_run: Perform dry-run of the provision operation
            force: Bypass precondition checks and force the operation
            timeout: Time in seconds to allow the operation to run before timing out
            verbosity: Playbook output verbosity
        Return:
            N/A
        """

        # Force the SSH key to be loaded (prompts the user for the password)
        _ = self._ssh_key

        if not force and self._is_in_use():
            raise error_utils.RIB723(self.config.name, "provision")

        self._update_metadata(
            {
                "last_provision_command": provision_command,
                "last_provision_time": general_utils.get_current_time(),
            }
        )

        ansible_utils.run_playbook(
            self.files.ansible_provision_playbook_file,
            dry_run=dry_run,
            inventory_file=self.files.ansible_inventory_file,
            num_forks=system_utils.get_cpu_count() * 4,
            playbook_vars={
                "awsEnvName": self.config.name,
                "awsEnvOwner": current_username,
                "awsRegion": self.config.region,
                "sshKeyName": self.config.ssh_key_name,
                "remoteUsername": self.config.remote_username,
                "managerIpAddress": f"{network_utils.get_public_ip()}/32",
                "clusterManagerType": self.config.cluster_manager.instance_type,
                "clusterManagerAmi": self.config.cluster_manager.instance_ami,
                "clusterManagerEbsSize": self.config.cluster_manager.ebs_size,
                "serviceHostType": self.config.service_host.instance_type,
                "serviceHostAmi": self.config.service_host.instance_ami,
                "serviceHostEbsSize": self.config.service_host.ebs_size,
                "linuxArmHostType": self.config.linux_arm64_hosts.instance_type,
                "linuxArmHostAmi": self.config.linux_arm64_hosts.instance_ami,
                "linuxArmHostEbsSize": self.config.linux_arm64_hosts.ebs_size,
                "linuxArmHostCount": self.config.linux_arm64_hosts.instance_count,
                "linuxX86HostType": self.config.linux_x86_64_hosts.instance_type,
                "linuxX86HostAmi": self.config.linux_x86_64_hosts.instance_ami,
                "linuxX86HostEbsSize": self.config.linux_x86_64_hosts.ebs_size,
                "linuxX86HostCount": self.config.linux_x86_64_hosts.instance_count,
                "linuxGpuArmHostType": self.config.linux_gpu_arm64_hosts.instance_type,
                "linuxGpuArmHostAmi": self.config.linux_gpu_arm64_hosts.instance_ami,
                "linuxGpuArmHostEbsSize": self.config.linux_gpu_arm64_hosts.ebs_size,
                "linuxGpuArmHostCount": self.config.linux_gpu_arm64_hosts.instance_count,
                "linuxGpuX86HostType": self.config.linux_gpu_x86_64_hosts.instance_type,
                "linuxGpuX86HostAmi": self.config.linux_gpu_x86_64_hosts.instance_ami,
                "linuxGpuX86HostEbsSize": self.config.linux_gpu_x86_64_hosts.ebs_size,
                "linuxGpuX86HostCount": self.config.linux_gpu_x86_64_hosts.instance_count,
                "androidArmHostType": self.config.android_arm64_hosts.instance_type,
                "androidArmHostAmi": self.config.android_arm64_hosts.instance_ami,
                "androidArmHostEbsSize": self.config.android_arm64_hosts.ebs_size,
                "androidArmHostCount": self.config.android_arm64_hosts.instance_count,
                "androidX86HostType": self.config.android_x86_64_hosts.instance_type,
                "androidX86HostAmi": self.config.android_x86_64_hosts.instance_ami,
                "androidX86HostEbsSize": self.config.android_x86_64_hosts.ebs_size,
                "androidX86HostCount": self.config.android_x86_64_hosts.instance_count,
            },
            remote_username=self.config.remote_username,
            ssh_key_name=self.files.ssh_key_file,
            timeout=timeout,
            verbosity=verbosity,
        )

        status_report = self.get_status_report()
        if status_report.status != AwsComponentStatus.READY:
            raise error_utils.RIB712(
                self.config.name,
                "provision",
                status_report.status,
                AwsComponentStatus.READY,
            )

    def unprovision(
        self,
        unprovision_command: str,
        dry_run: bool = False,
        force: bool = False,
        timeout: int = 600,
        verbosity: int = 0,
    ) -> None:
        """
        Purpose:
            Tear down an AWS environment.

            This will remove all EC2 instances, EFS volumes, and CloudFormation stacks in AWS.
        Args:
            unprovision_command: RiB command used to unprovision the AWS environment
            dry_run: Perform dry-run of the provision operation
            force: Bypass precondition checks and force the operation
            timeout: Time in seconds per stack to allow the operation to run before timing out
            verbosity: Playbook output verbosity
        """

        # Force the SSH key to be loaded (prompts the user for the password)
        _ = self._ssh_key

        if not force and self._is_in_use():
            raise error_utils.RIB723(self.config.name, "unprovision")

        self._update_metadata(
            {
                "last_unprovision_command": unprovision_command,
                "last_unprovision_time": general_utils.get_current_time(),
            }
        )

        ansible_utils.run_playbook(
            self.files.ansible_unprovision_playbook_file,
            dry_run=dry_run,
            inventory_file=self.files.ansible_inventory_file,
            num_forks=system_utils.get_cpu_count() * 4,
            playbook_vars={
                "awsEnvName": self.config.name,
                "awsRegion": self.config.region,
                "stackDeleteTimeout": timeout,
            },
            remote_username=self.config.remote_username,
            ssh_key_name=self.files.ssh_key_file,
            timeout=timeout * len(self._cloudformation_stacks),
            verbosity=verbosity,
        )

        status_report = self.get_status_report()
        if status_report.status != AwsComponentStatus.NOT_PRESENT:
            raise error_utils.RIB712(
                self.config.name,
                "unprovision",
                status_report.status,
                AwsComponentStatus.NOT_PRESENT,
            )

    ###
    # Remote execution methods
    ###

    def get_cluster_manager_ip(self) -> Optional[str]:
        """
        Purpose:
            Get the publically accessible IP address of the cluster manager for the AWS environment
        Args:
            N/A
        Return:
            Cluster manager instance public IP address, or None if the environment is not running
        """
        cluster_manager_instances = self._get_ec2_instance_ips().get(
            self.CLUSTER_MANAGER_ROLE
        )
        if cluster_manager_instances:
            return cluster_manager_instances[0]
        return None

    def run_playbook(
        self,
        dry_run: bool,
        playbook_file: str,
        playbook_vars: Dict[str, Any],
        timeout: int,
        verbosity: int,
    ) -> None:
        """
        Purpose:
            Execute an Ansible playbook on the AWS environment

            This is used by deployments using this AWS environment
        Args:
            dry_run: Perform dry-run of the playbook
            playbook_file: Playbook file to be executed
            playbook_vars: Extra variables to be set
            timeout: Time in seconds to allow the playbook to run
            verbosity: Playbook output verbosity
        """

        # Force the SSH key to be loaded (prompts the user for the password)
        _ = self._ssh_key

        ansible_utils.run_playbook(
            playbook_file,
            dry_run=dry_run,
            inventory_file=self.files.ansible_inventory_file,
            num_forks=system_utils.get_cpu_count() * 4,
            playbook_vars=playbook_vars,
            remote_username=self.config.remote_username,
            ssh_key_name=self.files.ssh_key_file,
            timeout=timeout,
            verbosity=verbosity,
        )

    def run_remote_command(
        self,
        command: str,
        check_exit_status: bool = False,
        print_stdout: bool = False,
        role: Optional[str] = None,
        timeout: int = 60,
    ) -> Dict[str, Dict[str, RemoteCommandResult]]:
        """
        Purpose:
            Executes a command on all remote instances as specified by the role.

            If the role is not specified, the command is run on all instances.

            If command is run on multiple instances, they will be executed in parallel.
        Args:
            command: Command to be executed
            check_exit_status: If true, verify command exits with a 0 exit code
            print_stdout: Enable printing of command to stdout of the local terminal (not
                recommended for parallel execution)
            role: Role of instance(s) on which to execute the command, or all instances if not set
            timeout: Time, in seconds, to allow the command to execute
        Return:
            Dictionary of role to dictionary of hostnames to command result, for example:
                ```
                {
                    "role-name": {
                        "instance-1-hostname": {
                            "success": True,
                            "stdout": [],
                            "stderr": [],
                        }
                    }
                }
                ```
        """

        roles = (
            [role] if role else [ec2_role[0] for ec2_role in self._ec2_instance_roles]
        )
        port = self._rib_config.RACE_AWS_MANAGE_SSH_PORT
        username = self.config.remote_username

        if role == self.BASTION_ROLE:
            # If role is bastion, we actually need the cluster manager on port 22
            roles = [self.CLUSTER_MANAGER_ROLE]
            port = 22
            username = "rib"

        instances = self._get_ec2_instance_ips()
        thread_executor = threading_utils.create_thread_executor()
        futures = {}
        for instance_role in roles:
            for instance_ip in instances.get(instance_role, []):
                futures[
                    (instance_role, instance_ip)
                ] = threading_utils.execute_function_in_thread(
                    thread_executor,
                    self._run_ssh_command,
                    kwargs={
                        "ssh_client": self._connect_ssh_client(
                            hostname=instance_ip,
                            username=username,
                            port=port,
                        ),
                        "command": command,
                        "check_exit_status": check_exit_status,
                        "print_stdout": print_stdout,
                        "timeout": timeout,
                    },
                )

        thread_results = threading_utils.get_threaded_function_results_as_completed(
            futures
        )
        results = {}
        for (job_role, job_hostname), job_return in thread_results[
            "return_values"
        ].items():
            # If the original request was for the bastion role, report cluster manager under bastion
            if role == self.BASTION_ROLE and job_role == self.CLUSTER_MANAGER_ROLE:
                job_role = self.BASTION_ROLE
            results.setdefault(job_role, {})
            results[job_role][job_hostname] = job_return

        return results

    @staticmethod
    def _run_ssh_command(
        ssh_client: paramiko.SSHClient,
        command: str,
        check_exit_status: bool,
        print_stdout: bool,
        timeout: int,
    ) -> RemoteCommandResult:
        """
        Purpose:
            Execute the given command using the given SSH client
        Args:
            ssh_client: SSH client
            command: Command to be executed
            check_exit_status: If true, verify command exits with a 0 exit code
            print_stdout: Enable printing of command to stdout of the local terminal
            timeout: Time, in seconds, to allow the command to execute
        """
        try:
            (stdout, stderr) = ssh_utils.run_ssh_command(
                ssh_client=ssh_client,
                command=command,
                timeout=timeout,
                print_stdout=print_stdout,
                check_exit_status=check_exit_status,
            )
            return RemoteCommandResult(
                success=True,
                stdout=stdout,
                stderr=stderr,
            )
        except Exception:
            return RemoteCommandResult(
                success=False,
                stdout=[],
                stderr=[],
            )

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

# Python Library Imports
from typing import List

# Local Library Imports
from rib.aws_env.rib_aws_env import RibAwsEnv
from rib.aws_env.rib_aws_env_status import Ec2InstanceRuntimeInfo
from rib.deployment.status.rib_deployment_status import RibDeploymentStatus, Require
from rib.utils import aws_topology_utils
from rib.utils import status_utils
from rib.utils.status_utils import StatusReport


class RibAwsDeploymentStatus(RibDeploymentStatus):
    """
    Purpose:
        Interface to handle status evaluation for a AWS deployment
    """

    def get_container_status_report(self) -> StatusReport:
        """
        Purpose:
            Get status of RACE containers. Relies on some deployment mode specific
            information
        Expected Args:
            N/A
        Expected Return:
            Container status_report
        """

        node_distribution = aws_topology_utils.read_distribution_from_file(
            self.deployment.paths.files["node_distribution"]
        )
        env_runtime_info = self.deployment._aws_env.get_runtime_info()

        role_reports = {}

        role_reports[
            RibAwsEnv.CLUSTER_MANAGER_ROLE
        ] = self._create_cluster_manager_role_container_status_report(
            instances=env_runtime_info.get(RibAwsEnv.CLUSTER_MANAGER_ROLE, [])
        )

        if node_distribution.android_arm64_instances:
            role_reports[
                RibAwsEnv.ANDROID_ARM_NODE_HOST_ROLE
            ] = self._create_node_host_role_container_status_report(
                instances=env_runtime_info.get(
                    RibAwsEnv.ANDROID_ARM_NODE_HOST_ROLE, []
                ),
                manifests=node_distribution.android_arm64_instances,
            )

        if node_distribution.android_x86_64_instances:
            role_reports[
                RibAwsEnv.ANDROID_x86_NODE_HOST_ROLE
            ] = self._create_node_host_role_container_status_report(
                instances=env_runtime_info.get(
                    RibAwsEnv.ANDROID_x86_NODE_HOST_ROLE, []
                ),
                manifests=node_distribution.android_x86_64_instances,
            )

        if node_distribution.linux_gpu_arm64_instances:
            role_reports[
                RibAwsEnv.LINUX_GPU_ARM_NODE_HOST_ROLE
            ] = self._create_node_host_role_container_status_report(
                instances=env_runtime_info.get(
                    RibAwsEnv.LINUX_GPU_ARM_NODE_HOST_ROLE, []
                ),
                manifests=node_distribution.linux_gpu_arm64_instances,
            )

        if node_distribution.linux_gpu_x86_64_instances:
            role_reports[
                RibAwsEnv.LINUX_GPU_x86_NODE_HOST_ROLE
            ] = self._create_node_host_role_container_status_report(
                instances=env_runtime_info.get(
                    RibAwsEnv.LINUX_GPU_x86_NODE_HOST_ROLE, []
                ),
                manifests=node_distribution.linux_gpu_x86_64_instances,
            )

        if node_distribution.linux_arm64_instances:
            role_reports[
                RibAwsEnv.LINUX_ARM_NODE_HOST_ROLE
            ] = self._create_node_host_role_container_status_report(
                instances=env_runtime_info.get(RibAwsEnv.LINUX_ARM_NODE_HOST_ROLE, []),
                manifests=node_distribution.linux_arm64_instances,
            )

        if node_distribution.linux_x86_64_instances:
            role_reports[
                RibAwsEnv.LINUX_x86_NODE_HOST_ROLE
            ] = self._create_node_host_role_container_status_report(
                instances=env_runtime_info.get(RibAwsEnv.LINUX_x86_NODE_HOST_ROLE, []),
                manifests=node_distribution.linux_x86_64_instances,
            )

        return StatusReport(
            status=status_utils.evaluate_grandparent_status(
                [child["status"] for child in role_reports.values()]
            ),
            children=role_reports,
        )

    def _get_external_services_status_report(self) -> StatusReport:
        """
        Purpose:
            Get status of external services (comms channels, artifact manager plugins)
        Args:
            N/A
        Return:
            External services status report
        """
        service_reports = {}

        for plugin_or_channel_id in self.deployment._external_services.keys():
            results = self.deployment._aws_env.run_remote_command(
                f"bash /home/{self.deployment._aws_env.config.remote_username}/external-services/{plugin_or_channel_id}/get_status_of_external_services.sh",
                check_exit_status=True,
                role=RibAwsEnv.SERVICE_HOST_ROLE,
            )
            if results.get(RibAwsEnv.SERVICE_HOST_ROLE, {}):
                success = (
                    list(results[RibAwsEnv.SERVICE_HOST_ROLE].values())
                    .pop()
                    .get("success", False)
                )
            else:
                success = False
            service_reports[plugin_or_channel_id] = StatusReport(
                status=status_utils.ServiceStatus.RUNNING
                if success
                else status_utils.ServiceStatus.NOT_RUNNING
            )

        return StatusReport(
            status=status_utils.evaluate_service_parent_status(
                [child["status"] for child in service_reports.values()]
            ),
            children=service_reports,
        )

    def _get_rib_services_status_report(self) -> StatusReport:
        """
        Purpose:
            Get status of RiB services (opentracing, orchestration, vpn)

            will call _get_rib_services_status_report_base with deployment-specific
            services + URLs depending on the class
        Args:
            N/A
        Return:
            RiB services status report
        """

        cluster_manager_ip = self.deployment._aws_env.get_cluster_manager_ip()
        if not cluster_manager_ip:
            return StatusReport(status=status_utils.ParentStatus.ALL_DOWN)

        return self._get_rib_services_status_report_base(
            cluster_manager_ip,
            [
                ("ElasticSearch", f"http://{cluster_manager_ip}:9200"),
                ("Kibana", f"http://{cluster_manager_ip}:5601"),
                ("Jaeger UI", f"http://{cluster_manager_ip}:16686"),
                ("File Server", f"http://{cluster_manager_ip}:3453"),
            ],
        )

    def do_expected_node_artifacts_exist(self, persona: str) -> bool:
        """
        Purpose:
            Check if artifacts exist for the node
        Args:
            persona: Node persona
        Return:
            True if all artifacts for the node exist
        """
        # AWS Mode expects plugin artifacts to be in the image
        # TODO: check for artifacts if fetch-plugins-on-start is enabled or
        # if node is a bootstrap node
        return True

    def is_down(self) -> bool:
        """
        Purpose:
            Checks if the deployment is completely down.
        Args:
            N/A
        Return:
            True if deployment is completely down
        """

        try:
            self.get_containers_that_match_status(
                action="",
                names=self.deployment.managed_personas + self.deployment.aux_services,
                container_status=[status_utils.ContainerStatus.NOT_PRESENT],
                require=Require.ALL,
                quiet=True,
            )
            return True
        except:
            return False

    def _create_cluster_manager_role_container_status_report(
        self,
        instances: List[Ec2InstanceRuntimeInfo],
    ) -> StatusReport:
        """
        Purpose:
            Creates a container status report for all hosts in the cluster manager role
        Args:
            instances: List of instance runtime info, including IP addresses and container status
        Return:
            Container status report for cluster manager hosts
        """

        instance_reports = {}

        # Should only contain one instance anyway, but written as a loop anyway just in case we end
        # up with multiple instances
        for instance in instances:
            instance_reports[
                instance["public_dns"]
            ] = self._create_cluster_manager_container_status_report(instance=instance)

        return StatusReport(
            status=status_utils.evaluate_grandparent_status(
                [child["status"] for child in instance_reports.values()]
            ),
            children=instance_reports,
        )

    def _create_cluster_manager_container_status_report(
        self, instance: Ec2InstanceRuntimeInfo
    ) -> StatusReport:
        """
        Purpose:
            Creates a container status report for the cluster manager
        Args:
            instance: Instance runtime info, including IP addresses and container status
        Return:
            Container status report for the cluster manager
        """

        container_reports = {}

        for aux_service in self.deployment.aux_services:
            # Have to look for aux service name as substring of the container name, because they
            # are deployed via docker swarm and so the name is "<stack>_<service>.1.<hash>"
            for container_name, container_state in instance["containers"].items():
                if (
                    container_state.get("deployment_name")
                    != self.deployment.config["name"]
                ):
                    continue
                if aux_service in container_name:
                    container_reports[aux_service] = StatusReport(
                        status=status_utils.evaluate_container_status(
                            state=container_state.get("state", "not running"),
                            status=container_state.get("status", ""),
                        )
                    )
                    break
            if not aux_service in container_reports:
                container_reports[aux_service] = StatusReport(
                    status=status_utils.ContainerStatus.NOT_PRESENT
                )

        return StatusReport(
            status=status_utils.evaluate_container_parent_status(
                [child["status"] for child in container_reports.values()]
            ),
            children=container_reports,
        )

    def _create_node_host_role_container_status_report(
        self,
        instances: List[Ec2InstanceRuntimeInfo],
        manifests: List[aws_topology_utils.NodeInstanceManifest],
    ) -> StatusReport:
        """
        Purpose:
            Creates a container status report for all hosts of a particular RACE node host role
        Args:
            instances: List of instance runtime info, including IP addresses and container status
            manifests: Node topology manifests for the role
        Return:
            Container status report for all hosts within the role
        """

        instances.sort(key=lambda i: i["public_dns"])

        instance_reports = {}

        for index, manifest in enumerate(manifests):
            try:
                instance = instances[index]
                instance_reports[
                    instance["public_dns"]
                ] = self._create_node_host_container_status_report(
                    instance=instance, manifest=manifest
                )
            except IndexError:
                instance_reports[f"missing-instance-{index}"] = StatusReport(
                    status=status_utils.ParentStatus.ALL_DOWN
                )

        return StatusReport(
            status=status_utils.evaluate_grandparent_status(
                [child["status"] for child in instance_reports.values()]
            ),
            children=instance_reports,
        )

    def _create_node_host_container_status_report(
        self,
        instance: Ec2InstanceRuntimeInfo,
        manifest: aws_topology_utils.NodeInstanceManifest,
    ) -> StatusReport:
        """
        Purpose:
            Creates a container status report for the given RACE node host
        Args:
            instance: Instance runtime info, including IP addresses and container status
            manifest: Node topology manifest for the role
        Return:
            Container status report for the host
        """

        container_reports = {}

        for persona in (
            manifest.android_clients
            + manifest.linux_gpu_clients
            + manifest.linux_clients
            + manifest.linux_gpu_servers
            + manifest.linux_servers
        ):
            container = instance["containers"].get(f"/race_nodes_{persona}_1")
            if (
                container
                and container.get("deployment_name") == self.deployment.config["name"]
            ):
                container_reports[persona] = StatusReport(
                    status=status_utils.evaluate_container_status(
                        state=container.get("state", "not running"),
                        status=container.get("status", ""),
                    )
                )
            else:
                container_reports[persona] = StatusReport(
                    status=status_utils.ContainerStatus.NOT_PRESENT
                )

        return StatusReport(
            status=status_utils.evaluate_container_parent_status(
                [child["status"] for child in container_reports.values()]
            ),
            children=container_reports,
        )

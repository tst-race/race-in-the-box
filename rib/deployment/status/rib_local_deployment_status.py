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
        TODO
"""

# Python Library Imports
import os
import subprocess

# Local Python Library Imports
from rib.deployment.status.rib_deployment_status import RibDeploymentStatus
from rib.utils.status_utils import StatusReport
from rib.utils import docker_utils, error_utils, status_utils


class RibLocalDeploymentStatus(RibDeploymentStatus):
    """
    Purpose:
        Interface to handle status evaluation for a local deployment
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
        container_reports = {}
        containers = docker_utils.get_deployment_container_status(
            self.deployment.config["name"]
        )

        for persona in self.deployment.managed_personas:
            container_reports[persona] = StatusReport(
                status=containers.get(persona, status_utils.ContainerStatus.NOT_PRESENT)
            )

        for service in self.deployment.aux_services:
            container_reports[service] = StatusReport(
                status=containers.get(service, status_utils.ContainerStatus.NOT_PRESENT)
            )

        return StatusReport(
            status=status_utils.evaluate_container_parent_status(
                [child["status"] for child in container_reports.values()]
            ),
            children=container_reports,
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
        for (
            plugin_or_channel_id,
            script_dir,
        ) in self.deployment._external_services.items():
            try:
                returncode = subprocess.call(
                    ["bash", f"{script_dir}/get_status_of_external_services.sh"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if returncode == 0:
                    service_reports[plugin_or_channel_id] = StatusReport(
                        status=status_utils.ServiceStatus.RUNNING
                    )
                else:
                    service_reports[plugin_or_channel_id] = StatusReport(
                        status=status_utils.ServiceStatus.NOT_RUNNING
                    )
            except Exception as err:
                service_reports[plugin_or_channel_id] = StatusReport(
                    status=status_utils.ServiceStatus.ERROR,
                    reason=error_utils.get_message(err),
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

        return self.deployment.status._get_rib_services_status_report_base(
            "rib-redis",
            [
                ("ElasticSearch", "http://elasticsearch:9200"),
                ("Kibana", "http://kibana:5601"),
                ("Jaeger UI", "http://jaeger-query:16686"),
                ("File Server", "http://rib-file-server:8080"),
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

        platform = self.deployment.config["nodes"][persona]["platform"]
        architecture = self.deployment.config["nodes"][persona]["architecture"]
        node_type = self.deployment.config["nodes"][persona]["node_type"]

        if architecture == "auto":
            # Can't verify for bridged devices
            return True

        for ta in self.deployment.paths.tas:
            if not os.listdir(
                self.deployment.paths.dirs[
                    self.deployment.paths.get_plugin_artifacts_ta_dir_key(
                        platform, architecture, node_type, ta
                    )
                ]
            ):
                # No artifacts exist
                return False
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

        # Deployment is completely down if there are no containers associated with the deployment
        return (
            len(
                docker_utils.get_deployment_container_status(
                    self.deployment.config["name"]
                )
            )
            == 0
        )

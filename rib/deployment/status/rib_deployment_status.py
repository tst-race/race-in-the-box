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
    Handle Status evaluation for a deployment
"""

# Python Library Imports
from abc import abstractmethod
import click
from datetime import datetime
from enum import auto
import logging
import os
import requests
import time
from typing import Iterable, List, Dict, Optional, Set, Tuple

# Local Python Library Imports
import rib.deployment.rib_deployment as rib_deployment
from rib.utils import error_utils, general_utils, redis_utils, status_utils
from rib.utils.status_utils import StatusReport

# Set up logger
logger = logging.getLogger(__name__)


disable_status_checks = os.environ.get("RIB_DISABLE_STATUS_CHECK", "").lower() in [
    "true",
    "yes",
    "1",
]


class Require(general_utils.PrettyEnum):
    """Whether all, any, or none of the requested nodes have to match status criteria"""

    # All requested nodes must match status criteria (will fail if not all match)
    ALL = auto()
    # Any requested nodes must match status criteria (will fail if none match)
    ANY = auto()
    # No required nodes (will never fail)
    NONE = auto()


class RibDeploymentStatus:
    """
    Purpose:
        Interface to handle status evaluation for a deployment
    """

    def __init__(self, deployment: "rib_deployment.RibDeployment") -> None:
        """
        Purpose:
            Initialize the object
        Args:
            deployment: Associated deployment instance
        Returns:
            N/A
        """
        self.deployment = deployment

        if disable_status_checks:
            logger.warning("Status checks are currently disabled, proceed cautiously")

    ###
    # "Get x that match status" Methods
    ##

    def get_containers_that_match_status(
        self,
        action: str,
        names: List[str],
        container_status: List[status_utils.ContainerStatus],
        require: Require = Require.ANY,
        force: bool = False,
        quiet: bool = False,
        verbosity: int = 1,  # defaulting to 1 to keep old functionality by default
    ) -> Set[str]:
        """
        Purpose:
            Get containers in the deployment matching the given status criteria,
            limited to the given subset of the deployment's containers.
        Args:
            action: Description of the action being executed
            names: list of candidate container names
            container_status: List of qualifying container status
            require: Raise an error if the matching containers don't meet the requirement
            force: Bypass all status checks
            quiet: Disable logging of matching/unmatching containers (e.g., when part of a loop)
            verbosity: set level of verbosity
        Return:
            List of matching containers
        Raises:
            error_utils.RIB331: if no containers match the status criteria
                when require is ANY
            error_utils.RIB342: if any container doesn't match the status criteria
                when require is ALL
        """

        matching_containers = set()

        if force or disable_status_checks:
            matching_containers = set(names)
        else:
            not_matching_containers = {}
            all_reports = status_utils.flatten(
                self.get_container_status_report().get("children", {})
            )

            for name in names:
                container_status_report = all_reports.get(
                    name, {"status": status_utils.ContainerStatus.NOT_PRESENT}
                )
                if container_status_report["status"] not in container_status:
                    not_matching_containers[name] = container_status_report
                    continue
                matching_containers.add(name)

            if not_matching_containers and require == Require.ALL:
                # Since at least one of the containers is not in the correct state, raise an error
                raise error_utils.RIB342(
                    deployment_name=self.deployment.config["name"],
                    rib_mode=self.deployment.rib_mode,
                    action=action,
                    reasons={
                        name: report["status"]
                        for name, report in not_matching_containers.items()
                    },
                )

            if not_matching_containers and not quiet:
                logger.warning(f"Unable to {action} the requested containers:")
                status_utils.print_status_report(
                    detail_level=0,
                    details=not_matching_containers,
                    printer=logger.warning,
                )

        if require == Require.ANY and not matching_containers:
            # Since none of the containers are in the correct state, raise an error
            raise error_utils.RIB331(
                deployment_name=self.deployment.config["name"],
                rib_mode=self.deployment.rib_mode,
                action=action,
            )

        if not quiet:
            logger.debug(
                f"Will {action} the following {len(matching_containers)} containers:"
            )
            max_log_output = 25 if verbosity < 1 else None
            log_line_count = 0
            for name in sorted(matching_containers):
                log_line_count += 1
                if max_log_output and log_line_count >= max_log_output:
                    logger.debug(f"\t...")
                    break
                logger.debug(f"\t{name}")

            logger.debug("")

        return matching_containers

    def get_nodes_that_match_status(
        self,
        action: str,
        personas: Optional[List[str]] = None,
        app_status: Optional[List[status_utils.AppStatus]] = None,
        daemon_status: Optional[List[status_utils.DaemonStatus]] = None,
        race_status: Optional[List[status_utils.RaceStatus]] = None,
        configs_status: Optional[List[status_utils.ConfigsStatus]] = None,
        etc_status: Optional[List[status_utils.EtcStatus]] = None,
        artifacts_status: Optional[List[status_utils.ArtifactsStatus]] = None,
        require: Require = Require.ANY,
        offline: bool = False,
        force: bool = False,
        quiet: bool = False,
        verbosity: int = 1,  # defaulting to 1 to keep old functionality by default
    ) -> Set[str]:
        """
        Purpose:
            Gets nodes in the deployment matching the given status criteria, optionally
            limited to a subset of the deployment's nodes.
        Args:
            action: Description of the action being executed. Only used for logging and error reporting.
            personas: Optional list of candidate personas (if None, all nodes in the deployment are
                candidates)
            app_status: Optional list of qualifying app status (if None, any app status will match)
            daemon_status: Optional list of qualifying daemon status (if None, any daemon status
                will match)
            race_status:  Optional list of qualifying race status (if None, any race status will match)
            configs_status:  Optional list of qualifying config status (if None, any config status will match)
            etc_status:  Optional list of qualifying etc status (if None, any etc status will match)
            artifacts_status:  Optional list of qualifying artifacts status (if None, any artifacts status will match)
            require: Raise an error if the matching containers don't meet the requirement
            offline: Only perform offline status checks (i.e., expect that node is down, do not
                include runtime status)
            force: Bypass all status checks
            quiet: Disable logging of matching/unmatching nodes (e.g., when part of a loop)
            verbosity: set level of verbosity
        Return:
            List of matching node personas
        Raises:
            error_utils.RIB331: if no nodes match the status criteria
                when require is ANY
            error_utils.RIB342: if any node doesn't match the status criteria
                when require is ALL
        """

        personas_to_query = personas or self.deployment.all_personas
        matching_nodes = set()

        if force or disable_status_checks:
            matching_nodes = set(personas_to_query)
        else:
            not_matching_nodes = {}

            for persona in personas_to_query:
                if (
                    app_status
                    or daemon_status
                    or race_status
                    or configs_status
                    or etc_status
                    or artifacts_status
                ):
                    node_status = self._get_node_status_report(persona, offline=offline)
                    if (
                        daemon_status
                        and node_status["children"]["daemon"]["status"]
                        not in daemon_status
                    ):
                        not_matching_nodes[persona] = node_status
                        continue
                    if (
                        app_status
                        and node_status["children"]["app"]["status"] not in app_status
                    ):
                        not_matching_nodes[persona] = node_status
                        continue
                    if (
                        race_status
                        and node_status["children"]["race"]["status"] not in race_status
                    ):
                        not_matching_nodes[persona] = node_status
                        continue
                    if (
                        configs_status
                        and node_status["children"]["configs"]["status"]
                        not in configs_status
                    ):
                        not_matching_nodes[persona] = node_status
                        continue
                    if (
                        etc_status
                        and node_status["children"]["etc"]["status"] not in etc_status
                    ):
                        not_matching_nodes[persona] = node_status
                        continue
                    if (
                        artifacts_status
                        and node_status["children"]["artifacts"]["status"]
                        not in artifacts_status
                    ):
                        not_matching_nodes[persona] = node_status
                        continue

                matching_nodes.add(persona)

            if not_matching_nodes and require == Require.ALL:
                # Since at least one of the nodes is not in the correct state, raise an error
                raise error_utils.RIB342(
                    deployment_name=self.deployment.config["name"],
                    rib_mode=self.deployment.rib_mode,
                    action=action,
                    reasons={
                        name: report["status"]
                        for name, report in not_matching_nodes.items()
                    },
                )

            if not_matching_nodes and not quiet:
                logger.warning(f"Unable to {action} the requested nodes:")
                status_utils.print_status_report(
                    detail_level=0,
                    details=not_matching_nodes,
                    printer=logger.warning,
                )

        if require == Require.ANY and not matching_nodes:
            # Since none of the nodes are in the correct state, raise an error
            raise error_utils.RIB331(
                deployment_name=self.deployment.config["name"],
                rib_mode=self.deployment.rib_mode,
                action=action,
            )

        if not quiet:
            logger.debug(f"Will {action} the following {len(matching_nodes)} nodes:")
            max_log_output = 25 if verbosity < 1 else None
            log_line_count = 0
            for name in sorted(matching_nodes):
                log_line_count += 1
                if max_log_output and log_line_count >= max_log_output:
                    logger.debug(f"\t...")
                    break
                logger.debug(f"\t{name}")
            logger.debug("")

        return matching_nodes

    ###
    # "Wait for status" Methods
    ##

    def wait_for_services_to_match_status(
        self,
        action: str,
        parent_status: List[status_utils.ParentStatus],
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Wait until the services for the deployment match the given status criteria,
            up to the given timeout threshold.
        Args:
            action: Description of the action being executed
            parent_status: List of qualifying service parent status
            timeout: Time in seconds before raising an error
        Raises:
            error_utils.RIB332: when services fail to transition to running state within the
            timeout threshold
        """
        if disable_status_checks:
            logger.warning(
                f"Status checks disabled, not waiting for services to {action}"
            )
            return

        click.echo(f"Waiting for services to {action}...", nl=False)
        command_run_time = datetime.now()
        while True:
            status_report = self.get_services_status_report()
            if status_report["status"] in parent_status:
                click.echo("done")
                break

            elapsed_secs = (datetime.now() - command_run_time).seconds
            if elapsed_secs > timeout:
                # TODO use a different error
                raise error_utils.RIB332(
                    deployment_name=self.deployment.config["name"],
                    rib_mode=self.deployment.rib_mode,
                    action=action,
                )

            time.sleep(1)
            click.echo(".", nl=False)

    def wait_for_containers_to_match_status(
        self,
        action: str,
        names: List[str],
        container_status: List[status_utils.ContainerStatus],
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Wait until the specified set of nodes match the given state criteria, up to
            the given timeout threshold.
        Args:
            action: Description of the action being executed
            names: List of container names to check
            container_status: List of qualifying container status
            timeout: Time in seconds before raising an error
        Raises:
            error_utils.RIB332: when nodes fail to transition to expected state within
                timeout threshold
        """
        if disable_status_checks:
            logger.warning(
                f"Status checks disabled, not waiting for containers to {action}"
            )
            return

        click.echo(f"Waiting for {len(names)} containers to {action}...", nl=False)
        command_run_time = datetime.now()
        while True:
            matching_containers = self.get_containers_that_match_status(
                action=action,
                names=names,
                container_status=container_status,
                require=Require.NONE,
                quiet=True,
            )

            if set(names) == set(matching_containers):
                click.echo("done")
                break

            elapsed_secs = (datetime.now() - command_run_time).seconds
            if elapsed_secs > timeout:
                raise error_utils.RIB332(
                    deployment_name=self.deployment.config["name"],
                    rib_mode=self.deployment.rib_mode,
                    action=action,
                    info=set(names) - set(matching_containers),
                )

            if elapsed_secs and elapsed_secs % 30 == 0:
                click.echo(
                    f"\nWaiting for {len(names) - len(matching_containers)} containers to {action}...",
                    nl=False,
                )

            time.sleep(1)
            click.echo(".", nl=False)

    def wait_for_nodes_to_match_status(
        self,
        action: str,
        personas: List[str],
        app_status: Optional[List[status_utils.AppStatus]] = None,
        daemon_status: Optional[List[status_utils.DaemonStatus]] = None,
        race_status: Optional[List[status_utils.RaceStatus]] = None,
        configs_status: Optional[List[status_utils.ConfigsStatus]] = None,
        etc_status: Optional[List[status_utils.EtcStatus]] = None,
        timeout: int = 120,
    ) -> None:
        """
        Purpose:
            Wait until the specified set of nodes match the given state criteria, up to
            the given timeout threshold.
        Args:
            action: Description of the action being executed. Only used for logging and error reporting.
            personas: List of node personas to check
            app_status: Optional list of expected app status (if None, any app status will match)
            daemon_status: Optional list of expected daemon status (if None, any daemon status
                will match)
            race_status: Optional list of expected race status (if None, any race status will match)
            timeout: Time in seconds before raising an error
        Raises:
            error_utils.RIB332: when nodes fail to transition to expected state within
                timeout threshold
        """
        if disable_status_checks:
            logger.warning(f"Status checks disabled, not waiting for nodes to {action}")
            return

        if not personas:
            return

        click.echo(f"Waiting for {len(personas)} nodes to {action}...", nl=False)
        command_run_time = datetime.now()
        how_often_to_print_waiting_status_in_seconds = 30
        waiting_status_print_counter = 1
        while True:
            matching_nodes = self.get_nodes_that_match_status(
                action=action,
                personas=personas,
                daemon_status=daemon_status,
                app_status=app_status,
                race_status=race_status,
                configs_status=configs_status,
                etc_status=etc_status,
                require=Require.NONE,
                quiet=True,
            )

            if set(personas) == set(matching_nodes):
                click.echo("done")
                break

            elapsed_secs = (datetime.now() - command_run_time).seconds
            if elapsed_secs > timeout:
                personas_in_wrong_state = set(personas) - set(matching_nodes)
                info = [
                    f"{persona}: {self._get_node_status_report(persona)['status']}"
                    for persona in sorted(personas_in_wrong_state)
                ]
                raise error_utils.RIB332(
                    deployment_name=self.deployment.config["name"],
                    rib_mode=self.deployment.rib_mode,
                    action=action,
                    info=info,
                )

            if elapsed_secs >= (
                how_often_to_print_waiting_status_in_seconds
                * waiting_status_print_counter
            ):
                waiting_status_print_counter += 1
                click.echo(
                    f"\nWaiting for {len(personas) - len(matching_nodes)} nodes to {action}...",
                    nl=False,
                )

            time.sleep(1)
            click.echo(".", nl=False)

    def get_node_os_details(
        self,
        persona: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Purpose:
            Fetch the current set of OS details posted by the given node's node-daemon instance
        Args:
            persona: The node personas for which OS details are to be fetched
        """
        try:
            daemon_status_details = (
                self.deployment.race_node_interface.get_daemon_status(persona)
            )
        except Exception:
            daemon_status_details = {"is_error": True}

        nodePlatform = daemon_status_details.get("nodePlatform", None)
        nodeArch = daemon_status_details.get("nodeArchitecture", None)
        return (nodePlatform, nodeArch)

    ###
    # Status Reports
    ###

    @abstractmethod
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

    @abstractmethod
    def _get_external_services_status_report(self) -> StatusReport:
        """
        Purpose:
            Get status of external services (comms channels, artifact manager plugins)
        Args:
            N/A
        Return:
            External services status report
        """

    @abstractmethod
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

    def get_services_status_report(self) -> StatusReport:
        """
        Purpose:
            Get status of RACE Services (opentracing, orchestration, external services, etc.).
        Args:
            N/A
        Return:
            Services status report
        """

        service_reports = {}
        external_service_report = self._get_external_services_status_report()
        if external_service_report is not None:
            service_reports["External Services"] = external_service_report
        service_reports["RiB"] = self._get_rib_services_status_report()

        return StatusReport(
            status=status_utils.evaluate_grandparent_status(
                [child["status"] for child in service_reports.values()]
            ),
            children=service_reports,
        )

    def get_app_status_report(self, nodes: Optional[List[str]] = None) -> StatusReport:
        """
        Purpose:
            Get status of RACE apps. This should be common for all deployments
        Expected Args:
            nodes ( Optional[List[str]]) the nodes to get status for
        Expected Return:
            status_report (StatusReport)
        """

        if nodes:
            nodes = self.deployment.get_nodes_from_regex(nodes)
        else:
            nodes = self.deployment.all_personas
        children = self._get_node_status_reports(nodes)
        return StatusReport(
            status=status_utils.evaluate_node_parent_status(
                [child["status"] for child in children.values()]
            ),
            children=children,
        )

    def _get_rib_services_status_report_base(
        self,
        redis_host: str,
        service_checks: List[Tuple[str, str]],
    ) -> StatusReport:
        """
        Purpose:
            Get status of RiB services (opentracing, orchestration, vpn)
        Args:
            redis_host: the hostname of the rib-redis service to get status of
            service_checks: Tuple of service names and URLs to poll to connectivity
        Return:
            RiB services status report
        """
        service_reports = {}

        for service, http_url in service_checks:
            try:
                result = requests.get(http_url)
                if result.status_code != 200:
                    service_reports[service] = StatusReport(
                        status=status_utils.ServiceStatus.NOT_RUNNING,
                        reason=f"HTTP status code {result.status_code}",
                    )
                else:
                    service_reports[service] = StatusReport(
                        status=status_utils.ServiceStatus.RUNNING
                    )
            except requests.ConnectionError:
                service_reports[service] = StatusReport(
                    status=status_utils.ServiceStatus.NOT_RUNNING
                )

        redis_client = redis_utils.create_redis_client(redis_host)
        if redis_client and redis_utils.is_connected(redis_client):
            service_reports["Redis"] = StatusReport(
                status=status_utils.ServiceStatus.RUNNING
            )
        else:
            service_reports["Redis"] = StatusReport(
                status=status_utils.ServiceStatus.NOT_RUNNING
            )

        return StatusReport(
            status=status_utils.evaluate_service_parent_status(
                [child["status"] for child in service_reports.values()]
            ),
            children=service_reports,
        )

    def _get_node_status_reports(
        self, personas: Iterable[str]
    ) -> Dict[str, StatusReport]:
        """
        Purpose:
            Get node status reports for all specified personas
        Args:
            personas: List of node personas
        Return:
            Dictionary of personas to status reports
        """
        return {persona: self._get_node_status_report(persona) for persona in personas}

    def _get_node_status_report(
        self, persona: str, offline: bool = False
    ) -> StatusReport:
        """
        Purpose:
            Get node status report for a single node
        Args:
            persona: Node persona
            offline: Only perform offline status checks (i.e., expect that node is down, do not
                include runtime status)
        Return:
            Node status report
        """

        daemon_status_reason = None
        app_status_reason = None
        race_status_reason = None
        configs_status_reason = None
        etc_status_reason = None
        artifacts_status_reason = None

        # Info from RiB File System
        expected_artifacts_exist = self.do_expected_node_artifacts_exist(persona)
        expected_artifact_tars_exists = self.do_expected_node_artifacts_archives_exist(
            persona
        )
        config_gen_success = self.did_config_gen_succeed()
        etc_tar_name = self.deployment.get_etc_tar_name(persona=persona)
        configs_tar_name = self.deployment.get_configs_tar_name(persona=persona)
        etc_tar_exists = os.path.isfile(
            f"{self.deployment.paths.dirs['etc']}/{etc_tar_name}"
        )
        configs_tar_exists = os.path.isfile(
            f"{self.deployment.paths.dirs['race_configs']}/{configs_tar_name}"
        )

        # Info from RiB File Server
        etc_tar_pushed = False
        configs_tar_pushed = False
        try:
            etc_tar_pushed = self.deployment.file_server_client.is_file_on_file_server(
                etc_tar_name
            )
        except Exception:
            pass
        try:
            configs_tar_pushed = (
                self.deployment.file_server_client.is_file_on_file_server(
                    configs_tar_name
                )
            )
        except Exception:
            pass

        # Info from the Node
        daemon_status_details = {}
        app_status_details = {}
        try:
            daemon_status_details = (
                self.deployment.race_node_interface.get_daemon_status(persona)
            )
        except Exception:
            daemon_status_details = {"is_error": True}
        try:
            app_status_details = self.deployment.race_node_interface.get_app_status(
                persona
            )
        except Exception:
            app_status_details = {"is_error": True}

        # Determine Statuses
        daemon_status, daemon_status_reason = (
            self.get_daemon_status(daemon_status_details)
            if not offline
            else (status_utils.DaemonStatus.NOT_REPORTING, None)
        )
        artifacts_status, artifacts_status_reason = self.get_artifacts_status(
            expected_artifacts_exist,
            expected_artifact_tars_exists,
        )
        configs_status, configs_status_reason = self.get_configs_status(
            config_gen_success,
            configs_tar_exists,
            configs_tar_pushed,
            daemon_status_details if not offline else None,
            app_status_details if not offline else None,
        )
        app_status, app_status_reason = (
            self.get_app_status(daemon_status_details, app_status_details)
            if not offline
            else (status_utils.AppStatus.NOT_REPORTING, None)
        )
        race_status, race_status_reason = (
            self.get_race_status(app_status_details)
            if not offline
            else (status_utils.RaceStatus.NOT_REPORTING, None)
        )
        etc_status, etc_status_reason = self.get_etc_status(
            config_gen_success,
            etc_tar_exists,
            etc_tar_pushed,
            daemon_status_details if not offline else None,
            app_status_details if not offline else None,
        )

        return StatusReport(
            status=status_utils.evaluate_node_status(
                daemon_status,
                app_status,
                race_status,
                configs_status,
                etc_status,
                artifacts_status,
            ),
            children={
                "daemon": StatusReport(
                    status=daemon_status, reason=daemon_status_reason
                ),
                "artifacts": StatusReport(
                    status=artifacts_status, reason=artifacts_status_reason
                ),
                "app": StatusReport(status=app_status, reason=app_status_reason),
                "race": StatusReport(status=race_status, reason=race_status_reason),
                "configs": StatusReport(
                    status=configs_status, reason=configs_status_reason
                ),
                "etc": StatusReport(status=etc_status, reason=etc_status_reason),
            },
        )

    ###
    # Individual Status Type Evaluations
    ##

    def get_artifacts_status(
        self,
        expected_artifacts_exist: bool,
        expected_artifact_tars_exists: bool,
    ) -> Tuple[status_utils.ArtifactsStatus, str]:
        artifacts_status_reason = None
        if not expected_artifacts_exist:
            # If no expected artifacts, expected_artifacts_exist will be True
            artifacts_status = status_utils.ArtifactsStatus.ERROR
            artifacts_status_reason = (
                "Artifacts for the node are not in the Rib file system but should be"
            )
        elif not expected_artifact_tars_exists:
            artifacts_status = status_utils.ArtifactsStatus.ARTIFACTS_EXIST
        else:
            artifacts_status = status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST
        return (artifacts_status, artifacts_status_reason)

    def get_daemon_status(
        self, daemon_status_details
    ) -> Tuple[status_utils.DaemonStatus, str]:
        daemon_status_reason = None
        daemon_status = status_utils.DaemonStatus.UNKNOWN
        if daemon_status_details.get("is_error", False):
            daemon_status = status_utils.DaemonStatus.ERROR
            daemon_status_reason = "Unexpectedly unable to get daemon status"
        elif not daemon_status_details.get("is_alive", False):  # daemon isn't alive
            daemon_status = status_utils.DaemonStatus.NOT_REPORTING
        elif daemon_status_details.get("dnsSuccessful", False):
            daemon_status = status_utils.DaemonStatus.RUNNING
        else:
            daemon_status = status_utils.DaemonStatus.ERROR
            daemon_status_reason = "DNS lookups are failing on node"

        return (daemon_status, daemon_status_reason)

    def get_configs_status(
        self,
        config_gen_success,
        configs_tar_exists,
        configs_tar_pushed,
        daemon_status_details,
        app_status_details,
    ) -> Tuple[status_utils.ConfigsStatus, str]:
        configs_status_reason = None
        if not config_gen_success:
            configs_status = status_utils.ConfigsStatus.ERROR_CONFIG_GEN_FAILED
            configs_status_reason = (
                "Network Manager Config Gen status file not found or reporting Error"
            )
        else:
            configs_status = status_utils.ConfigsStatus.CONFIG_GEN_SUCCESS

        if configs_tar_exists:
            configs_status = status_utils.ConfigsStatus.CONFIGS_TAR_EXISTS
        if configs_tar_pushed:
            configs_status = status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED

        if daemon_status_details and daemon_status_details.get(
            "is_alive", False
        ):  # daemon is alive
            # Configs can either be in the configs tar or extracted
            if daemon_status_details.get("configsPresent", False):
                configs_status = status_utils.ConfigsStatus.DOWNLOADED_CONFIGS

                configs_deployment_name = daemon_status_details.get("deployment", None)
                if not configs_deployment_name:
                    configs_status = status_utils.ConfigsStatus.ERROR
                    configs_status_reason = "No deployment associated with RACE configs"
                elif configs_deployment_name != self.deployment.config["name"]:
                    configs_status = status_utils.ConfigsStatus.ERROR
                    configs_status_reason = f"Configs from wrong deployment present: {configs_deployment_name}"

            # Extracted status overrides Downloaded status because extracted
            # configs will be used
            if daemon_status_details.get("configsExtracted", False):
                configs_status = status_utils.ConfigsStatus.EXTRACTED_CONFIGS
            # TODO: add deployment name verification

            if app_status_details.get("is_alive", False):
                sdk_status_detail = app_status_details.get("RaceStatus", None)
                if sdk_status_detail:
                    if not sdk_status_detail.get("validConfigs", False):
                        configs_status = (
                            status_utils.ConfigsStatus.ERROR_INVALID_CONFIGS
                        )

        return (configs_status, configs_status_reason)

    def get_etc_status(
        self,
        config_gen_success,
        etc_tar_exists,
        etc_tar_pushed,
        daemon_status_details,
        app_status_details,
    ) -> Tuple[status_utils.ConfigsStatus, str]:
        etc_status_reason = None
        if not config_gen_success:
            etc_status = status_utils.EtcStatus.ERROR_CONFIG_GEN_FAILED
            etc_status_reason = (
                "Network Manager Config Gen status file not found or reporting Error"
            )
        else:
            etc_status = status_utils.EtcStatus.CONFIG_GEN_SUCCESS

        if etc_tar_exists:
            etc_status = status_utils.EtcStatus.ETC_TAR_EXISTS
        if etc_tar_pushed:
            etc_status = status_utils.EtcStatus.ETC_TAR_PUSHED

        if daemon_status_details and daemon_status_details.get(
            "is_alive", False
        ):  # daemon is alive
            if daemon_status_details.get("jaegerConfigExists", False):
                etc_status = status_utils.EtcStatus.READY
            # TODO: add deployment name verification
            # TODO: What if invalid user-responses.json causes crash?

        return (etc_status, etc_status_reason)

    def get_app_status(
        self, daemon_status_details, app_status_details
    ) -> Tuple[status_utils.AppStatus, str]:
        app_status_reason = None
        if not daemon_status_details.get("is_alive", False):  # daemon isn't alive
            app_status = status_utils.AppStatus.NOT_REPORTING
        elif not daemon_status_details.get("installed", False):
            app_status = status_utils.AppStatus.NOT_INSTALLED
        elif app_status_details.get("is_error", False):
            app_status = status_utils.AppStatus.ERROR
            app_status_reason = "Unexpectedly unable to get app status"
        elif not app_status_details.get("is_alive", False):
            app_status = status_utils.AppStatus.NOT_RUNNING
        else:
            app_status = status_utils.AppStatus.RUNNING
        return (app_status, app_status_reason)

    def get_race_status(
        self, app_status_details
    ) -> Tuple[status_utils.RaceStatus, str]:
        race_status_reason = None
        race_status_detail = app_status_details.get("RaceStatus", None)
        if not race_status_detail or not app_status_details.get("is_alive", False):
            race_status = status_utils.RaceStatus.NOT_REPORTING
        else:
            if not race_status_detail.get("validConfigs", False):
                race_status = status_utils.RaceStatus.NOT_INITIALIZED

            elif (
                race_status_detail.get("network-manager-status", "")
                == status_utils.PLUGIN_STATUS_READY
            ):
                race_status = status_utils.RaceStatus.RUNNING
            else:
                race_status = status_utils.RaceStatus.NETWORK_MANAGER_NOT_READY
        return (race_status, race_status_reason)

    @abstractmethod
    def is_down(self) -> bool:
        """
        Purpose:
            Checks if the deployment is completely down.
        Args:
            N/A
        Return:
            True if deployment is completely down
        """

    def verify_deployment_is_down(
        self, action: str, force: bool = False, forcible: bool = False
    ) -> None:
        """
        Purpose:
            Verify that the deployment is completely down.
        Args:
            action: Description of the action being executed
            force: Bypass all status checks
        Return:
            N/A
        Raises:
            error_utils.RIB341: when deployment is not down
        """

        if not force and not self.is_down():
            raise error_utils.RIB341(
                self.deployment.config["name"],
                self.deployment.rib_mode,
                action,
                forcible,
            )

    def verify_deployment_is_active(self, action: str, none_ok: bool = False) -> None:
        """
        Purpose:
            Verify that the current deployment is the active deployment (if any)
        Args:
            action: Description of the action being executed
            none_ok: If True, will proceed when no deployment is active
        Return:
            N/A
        Raises:
            error_utils.RIB343: when another deployment is active
        """
        active_deployment = self.deployment.get_active()
        if (not active_deployment and not none_ok) or (
            active_deployment and active_deployment != self.deployment.config["name"]
        ):
            raise error_utils.RIB343(
                deployment_name=self.deployment.config["name"],
                rib_mode=self.deployment.rib_mode,
                action=action,
                active_deployment_name=active_deployment,
            )

    ###
    # Individual Information checks
    ###

    def do_expected_node_artifacts_archives_exist(self, persona: str) -> bool:
        """
        Purpose:
            Check if artifacts tar exists for the node
        Args:
            persona: Node persona
        Return:
            True if the artifacts tar for the node exists
        """

        platform = self.deployment.config["nodes"][persona]["platform"]
        architecture = self.deployment.config["nodes"][persona]["architecture"]
        node_type = self.deployment.config["nodes"][persona]["node_type"]

        if architecture == "auto":
            # Can't verify for bridged devices
            return True

        # Network manager
        network_manager_artifacts_tar = f'{self.deployment.paths.dirs["distribution_artifacts"]}/{platform}-{architecture}-{node_type}-{self.deployment.config.network_manager_kit.name}.zip'
        if not os.path.isfile(network_manager_artifacts_tar):
            return False

        # Comms cannot be checked because we don't know what subset of comms are
        # expected on this node_type/platform/architecture

        # Artifact Manager Plugins cannot be checked because we don't know what
        # subset of AMPs are expected on this node_type/platform/architecture

        # Core
        # Can check for client/server node types. Registries cannot be checked
        # because we don't know what subset of registry apps are expected
        if node_type != "registry":
            app_tar = f'{self.deployment.paths.dirs["distribution_artifacts"]}/{platform}-{architecture}-{node_type}-race.zip'
            if not os.path.isfile(app_tar):
                return False
        return True

    def did_config_gen_succeed(self) -> bool:
        """
        Purpose:
            Checks if Config Generation Succeeded for the deployment
        Args:
        Return:
            True if network manager Config Gen indicates success
        """
        network_manager_config_gen_status_file = f'{self.deployment.paths.dirs["network_manager_configs_base"]}/{self.deployment.config.network_manager_kit.name}/network-manager-config-gen-status.json'
        if os.path.isfile(network_manager_config_gen_status_file):
            network_manager_config_gen_status = general_utils.load_file_into_memory(
                network_manager_config_gen_status_file,
                data_format="json",
            )
            return network_manager_config_gen_status.get("reason") == "success"
        return False

    @abstractmethod
    def do_expected_node_artifacts_exist(self, persona: str) -> bool:
        """
        Purpose:
            Check if artifacts exist for the node
        Args:
            persona: Node persona
        Return:
            True if all artifacts for the node exist
        """

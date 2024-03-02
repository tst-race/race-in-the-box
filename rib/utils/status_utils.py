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
    Status types and evaluation utility functions
"""

# Python Library Imports
from enum import auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Iterable,
    Optional,
)
from typing_extensions import TypedDict

# Local Python Library Imports
from rib.utils import general_utils

###
# Constants
###

PLUGIN_STATUS_UNDEF = "PLUGIN_UNDEF"
PLUGIN_STATUS_NOT_READY = "PLUGIN_NOT_READY"
PLUGIN_STATUS_READY = "PLUGIN_READY"

###
# Types
###


class StatusReport(TypedDict):
    """Status report for an element, possibly with child elements"""

    status: Any
    reason: Optional[str]
    children: Optional[Dict[str, "StatusReport"]]


class NodeStatus(general_utils.PrettyEnum):
    """User-facing high-level status for a RACE node"""

    # Deployment Created but config gen not run
    READY_TO_GENERATE_CONFIG = auto()
    # Config Gen run but tars not created
    READY_TO_TAR_CONFIGS = auto()
    # Node is not running at all
    DOWN = auto()
    # File Server is up, ready to receive configs
    READY_TO_PUBLISH_CONFIGS = auto()
    # Configs have been pushed to file server
    READY_TO_INSTALL_CONFIGS = auto()
    # Node is running, but RACE app is not installed
    READY_TO_BOOTSTRAP = auto()
    # Node is running, RACE app is installed but not running
    READY_TO_START = auto()
    # Node is running, RACE app is running, network manager not ready
    INITIALIZING = auto()
    # Node is running, RACE app is running, network manager is ready
    RUNNING = auto()
    # Node was run at least once but is now stopped
    STOPPED = auto()
    # Some kind of error exists
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class ParentStatus(general_utils.PrettyEnum):
    """User-facing status for a parent of child statuses"""

    # Config Gen has not been run yet
    READY_TO_GENERATE_CONFIG = auto()
    # Config Gen was successful
    READY_TO_TAR_CONFIGS = auto()
    # All children are down
    ALL_DOWN = auto()
    # Containers are up but no configs have been pushed to the file server
    READY_TO_PUBLISH_CONFIGS = auto()
    # All expected config or etc tars have been published to the file server
    READY_TO_INSTALL_CONFIGS = auto()
    # All children are up, but none are running
    READY_TO_START = auto()
    # Nodes is running, RACE apps are running, not all network managers are ready
    INITIALIZING = auto()
    # Ready to bootstrap one or more nodes
    READY_TO_BOOTSTRAP = auto()
    # All children are running
    ALL_RUNNING = auto()
    # All children have run at least once and are now stopped
    ALL_STOPPED = auto()
    # Some children are in an error state
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()
    # Child statuses are not equal
    MIXED = auto()

    # ONLY USE FOR SERVICES & CONTAINERS
    SOME_RUNNING = auto()


class ContainerStatus(general_utils.PrettyEnum):
    """Status of a Docker container"""

    # Container has not been created
    NOT_PRESENT = auto()
    # Container has been created but is not running (i.e., it is stopped or crashed)
    EXITED = auto()
    # Container is initializing
    STARTING = auto()
    # Container is running and health check (if defined) is passing
    RUNNING = auto()
    # Container is running but health check is failing
    UNHEALTHY = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class ArtifactsStatus(general_utils.PrettyEnum):
    """Status of depencies for the node that aren't on the node itself"""

    # Pugins, RACE, & Daemon artifacts exist in the RiB Filesystem
    ARTIFACTS_EXIST = auto()
    # Pugins, RACE, & Daemon artifacts are tar'd in the RiB Filesystem
    ARTIFACT_TARS_EXIST = auto()
    # Unkown Error
    ERROR = auto()


class DaemonStatus(general_utils.PrettyEnum):
    """Status of the RACE node daemon"""

    # Daemon is not reporting any status, and is assumed to be not running
    NOT_REPORTING = auto()
    # Daemon is reporting its status
    RUNNING = auto()
    # Some kind of error exists
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class AppStatus(general_utils.PrettyEnum):
    """Status of the application (not including RACE SDK status)"""

    # Daemon is not reporting any status, and app is assumed to be not running
    NOT_REPORTING = auto()
    # App is not installed
    NOT_INSTALLED = auto()
    # Some artifacts are missing
    ERROR_PARTIALLY_INSTALLED = auto()
    # App is not running (i.e., not reporting any status)
    NOT_RUNNING = auto()
    # App is running, check RaceStatus for next actionable state
    RUNNING = auto()
    # Some kind of error exists
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class RaceStatus(general_utils.PrettyEnum):
    """Status of the RACE SDK"""

    # App is not reporting any status, and app is assumed to be not running
    NOT_REPORTING = auto()
    # Init RACE System hasn't completed yet
    NOT_INITIALIZED = auto()
    # Network manager hasn't posted ready status yet
    NETWORK_MANAGER_NOT_READY = auto()
    # App is running and ready to send/receive messages
    RUNNING = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class ConfigsStatus(general_utils.PrettyEnum):
    """Status of Configs for a node"""

    # Config Gen Succeeded
    CONFIG_GEN_SUCCESS = auto()
    # Config Gen Failed
    ERROR_CONFIG_GEN_FAILED = auto()
    # Config Tar Files Exists
    CONFIGS_TAR_EXISTS = auto()
    # Configs Tar File exists in the RiB File Server
    CONFIGS_TAR_PUSHED = auto()
    # Daemon has downloaded the configs tar file
    DOWNLOADED_CONFIGS = auto()
    # App has extracted configs
    EXTRACTED_CONFIGS = auto()
    # App extracted configs but they were invalid (unparsable or insufficient)
    # TODO this can be split up with more detail if the sdk constructor is refactored
    ERROR_INVALID_CONFIGS = auto()
    # Catch all for unknown errors
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class EtcStatus(general_utils.PrettyEnum):
    """Status of Etc files (jaeger-config)"""

    # Etc dir for the persona exists in RiB filesystem
    CONFIG_GEN_SUCCESS = auto()
    # Etc dir for the persona exists in RiB filesystem
    ERROR_CONFIG_GEN_FAILED = auto()
    # Etc Tar File Exists in RiB filesystem
    ETC_TAR_EXISTS = auto()
    # Etc Tar File exists in the RiB File Server
    ETC_TAR_PUSHED = auto()
    # Some critical files are missing (jaeger-config.yml)
    MISSING_REQUIRED_FILES = auto()
    # All critical files are seen on the node
    READY = auto()
    # Catch all for unknown errors
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()


class ServiceStatus(general_utils.PrettyEnum):
    """Status of a RiB or plugin service"""

    # Service is not reachable or failing health check
    NOT_RUNNING = auto()
    # Service is reachable or passing health check
    RUNNING = auto()
    # Some kind of error exists
    ERROR = auto()
    # Status cannot be determined
    UNKNOWN = auto()


###
# Functions
###


def evaluate_container_status(state: str, status: str) -> ContainerStatus:
    """
    Purpose:
        Determines the status of a container from the state and status as reported by a docker
        daemon
    Args:
        state: Docker-reported container state (e.g., "running")
        status: Docker-reported container status (e.g., "starting", "Up 2 minutes (healthy)")
    Return:
        Container status enum value
    """

    if state != "running":
        return ContainerStatus.EXITED
    if "starting" in status:
        return ContainerStatus.STARTING
    if "unhealthy" in status:
        return ContainerStatus.UNHEALTHY
    if "healthy" in status or "Up" in status:
        return ContainerStatus.RUNNING
    return ContainerStatus.UNKNOWN


def evaluate_node_status(
    daemon: DaemonStatus,
    app: AppStatus,
    race: RaceStatus,
    configs: ConfigsStatus,
    etc: EtcStatus,
    artifacts: ArtifactsStatus,
) -> NodeStatus:
    """
    Purpose:
        Determines the node status based on the given daemon and app status
    Args:
        daemon: Node daemon status
        app: Node app status
        race: Node race status
        configs: Node config status
        etc: Node etc status
        artifacts: Node artifacts status
    Return:
        Node status
    """

    # Created
    if configs in [ConfigsStatus.ERROR_CONFIG_GEN_FAILED] and app not in [
        AppStatus.RUNNING
    ]:
        return NodeStatus.READY_TO_GENERATE_CONFIG

    # Configs Generated
    if (
        etc in [EtcStatus.CONFIG_GEN_SUCCESS]
        and configs in [ConfigsStatus.CONFIG_GEN_SUCCESS]
        and app not in [AppStatus.RUNNING]
    ):
        return NodeStatus.READY_TO_TAR_CONFIGS

    # Down
    if (
        etc in [EtcStatus.ETC_TAR_EXISTS]
        and configs in [ConfigsStatus.CONFIGS_TAR_EXISTS]
        and daemon not in [DaemonStatus.RUNNING]
        and app not in [AppStatus.RUNNING]
    ):
        return NodeStatus.DOWN

    # Containers Up
    if (
        etc in [EtcStatus.ETC_TAR_EXISTS]
        and configs in [ConfigsStatus.CONFIGS_TAR_EXISTS]
        # Daemon doesn't actually matter but we're using this to assume containers are up
        and daemon in [DaemonStatus.RUNNING]
        and app not in [AppStatus.RUNNING]
    ):
        return NodeStatus.READY_TO_PUBLISH_CONFIGS

    # Requirements Pushed
    if (
        etc in [EtcStatus.ETC_TAR_PUSHED]
        and configs in [ConfigsStatus.CONFIGS_TAR_PUSHED]
        and daemon in [DaemonStatus.RUNNING]
        and app
        in [AppStatus.NOT_RUNNING, AppStatus.NOT_INSTALLED, AppStatus.NOT_REPORTING]
    ):
        return NodeStatus.READY_TO_INSTALL_CONFIGS

    # Up - Ready to Start
    if (
        etc in [EtcStatus.READY]
        and configs in [ConfigsStatus.DOWNLOADED_CONFIGS]
        and daemon in [DaemonStatus.RUNNING]
        and app in [AppStatus.NOT_RUNNING]
    ):
        return NodeStatus.READY_TO_START

    # Up - Ready to Bootstrap
    if (
        etc in [EtcStatus.READY]
        and artifacts in [ArtifactsStatus.ARTIFACT_TARS_EXIST]
        and daemon in [DaemonStatus.RUNNING]
        and app in [AppStatus.NOT_INSTALLED]
    ):
        return NodeStatus.READY_TO_BOOTSTRAP

    # Initializing
    if (
        etc in [EtcStatus.READY]
        and configs
        in [ConfigsStatus.EXTRACTED_CONFIGS, ConfigsStatus.DOWNLOADED_CONFIGS]
        and daemon in [DaemonStatus.RUNNING]
        and app in [AppStatus.RUNNING]
        and race in [RaceStatus.NETWORK_MANAGER_NOT_READY]
    ):
        return NodeStatus.INITIALIZING

    # Started
    if (
        etc in [EtcStatus.READY]
        and configs in [ConfigsStatus.EXTRACTED_CONFIGS]
        and daemon in [DaemonStatus.RUNNING]
        and app in [AppStatus.RUNNING]
        and race in [RaceStatus.RUNNING]
    ):
        return NodeStatus.RUNNING

    # Stopped
    if (
        etc in [EtcStatus.READY]
        and configs in [ConfigsStatus.EXTRACTED_CONFIGS]
        and daemon in [DaemonStatus.RUNNING]
        and app in [AppStatus.NOT_RUNNING]
    ):
        return NodeStatus.STOPPED

    # Basic ERROR
    if (
        daemon in [DaemonStatus.ERROR]
        or app in [AppStatus.ERROR]
        or configs in [ConfigsStatus.ERROR, ConfigsStatus.ERROR_INVALID_CONFIGS]
        or etc in [EtcStatus.ERROR]
        or artifacts in [ArtifactsStatus.ERROR]
    ):
        return NodeStatus.ERROR

    # TODO: Add common error cases as we encounter them

    return NodeStatus.UNKNOWN


def evaluate_node_parent_status(children: List[NodeStatus]) -> ParentStatus:
    """
    Purpose:
        Determines the parent status for a list of node status values
    Args:
        children: Node status values
    Return:
        Parent status
    """

    # Put all status into a set so we have just the unique status values
    consolidated = set(children)

    # Status where if one node is that status, the parent status must match
    if NodeStatus.UNKNOWN in consolidated:
        return ParentStatus.UNKNOWN
    if NodeStatus.ERROR in consolidated:
        return ParentStatus.ERROR

    # Bootstrap is the only case where we expect nodes in different states
    if {NodeStatus.READY_TO_BOOTSTRAP, NodeStatus.READY_TO_START} == consolidated:
        return ParentStatus.READY_TO_START
    if {NodeStatus.READY_TO_BOOTSTRAP, NodeStatus.RUNNING} == consolidated:
        return ParentStatus.READY_TO_BOOTSTRAP

    # At this point if there are nodes in different states, just return Mixed
    if len(consolidated) > 1:
        return ParentStatus.MIXED

    # All nodes match state
    if {NodeStatus.READY_TO_GENERATE_CONFIG} == consolidated:
        return ParentStatus.READY_TO_GENERATE_CONFIG
    if {NodeStatus.READY_TO_TAR_CONFIGS} == consolidated:
        return ParentStatus.READY_TO_TAR_CONFIGS
    if set() == consolidated:
        return ParentStatus.ALL_DOWN
    if {NodeStatus.DOWN} == consolidated:
        return ParentStatus.ALL_DOWN
    if {NodeStatus.READY_TO_PUBLISH_CONFIGS} == consolidated:
        return ParentStatus.READY_TO_PUBLISH_CONFIGS
    if {NodeStatus.READY_TO_INSTALL_CONFIGS} == consolidated:
        return ParentStatus.READY_TO_INSTALL_CONFIGS
    if {NodeStatus.READY_TO_START} == consolidated:
        return ParentStatus.READY_TO_START
    if {NodeStatus.READY_TO_BOOTSTRAP} == consolidated:
        return ParentStatus.READY_TO_BOOTSTRAP
    if {NodeStatus.INITIALIZING} == consolidated:
        return ParentStatus.INITIALIZING
    if {NodeStatus.RUNNING} == consolidated:
        return ParentStatus.ALL_RUNNING
    if {NodeStatus.STOPPED} == consolidated:
        return ParentStatus.ALL_STOPPED


def evaluate_container_parent_status(children: List[ContainerStatus]) -> ParentStatus:
    """
    Purpose:
        Determines the parent status for a list of container status values
    Args:
        children: Container status values
    Return:
        Parent status
    """

    # Put all status into a set so we have just the unique status values
    consolidated = set(children)
    # If any containers have unknown status, the parent is unknown
    if ContainerStatus.UNKNOWN in consolidated:
        return ParentStatus.UNKNOWN
    # If any container have unhealthy status, the parent is error
    if ContainerStatus.UNHEALTHY in consolidated:
        return ParentStatus.ERROR
    # If all containers are running or starting, the host is all-running
    if (
        consolidated == {ContainerStatus.RUNNING}
        or consolidated == {ContainerStatus.STARTING}
        or consolidated == {ContainerStatus.RUNNING, ContainerStatus.STARTING}
    ):
        return ParentStatus.ALL_RUNNING
    # If a container is running or starting, the host is some-running
    if (
        ContainerStatus.RUNNING in consolidated
        or ContainerStatus.STARTING in consolidated
    ):
        return ParentStatus.SOME_RUNNING
    # Otherwise all containers are not-present or exited, parent is all-down
    return ParentStatus.ALL_DOWN


def evaluate_service_parent_status(children: List[ServiceStatus]) -> ParentStatus:
    """
    Purpose:
        Determines the parent status for a list of service status values
    Args:
        children: Service status values
    Return:
        Parent status
    """

    # Put all status into a set so we have just the unique status values
    consolidated = set(children)
    # If any services have unknown status, the parent is unknown
    if ServiceStatus.UNKNOWN in consolidated:
        return ParentStatus.UNKNOWN
    # If any services have error status, the parent is error
    if ServiceStatus.ERROR in consolidated:
        return ParentStatus.ERROR
    # If all services are running, the parent is all-running
    if consolidated == {ServiceStatus.RUNNING}:
        return ParentStatus.ALL_RUNNING
    # If a service is running, the parent is some-running
    if ServiceStatus.RUNNING in consolidated:
        return ParentStatus.SOME_RUNNING
    # Otherwise all services are not-running, parent is all-down
    return ParentStatus.ALL_DOWN


def evaluate_grandparent_status(children: List[ParentStatus]) -> ParentStatus:
    """
    Purpose:
        Determines the parent status for a list of parent status values
    Args:
        children: Parent status values
    Return:
        Parent status
    """

    # Put all status into a set so we have just the unique status values
    consolidated = set(children)
    # If all child status were the same, use that as the parent status
    if len(consolidated) == 1:
        return consolidated.pop()
    # If any children have unknown status, the parent is unknown
    if ParentStatus.UNKNOWN in consolidated:
        return ParentStatus.UNKNOWN
    # If any children have error status, the parent is error
    if ParentStatus.ERROR in consolidated:
        return ParentStatus.ERROR

    # If any grandchildren are running, the parent is some-running
    if ParentStatus.SOME_RUNNING in consolidated:
        return ParentStatus.SOME_RUNNING

    if len(consolidated) > 1:
        return ParentStatus.MIXED

    # Otherwise the parent is all-down
    return ParentStatus.ALL_DOWN


def _humanize(text: str) -> str:
    """Humanizes dictionary keys for printing"""
    return text.replace("_", " ")


def _indent(level: int) -> str:
    """Creates a string with the specified number of tabs for indentation"""
    return "\t" * level


def print_status_report(
    detail_level: int,
    details: Dict[str, StatusReport],
    printer: Callable[[str], None],
    indent: int = 1,
) -> None:
    """
    Purpose:
        Formats and prints the given status reports, recursively up to the given detail level

        If the detail level is 0, only the overall status of each item in the details map is
        printed. If the detail level is 1 or higher and the detail report contains child status
        reports, the child report is printed and the detail level is decremented. This way, we
        can support any number of levels in the status report hierarchy.
    Args:
        detail_level: Level of detail
        details: Dictionary of names to status reports
        printer: Printer callable
        indent: Levels of indentation
    Return:
        N/A
    """

    for item_name in sorted(details.keys()):
        item_status = details[item_name]
        printer(f"{_indent(indent)}{_humanize(item_name)}: {item_status['status']}")
        if item_status.get("reason"):
            printer(f"{_indent(indent+2)}{item_status['reason']}")
        if detail_level > 0 and item_status.get("children"):
            print_status_report(
                detail_level=detail_level - 1,
                details=item_status["children"],
                printer=printer,
                indent=indent + 1,
            )


def print_count_report(
    detail_level: int,
    details: Dict[str, StatusReport],
    printer: Callable[[str], None],
    status_type: Iterable[str],
) -> None:
    """
    Purpose:
        Formats and prints a status count report for the given status reports

        If the detail level is 0, only non-zero counts are reported. If the detail level is greater
        than 0, all counts will be reported.
    Args:
        details: Dictionary of names to status reports
        printer: Printer callable
        status_type: All possible status values (may be a status enum)
    Return:
        N/A
    """

    flattened = flatten(details)

    counts = {}
    for status in status_type:
        counts[str(status)] = 0
    for report in flattened.values():
        counts[str(report["status"])] += 1

    total = len(flattened)
    for status in sorted(counts.keys()):
        count = counts[status]
        if count or detail_level > 0:
            printer(f"\t{count}/{total} are {status}")


def flatten(reports: Dict[str, StatusReport]) -> Dict[str, StatusReport]:
    """
    Purpose:
        Flatten the given set of status reports so that only leaf status reports exist (that is,
        remove all parent entries from the report structure)
    Args:
        reports: Dictionary of names to parent or leaf status reports
    Return:
        Dictionary of names to leaf status reports
    """

    flattened = {}

    for name, report in reports.items():
        if isinstance(report["status"], ParentStatus):
            flattened.update(flatten(report.get("children", {})))
        else:
            flattened[name] = report

    return flattened

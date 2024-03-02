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
        The RibAwsEnvStatus Enum is a representation of AWS Env statuses
"""

# Python Library Imports
from enum import auto
from typing import Dict, List, NamedTuple, Set, TypedDict

# Local Python Library Imports
from rib.utils import general_utils
from rib.utils.status_utils import StatusReport


###
# Types
###


class RibAwsEnvStatus(general_utils.PrettyEnum):
    """
    Purpose:
        Track the state of a RiB AWS Env
    """

    # For Environments, means that nothing tied to the Environment exists
    # For CF, means 0 stacks exist (regardless of state) or are in the
    #     `DELETE_COMPLETE` state
    # For EC2, means 0 managers or workers exist (regardless of state) or are
    #     exist in a `terminated` state
    # For EFS, means that neither log/data EFS exist (regardless of state) or
    #     exist in a `deleted` state
    # For Bastion, means bastion is not reachable or not running on the swarm manager
    DOWN = 0

    # For Environments, means that all stacks are running
    # For CF, means all stacks are in `CREATE_COMPLETED` state
    # For EC2, means 1 manager and x workers (set as a env config) are all in `ready`
    #     state
    # For EFS, means that log/data EFS are in `available` state
    # For Bastion, means bastion is reachable on the swarm manager
    UP = 1

    # For Environments, means that some stacks are running, but not
    #     all of the expected items. May require a `down --force` or manual intervention (
    #     i.e. going into AWS and shutting things down) if it is bad enough
    # For CF, means that all expected stacks are not in the `CREATE_COMPLETED` state
    #     but the environment is not fully DOWN
    # For EC2, means that all expected instances are not in the `ready` state
    #     but the environment is not fully DOWN
    # For Bastion, means that bastion may be running, but not connectable
    PARTIALLY_UP = 2

    # For Environments, means that all containers are running
    PROVISIONED = 3

    # For Environments, means that some containers are running, but not
    #     all of the expected items. May require a `down --force` or manual intervention
    #     if it is bad enough
    PARTIALLY_PROVISIONED = 4

    # An error has occured getting the status or taking an action on the envrionment.
    # Because AWS costs money, it is important to let the user know and allow for manual
    # intervention (i.e. shutting down the stacks in AWS) if necessary
    ERROR = 99


class AwsComponentStatus(general_utils.PrettyEnum):
    """Generic AWS environment component status"""

    # RiB does not possess enough information to evaluate the status
    UNKNOWN = auto()
    # Component does not exist
    NOT_PRESENT = auto()
    # Component exists but is not in a usable state
    NOT_READY = auto()
    # Component exists and is in a usable state
    READY = auto()
    # Component exists and is in an error state
    ERROR = auto()


class AwsEnvComponentStatus(TypedDict):
    """AWS environment status report"""

    cloud_formation: StatusReport
    ec2_instance: StatusReport
    efs: StatusReport


class AwsEnvStatus(NamedTuple):
    """AWS environment status report"""

    status: AwsComponentStatus
    components: AwsEnvComponentStatus


class ContainerRuntimeInfo(TypedDict):
    """Container runtime info"""

    state: str
    status: str
    deployment_name: str


class Ec2InstanceRuntimeInfo(TypedDict):
    """AWS EC2 instance runtime info"""

    public_dns: str
    public_ip: str
    private_dns: str
    private_ip: str
    tags: Dict[str, str]
    containers: Dict[str, ContainerRuntimeInfo]


class ActiveAwsEnvs(NamedTuple):
    """Names of active AWS environments"""

    owned: Set[str]
    unowned: Set[str]


class IncompatibleAwsEnv(NamedTuple):
    """Incompatible AWS environment"""

    name: str
    rib_version: str


class LocalAwsEnvs(NamedTuple):
    """Names of local AWS environments"""

    compatible: Set[str]
    incompatible: Set[IncompatibleAwsEnv]


###
# Functions
###


def create_parent_report(children: Dict[str, StatusReport]) -> StatusReport:
    """
    Purpose:
        Creates a parent status report, using the children status to determine the
        overall parent status
    Args:
        children: Child status reports
    Return:
        Parent status report
    """
    return StatusReport(
        status=get_parent_status([child["status"] for child in children.values()]),
        children=children,
        reason=None,
    )


def get_parent_status(children: List[AwsComponentStatus]) -> AwsComponentStatus:
    """
    Purpose:
        Determines the overall parent status from the list of child status values
    Args:
        children: Status values of all child components
    Return:
        Overall parent status
    """
    # Put all status into a set so we have just the unique status values
    consolidated = set(children)
    # If all child status were the same, use that as the parent status
    if len(consolidated) == 1:
        return consolidated.pop()
    # If any childen have error status, the parent has error status
    if AwsComponentStatus.ERROR in consolidated:
        return AwsComponentStatus.ERROR
    # If at least one child is ready or not-ready, the parent is not-ready
    if (
        AwsComponentStatus.NOT_READY in consolidated
        or AwsComponentStatus.READY in consolidated
    ):
        return AwsComponentStatus.NOT_READY
    # The only way to get here would be if there's a mix of not-present and unknown status
    return AwsComponentStatus.UNKNOWN


def convert_cf_status_to_enum(status: str) -> AwsComponentStatus:
    """
    Purpose:
        Converts the given CloudFormation stack status value to an AWS component status enum value
    Args:
        status: CloudFormation stack status value
    Return:
        AWS component status enum
    """
    if status == "CREATE_COMPLETE":
        return AwsComponentStatus.READY
    if status in ("CREATE_FAILED", "DELETE_FAILED"):
        return AwsComponentStatus.ERROR
    if status == "DELETE_COMPLETE":
        return AwsComponentStatus.NOT_PRESENT
    if status in ("CREATE_IN_PROGRESS", "DELETE_IN_PROGRESS"):
        return AwsComponentStatus.NOT_READY
    return AwsComponentStatus.UNKNOWN


def convert_ec2_status_to_enum(status: str) -> AwsComponentStatus:
    """
    Purpose:
        Converts the given EC2 instance status value to an AWS compnent status enum value
    Args:
        status: EC2 instance status value
    Return:
        AWS component status enum
    """
    if status == "running":
        return AwsComponentStatus.READY
    if status in ("stopped", "terminated"):
        return AwsComponentStatus.NOT_PRESENT
    if status in ("pending", "shutting-down", "stopping"):
        return AwsComponentStatus.NOT_READY
    return AwsComponentStatus.UNKNOWN


def convert_efs_status_to_enum(status: str) -> AwsComponentStatus:
    """
    Purpose:
        Converts the given EFS volume status value to an AWS component status enum value
    Args:
        status: EFS volume status value
    Return:
        AWS component status enum
    """
    if status == "available":
        return AwsComponentStatus.READY
    if status == "error":
        return AwsComponentStatus.ERROR
    if status == "deleted":
        return AwsComponentStatus.NOT_PRESENT
    if status in ("creating", "deleting"):
        return AwsComponentStatus.NOT_READY
    return AwsComponentStatus.UNKNOWN

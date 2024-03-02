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
        Utilities for connecting to AWS from RiB
"""

# Python Library Imports
import boto3
import botocore
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Local Library Imports
from rib.utils import error_utils, general_utils


###
# AWS Profile Functions
###


def create_aws_profile(
    access_id: str,
    secret_id: str,
    aws_region: str,
    overwrite: bool,
    linux_x86_64_ami: str = None,
    linux_arm64_ami: str = None,
    linux_gpu_x86_64_ami: str = None,
    linux_gpu_arm64_ami: str = None,
) -> None:
    """
    Purpose:
        Create an AWS Profile from access id and secret id

        NOTE (TODO): https://boto3.amazonaws.com/v1/documentation/api/latest/
            guide/configuration.html only has passing params or a profile file as
            options. It would be nice to have a feature to CREATE a profile, but I
            do not see that. would like to make this smarter in the future.
    Args:
        access_id (str): access id for the aws account to use
        secret_id (str): secret id for the aws account to use
        aws_region (str): Default region for AWS operations
        overwrite (bool): Recreate creds file if it already exists, else raise
        linux_x86_64_ami (str): AMI for linux-x86-64 instances
        linux_arm64_ami (str): AMI for linux-arm64 instances
        linux_gpu_x86_64_ami (str): AMI for linux-gpu-x86-64 instances
        linux_gpu_arm64_ami (str): AMI for linux-gpu-arm64 instances
    Return:
        None
    Raises:
        Exception: If we fail to create profile
    """

    # Set Paths
    aws_credentials_file = os.path.expanduser("~/.aws/credentials")
    aws_config_file = os.path.expanduser("~/.aws/config")
    rib_aws_pref_file = os.path.expanduser("~/.race/rib/aws/rib-preferences")

    # Check for prexisting configs, clear or error
    if os.path.isfile(aws_credentials_file) or os.path.isfile(aws_config_file):
        if overwrite:
            print("Overwriting existing AWS credentials")
        else:
            raise error_utils.RIB703()

    # Store Credentials data
    aws_credentials_data = f"""
    [default]
    aws_access_key_id = {access_id}
    aws_secret_access_key = {secret_id}
    """
    general_utils.write_data_to_file(
        aws_credentials_file, aws_credentials_data, overwrite=True
    )

    # Store Config data
    aws_config_data = f"""
    [default]
    output = json
    region = {aws_region}
    """
    general_utils.write_data_to_file(aws_config_file, aws_config_data, overwrite=True)

    # Store rib preferences
    rib_pref_data = {}
    if linux_x86_64_ami:
        rib_pref_data["linux_x86_64_ami"] = linux_x86_64_ami
    if linux_arm64_ami:
        rib_pref_data["linux_arm64_ami"] = linux_arm64_ami
    if linux_gpu_x86_64_ami:
        rib_pref_data["linux_gpu_x86_64_ami"] = linux_gpu_x86_64_ami
    if linux_gpu_arm64_ami:
        rib_pref_data["linux_gpu_arm64_ami"] = linux_gpu_arm64_ami
    general_utils.write_data_to_file(
        rib_aws_pref_file, rib_pref_data, data_format="json", overwrite=True
    )

    # Verify that the provide credentials work
    verify_aws_profile()


def verify_aws_profile(
    profile: str = "default", required_services: Optional[List[str]] = None
) -> None:
    """
    Purpose:
        Verify an AWS profile.

        Will test to make sure the profile has access to a set of resources needed
        for RiB.

        required_services has been added as different performers (and especially Core vs
        Network Manager/Comms) will need different resources for their solutions and a different level
        of verification. Right now, there is a basis default set needed to do anything
        in AWS with RiB (cloudformation for creating resources, EC2 as the primary
        resource, and IAM for user control/permissions/grants on the resources). S3
        is not yet in use, but it will be for certain performers (STR needs it for its
        tensorflow models).
    Args:
        profile (str): the profile to use to connect to AWS.
        required_services (List[str]): List of resources to confirm the profile has
            access to
    Return:
        N/A
    Raises:
        error_utils.RIB702: when the profile does not have the required permissions.
            This means the user is not able to use RiB with AWS without updating
            their priveleges
        error_utils.RIB704: when there is some required resource that is not currently
            able to be validated (i.e. some caller wants to verify SNS and that does not
            have a validator function yet). This requires a code update to this util
            to verify the required resource OR the caller needs to accept that it is
            not validated to proceed.
    """

    service_validators = {
        "cloudformation": validate_service_cloudformation,
        "ec2": validate_service_ec2,
        "efs": validate_service_efs,
        "iam": validate_service_iam,
        "s3": validate_service_s3,
    }

    if not required_services:
        required_services = ["cloudformation", "ec2", "efs", "iam"]

    aws_session = connect_aws_session_with_profile(profile=profile)
    missing_privileges = []
    for expected_service_name in required_services:
        service_validtor = service_validators.get(expected_service_name, None)

        if not service_validtor:
            raise error_utils.RIB704(expected_service_name)

        try:
            service_validtor(aws_session)
        except error_utils.RIB702 as missing_priv_err:
            missing_privileges.append(expected_service_name)

    if missing_privileges:
        raise error_utils.RIB702(missing_privileges)


def get_rib_aws_preferences() -> Dict[str, str]:
    """
    Purpose:
        Get aws RiB preferences
    Return:
        rib_aws_preferences (Dict[str, str]): RiB preference information
    """
    rib_aws_pref_filename = "~/.race/rib/aws/rib-preferences"
    rib_aws_pref_file = os.path.expanduser(rib_aws_pref_filename)
    try:
        rib_aws_preferences = general_utils.load_file_into_memory(
            rib_aws_pref_file, data_format="json"
        )
        print(f"Using RiB AWS preferences from file: {rib_aws_pref_filename}")
    except Exception as err:
        rib_aws_preferences = {}
    return rib_aws_preferences


def get_aws_profile_information(profile: str = "default") -> Dict[str, str]:
    """
    Purpose:
        Get profile information for the user
    Args:
        profile (str): the profile to use to connect to AWS.
    Return:
        aws_profile_information (Dict[str, str]): Profile information
    """

    aws_profile_information = {}

    aws_session = connect_aws_session_with_profile(profile=profile)
    aws_creds = aws_session.get_credentials()

    aws_profile_information["access_key"] = aws_creds.access_key
    aws_profile_information["profile_name"] = aws_session.profile_name
    aws_profile_information["region_name"] = aws_session.region_name

    aws_profile_information.update(get_user_details(aws_session))

    return aws_profile_information


###
# Permission Validtors per resource
###


def validate_service_cloudformation(aws_session: boto3.session.Session) -> None:
    """
    Purpose:
        Validate Cloudformation Resource Access in AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        N/A
    Raises:
        error_utils.RIB702: when access is not available for the service
    """

    try:
        # Get and use the resource to check connectivity (have to use to test)
        cloudformation_resource = connect_aws_resource(aws_session, "cloudformation")
        _ = list(cloudformation_resource.stacks.all())
    except botocore.exceptions.ClientError as client_err:
        raise error_utils.RIB702(["cloudformation"])


def validate_service_ec2(aws_session: boto3.session.Session) -> None:
    """
    Purpose:
        Validate EC2 Resource Access in AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        N/A
    Raises:
        error_utils.RIB702: when access is not available for the service
    """

    try:
        # Get and use the resource to check connectivity (have to use to test)
        get_ec2_instances(aws_session)
    except botocore.exceptions.ClientError as client_err:
        raise error_utils.RIB702(["ec2"])


def validate_service_efs(aws_session: boto3.session.Session) -> None:
    """
    Purpose:
        Validate EFS Client Access in AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        N/A
    Raises:
        error_utils.RIB702: when access is not available for the service
    """

    try:
        # Get and use the service to check connectivity (have to use to test)
        _ = get_efs_filesystems(aws_session)
    except botocore.exceptions.ClientError as client_err:
        raise error_utils.RIB702(["efs"])


def validate_service_iam(aws_session: boto3.session.Session) -> None:
    """
    Purpose:
        Validate IAM Resource Access in AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        N/A
    Raises:
        error_utils.RIB702: when access is not available for the service
    """

    try:
        # Get and use the resource to check connectivity (have to use to test)
        iam_resource = connect_aws_resource(aws_session, "iam")
        _ = list(iam_resource.roles.all())
    except botocore.exceptions.ClientError as client_err:
        raise error_utils.RIB702(["iam"])


def validate_service_s3(aws_session: boto3.session.Session) -> None:
    """
    Purpose:
        Validate S3 Resource Access in AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        N/A
    Raises:
        error_utils.RIB702: when access is not available for the service
    """

    try:
        # Get and use the service to check connectivity (have to use to test)
        s3_resource = connect_aws_resource(aws_session, "s3")
        _ = list(s3_resource.buckets.all())
    except botocore.exceptions.ClientError as client_err:
        raise error_utils.RIB702(["s3"])


###
# AWS Session/Resource/Client Functions
###


def connect_aws_session_with_profile(profile: str = "default") -> boto3.session.Session:
    """
    Purpose:
        Create an AWS Session object with a profile
    Args:
        profile (str): the profile to use to connect to AWS.
    Return:
        aws_session (boto3.Session Object): connected session object
    Raises:
        Exception: if the profile is not found
    """

    # Establish/Connect AWS Session
    try:
        aws_session = boto3.session.Session(profile_name=profile)
    except botocore.exceptions.ProfileNotFound as profile_err:
        raise error_utils.RIB706() from None

    return aws_session


def connect_aws_resource(
    aws_session: boto3.session.Session, aws_resource_name: str
) -> boto3.resources.factory.ServiceResource:
    """
    Purpose:
        Get an AWS Resource Object

        Resource is a higher-level OOP objecgts to interact with AWS. There are limits
        to what AWS resources you can work with, use a client when necessary.
    Args:
        aws_session (boto3.Session Object): connected session object
        aws_resource_name (str): Name of the resource to get
    Return:
        aws_resource (boto3 Resource Object): connected aws resource object
    Raises:
        boto3.exceptions.ResourceNotExistsError: When a resource is not available
        Exception: When the resource is returned but object is unusable
    """

    # Get the AWS Resource Object
    try:
        aws_resource = aws_session.resource(aws_resource_name)
    except boto3.exceptions.ResourceNotExistsError as resouce_err:
        print(f"No Permissions for {aws_resource_name} Resource with provided profile")
        raise resouce_err

    # Test Resource Connected, have to actually test the resource to confirm it works
    try:
        _ = aws_resource.meta
    except Exception as err:
        print(f"Failed to get {aws_resource_name} Resource")
        raise err

    return aws_resource


def connect_aws_client(
    aws_session: boto3.session.Session, aws_client_name: str
) -> botocore.client.BaseClient:
    """
    Purpose:
        Get an AWS Client Object.

        Client is a lower-level service for AWS and exposes
    Args:
        aws_session (boto3.Session Object): connected session object
        aws_client_name (str): Name of the client to get
    Return:
        aws_client (boto3 Client Object): connected aws client object
    Raises:
        boto3.exceptions.ResourceNotExistsError: When a client is not available
        Exception: When the client is returned but object is unusable
    """

    # Get the AWS Client Object
    try:
        aws_client = aws_session.client(aws_client_name)
    except boto3.exceptions.ResourceNotExistsError as resouce_err:
        print(f"No Permissions for {aws_client_name} Resource with provided profile")
        raise resouce_err

    # Test Client Connected, have to actually test the resource to confirm it works
    try:
        _ = aws_client.meta
    except Exception as err:
        print(f"Failed to get {aws_client_name} Client")
        raise err

    # Test that client is created correctly as an object of the BaseClient class
    if not issubclass(type(aws_client), botocore.client.BaseClient):
        print(f"Failed to get {aws_client_name} Client")
        raise err

    return aws_client


###
# STS (User) Functions
###


def get_user_details(aws_session: boto3.session.Session) -> Dict[str, str]:
    """
    Purpose:
        Get user details from AWS. Will use the STS service to get information about
        the user that is not available in RiB. If this fails, will return nothing instead
        of an exception (for now)

        TODO: should we raise here?
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        user_details (Dict[str, str]): user details
    Raises:
        N/A
    """

    user_details = {}

    try:
        sts_client = connect_aws_client(aws_session, "sts")
        unparsed_user_details = sts_client.get_caller_identity()
        user_details = {
            "user_id": unparsed_user_details["UserId"],
            "account": unparsed_user_details["Account"],
            "arn": unparsed_user_details["Arn"],
            "username": unparsed_user_details["Arn"].split("/")[-1],
        }
    except Exception as err:
        print(f"Error getting user details: {err}")

    return user_details


###
# EFS Functions
###


def get_efs_filesystems(aws_session: boto3.session.Session) -> Dict[str, str]:
    """
    Purpose:
        Get EFS Filesystems from AWS. Will use the EFS Service/Client ...
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        user_details (Dict[str, str]): user details
    Raises:
        N/A
    """

    efs_filesystem_details = {}

    try:
        efs_client = connect_aws_client(aws_session, "efs")
        efs_filesystem_details = get_efs_filesystem_details(efs_client)
    except Exception as err:
        # TODO, catch more specific exceptions
        raise

    return efs_filesystem_details


def get_efs_filesystem_details(
    efs_client: botocore.client.BaseClient,
) -> Dict[str, Dict]:
    """
    Purpose:
        Get EFS Filesystems running in AWS
    Args:
        ec2_client (boto3 EC2 Resource Object): connected ec2 client object
    Return:
        efs_filesystems (Dict[str, Dict]): Dict of EC2 instances with details for each
    Raises:
        N/A
    """

    return {
        efs_filesystem["Name"]: parse_efs_filesystem_details(efs_filesystem)
        for efs_filesystem in efs_client.describe_file_systems()["FileSystems"]
    }


def parse_efs_filesystem_details(efs_filesystem: Dict[str, Any]) -> Dict[str, Any]:
    """
    Purpose:
        Get EC2 Instances Details
    Args:
        efs_filesystem (Dict[str, Any]): EFS Filesystem to parse
    Return:
        efs_filesystem_details (Dict[str, Any]): parsed information from EFS
            filesystems
    Raises:
        N/A
    """

    if efs_filesystem.get("Tags", []) is not None:
        efs_tags = {tag["Key"]: tag["Value"] for tag in efs_filesystem.get("Tags", [])}
    else:
        efs_tags = {}

    efs_filesystem_details = {
        "id": efs_filesystem["FileSystemId"],
        "name": efs_filesystem["Name"],
        "state": efs_filesystem["LifeCycleState"],
        "throughput_mode": efs_filesystem["ThroughputMode"],
        "performance_mode": efs_filesystem["PerformanceMode"],
        "size_bytes": efs_filesystem["SizeInBytes"]["Value"],
        "create_time": efs_filesystem["CreationTime"],
        "tags": efs_tags,
    }

    return efs_filesystem_details


def filter_efs_filesystem_by_tags_and_state(
    efs_filesystems: Dict[str, Any],
    tags: Optional[Dict[str, Any]] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Filter a Dict of EFS filesystems by tag and state

        NOTE: will use AND logic when verifying tags (all requested need to be present)
    Args:
        efs_filesystems (Dict[str, Dict]): Dict of EC2 instances with details for each
        tags (Dict[str, Any]): Dict of key/value tags to match on. Will use AND logic
        state (Optional[str]): state of the stacks to return
    Return:
        filtered_efs_filesystems (Dict[str, Dict]): Dict of EC2 instances with details
            for each
    Raises:
        TBD
    """

    filtered_efs_filesystems = {}

    # Default tags to empty, will auto-pass
    if not tags:
        tags = {}

    for efs_filesystems_name, efs_filesystems_details in efs_filesystems.items():
        # If missing tags, we will filter out the stack
        if not all(
            efs_filesystems_details["tags"].get(tag_key, None) == tag_val
            for tag_key, tag_val in tags.items()
        ):
            continue

        # If state is set and the stack is in a different set, we will filter the stack
        elif state is not None and efs_filesystems_details["status"] != state:
            continue

        filtered_efs_filesystems[efs_filesystems_name] = efs_filesystems_details

    return filtered_efs_filesystems


###
# Cloudformation Service Functions
###


def get_cf_stacks(aws_session: boto3.session.Session) -> Dict[str, Any]:
    """
    Purpose:
        Get Cloudformation Instances from AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        cf_stack_details (Dict[str, Any]): dict of stack ids and details
    """

    cf_stack_details = {}

    try:
        cf_resource = connect_aws_resource(aws_session, "cloudformation")
        cf_stack_details = get_cf_stack_details(cf_resource)
    except Exception as err:
        # TODO, catch more specific exceptions
        raise

    return cf_stack_details


def get_cf_stack_details(
    cf_resource: boto3.resources.factory.ServiceResource,
) -> Dict[str, Dict]:
    """
    Purpose:
        Get Cloudformation Stacks running in AWS
    Args:
        cf_resource (boto3 Cloudformation Resource Object): connected
            cf resource object
    Return:
        cf_stacks (Dict): Dict of EC2 stacks with details for each
    Raises:
        N/A
    """

    cf_stacks = {
        cf_stack_obj.name: parse_cf_stack_details(cf_stack_obj)
        for cf_stack_obj in cf_resource.stacks.all()
    }

    return cf_stacks


def parse_cf_stack_details(
    cf_stack_obj: boto3.resources.factory.ServiceResource,
) -> Dict[str, Any]:
    """
    Purpose:
        Get Cloudformation Stack Details
    Args:
        cf_resource (boto3 Cloudformation Resource Object): Cloudformation
            Stack obj to parse
    Return:
        cf_stack_details (Dict[str, Any]): parsed information from
            Cloudformation Stack
    Raises:
        TBD
    """

    if cf_stack_obj.tags:
        stack_tags = {tag["Key"]: tag["Value"] for tag in cf_stack_obj.tags}
    else:
        stack_tags = {}

    cf_stack_details = {
        # Metadata
        "id": cf_stack_obj.stack_id,
        "name": cf_stack_obj.name,
        # Status
        "status": cf_stack_obj.stack_status,
        "status_reason": cf_stack_obj.stack_status_reason,
        # Outputs of the Stack
        "outputs": cf_stack_obj.outputs,
        # Tags identifying the stack
        "tags": stack_tags,
        # Time Information
        "creation_time": cf_stack_obj.creation_time,
        "last_updated_time": cf_stack_obj.last_updated_time,
    }

    return cf_stack_details


def filter_cf_stacks_by_tags_and_state(
    cf_stacks: Dict[str, Any],
    tags: Optional[Dict[str, Any]] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Filter a Dict of cf stacks by tag and state.

        NOTE: will use AND logic when verifying tags (all requested need to be present)
    Args:
        cf_stacks (Dict[str, Any]): Dict of Cloudformation stacks with details for each
        tags (Dict[str, Any]): Dict of key/value tags to match on. Will AND them all
        state (Optional[str]): state of the stacks to return
    Return:
        filtered_cf_stacks (Dict[str, Any]): Dict of Cloudformation stacks with
            details for each
    Raises:
        TBD
    """

    filtered_cf_stacks = {}

    # Default tags to empty, will auto-pass
    if not tags:
        tags = {}

    for cf_stack_name, cf_stack_details in cf_stacks.items():
        # If missing tags, we will filter out the stack
        if not all(
            cf_stack_details["tags"].get(tag_key, None) == tag_val
            for tag_key, tag_val in tags.items()
        ):
            continue

        # If state is set and the stack is in a different set, we will filter the stack
        elif state is not None and cf_stack_details["status"] != state:
            continue

        filtered_cf_stacks[cf_stack_name] = cf_stack_details

    return filtered_cf_stacks


###
# EC2 Service Functions
###


@dataclass
class Ec2InstanceTypeDetails:
    """Details (specs) about an instance type"""

    arch: str
    cpus: int
    gpus: int
    is_metal: bool
    name: str
    ram_mb: int


def get_ec2_instance_type_details(
    aws_session: boto3.session.Session, types: List[str]
) -> Dict[str, Ec2InstanceTypeDetails]:
    """
    Purpose:
        Get EC2 instance type details from AWS
    Args:
        aws_session: connected session object
        types: List of instance types to fetch details
    Returns:
        Dict of instance types to details
    """
    details_by_type = {}
    try:
        # ignoring this, known issue with pylint and botocore due to botocore dynamically
        # construction members based on the
        # datamodel https://github.com/PyCQA/pylint/issues/3134
        # pylint: disable=no-member
        ec2_client: botocore.client.EC2 = connect_aws_client(aws_session, "ec2")
        instance_types = ec2_client.describe_instance_types(InstanceTypes=types)
        for instance_type in instance_types["InstanceTypes"]:
            details_by_type[instance_type["InstanceType"]] = Ec2InstanceTypeDetails(
                arch=instance_type["ProcessorInfo"]["SupportedArchitectures"][0],
                cpus=instance_type["VCpuInfo"]["DefaultVCpus"],
                gpus=_get_num_gpus(instance_type),
                is_metal=instance_type["BareMetal"],
                name=instance_type["InstanceType"],
                ram_mb=instance_type["MemoryInfo"]["SizeInMiB"],
            )
    except Exception as err:
        raise error_utils.RIB700(err)

    return details_by_type


def _get_num_gpus(instance_type: Dict[str, Any]) -> int:
    """
    Purpose:
        Determines the number of total GPUs available in the given instance type
    Args:
        instance_type: Information about instance type
    Return:
        Number of GPUs
    """
    num_gpus = 0
    for gpu in instance_type.get("GpuInfo", {}).get("Gpus", []):
        num_gpus += gpu.get("Count", 0)
    return num_gpus


def get_ec2_instances(aws_session: boto3.session.Session) -> Dict[str, Any]:
    """
    Purpose:
        Get EC2 Instances from AWS
    Args:
        aws_session (boto3.Session Object): connected session object
    Return:
        ec2_instance_details (Dict[str, Any]): dict of instance ids and details
    """

    ec2_instance_details = {}

    try:
        ec2_resource = connect_aws_resource(aws_session, "ec2")
        ec2_instance_details = get_ec2_instance_details(ec2_resource)
    except Exception as err:
        # TODO, catch more specific exceptions
        raise

    return ec2_instance_details


def get_ec2_instance_details(
    ec2_resource: boto3.resources.factory.ServiceResource,
) -> Dict[str, Dict]:
    """
    Purpose:
        Get EC2 Instances running in AWS
    Args:
        ec2_resource (boto3 EC2 Resource Object): connected ec2 resource object
    Return:
        ec2_instances (Dict): Dict of EC2 instances with details for each
    Raises:
        N/A
    """

    return {
        ec2_instance_obj.id: parse_ec2_instance_details(ec2_instance_obj)
        for ec2_instance_obj in ec2_resource.instances.all()
    }


def parse_ec2_instance_details(
    ec2_instance_obj: boto3.resources.factory.ServiceResource,
) -> Dict[str, Any]:
    """
    Purpose:
        Get EC2 Instances Details
    Args:
        ec2_instance_obj (boto3 EC2 Instance Object): EC2 Instance obj to parse
    Return:
        ec2_instance_details (Dict[str, Any]): parsed information from EC2 Instance
    Raises:
        TBD
    """

    if ec2_instance_obj.tags:
        instance_tags = {tag["Key"]: tag["Value"] for tag in ec2_instance_obj.tags}
    else:
        instance_tags = {}

    ec2_instance_details = {
        "id": ec2_instance_obj.id,
        "addresses": {
            "private": {
                "ip": ec2_instance_obj.private_ip_address,
                "dns": ec2_instance_obj.private_dns_name,
            },
            "public": {
                "ip": ec2_instance_obj.public_ip_address,
                "dns": ec2_instance_obj.public_dns_name,
            },
        },
        "state": ec2_instance_obj.state,
        "tags": instance_tags,
    }

    return ec2_instance_details


def filter_ec2_instances_by_tags_and_state(
    ec2_instances: Dict[str, Any],
    tags: Optional[Dict[str, Any]] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Purpose:
        Filter a set of ec2 instances by tag.

        NOTE: will AND all tags.
    Args:
        ec2_instances (Dict[str, Any]): Dict of EC2 instances with details for each
        tags (Dict[str, Any]): Dict of key/value tags to match on. Will AND them all
        state (Optional[str]): state of the instances to return
    Return:
        filtered_ec2_instances (Dict[str, Any]): Dict of EC2 instances with
            details for each
    Raises:
        TBD
    """

    filtered_ec2_instances = {}

    if not tags:
        tags = {}

    for ec2_instance_id, ec2_instance_details in ec2_instances.items():
        if not all(
            ec2_instance_details["tags"].get(tag_key, None) == tag_val
            for tag_key, tag_val in tags.items()
        ):
            continue

        if state is not None and ec2_instance_details["state"]["Name"] != state:
            continue

        filtered_ec2_instances[ec2_instance_id] = ec2_instance_details

    return filtered_ec2_instances


def does_ssh_key_exist(ssh_key_name: str) -> bool:
    """
    Purpose:
        Check to see if a given ssh key name exists. this is a key in aws that
        will be mounted in an EC2 instance, if this is false the instance would be
        inaccessible or fail.
    Args:
        ssh_key_name: name of the ssh key pair in aws
    Return:
        key_exists: if the key exists in AWS
    """

    key_exists = False

    try:
        # Connect AWS session/resource
        aws_session = connect_aws_session_with_profile()
        ec2_resource = connect_aws_resource(aws_session, "ec2")

        # Check for the key in the filtered key pairs, should only be one, but any
        # results indicate the key name works
        for key_pair in ec2_resource.key_pairs.filter(KeyNames=[ssh_key_name]):
            key_exists = True
            break
    except botocore.exceptions.ClientError:
        # Key does not exist, continue
        pass
    except Exception:
        # TODO, catch more specific exceptions
        raise

    return key_exists

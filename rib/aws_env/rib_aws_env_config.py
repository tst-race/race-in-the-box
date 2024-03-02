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
    Configuration types for AWS environments
"""

# Python Library Imports
from pydantic import BaseModel
from typing import Any, Collection, Mapping, Optional, TypedDict


###
# Types
###


class Ec2InstanceConfig(BaseModel):
    """EC2 instance configuration"""

    instance_type: str
    instance_ami: str
    ebs_size: int


class Ec2InstanceGroupConfig(Ec2InstanceConfig):
    """EC2 instance group configuration"""

    instance_count: int


class AwsEnvConfig(BaseModel):
    """AWS environment configuration"""

    name: str
    rib_version: str
    ssh_key_name: str
    remote_username: str
    region: str
    cluster_manager: Ec2InstanceConfig
    service_host: Ec2InstanceConfig
    linux_arm64_hosts: Ec2InstanceGroupConfig
    linux_x86_64_hosts: Ec2InstanceGroupConfig
    linux_gpu_arm64_hosts: Ec2InstanceGroupConfig
    linux_gpu_x86_64_hosts: Ec2InstanceGroupConfig
    android_arm64_hosts: Ec2InstanceGroupConfig
    android_x86_64_hosts: Ec2InstanceGroupConfig


class Ec2InstanceDetails(TypedDict):
    """Runtime details about an EC2 instance"""

    id: str
    private_ip: str
    private_dns: str
    public_ip: str
    public_dns: str
    tags: Mapping[str, Any]


class AwsEnvCache(TypedDict):
    """Cached AWS enviroment information"""

    instances: Mapping[str, Collection[str]]


class AwsEnvMetadata(TypedDict):
    """AWS environment metadata"""

    rib_image: Mapping[str, Any]

    create_command: str
    create_date: str

    last_provision_command: Optional[str]
    last_provision_time: Optional[str]

    last_unprovision_command: Optional[str]
    last_unprovision_time: Optional[str]

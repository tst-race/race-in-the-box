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

""" AWS deployment operation functions """

# Python Library Imports
from typing import Any, Dict

# Local Python Library Imports
from rib.deployment import RibAwsDeployment
from rib.restapi.schemas.aws_deployments import (
    StandUpAwsDeploymentParams,
    TearDownAwsDeploymentParams,
)


def stand_up_te_deployment(deployment_name: str, data: Dict[str, Any]):
    """Stand up an AWS deployment"""

    params = StandUpAwsDeploymentParams.parse_obj(data)

    deployment = RibAwsDeployment.get_existing_deployment_or_fail(
        deployment_name, "aws"
    )

    deployment.up(
        force=params.force,
        no_publish=params.no_publish,
        timeout=params.timeout,
    )


def tear_down_te_deployment(deployment_name: str, data: Dict[str, Any]):
    """Tear down an AWS deployment"""

    params = TearDownAwsDeploymentParams.parse_obj(data)

    deployment = RibAwsDeployment.get_existing_deployment_or_fail(
        deployment_name, "aws"
    )

    deployment.down(force=params.force, timeout=params.timeout)

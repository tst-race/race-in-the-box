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

""" AWS deployment API schemas """

# Python Library Imports
from pydantic import BaseModel


###
# Operation Payloads
###


class StandUpAwsDeploymentParams(BaseModel):
    """Stand up AWS deployment request parameters"""

    force: bool = False
    timeout: int = 300
    no_publish: bool = False


class TearDownAwsDeploymentParams(BaseModel):
    """Tear down AWS deployment request parameters"""

    force: bool = False
    timeout: int = 300

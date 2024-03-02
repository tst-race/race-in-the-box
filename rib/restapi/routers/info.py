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

""" RiB /api/info router """

# Python Library Imports
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local Python Library Imports
from rib.restapi.dependencies import RaceInTheBoxState, get_rib_state
from rib.utils import docker_utils

router = APIRouter(prefix="/api/info", tags=["RiB information"])


class RiBInfo(BaseModel):
    """RiB information model"""

    version: str
    image_tag: str
    image_digest: str
    image_created: str


@router.get("", response_model=RiBInfo)
def rib_info(rib_state: RaceInTheBoxState = Depends(get_rib_state)):
    """Get RiB information"""
    try:
        image_info = docker_utils.get_container_info("race-in-the-box")["image"]
    except:
        image_info = []
    return {
        "version": rib_state.config.RIB_VERSION,
        "image_tag": image_info.get("tag", "unknown"),
        "image_digest": image_info.get("digest", "unknown"),
        "image_created": image_info.get("created", "unknown"),
    }

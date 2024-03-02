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

"""RiB /api/race router"""

# Python Library Imports
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local Python Library Imports
from rib.restapi.dependencies import get_rib_state
from typing import List

router = APIRouter(
    prefix="/api/race",
    tags=["RACE artifacts"],
    responses={404: {"description": "Not found"}},
)


class RaceVersions(BaseModel):
    """Compatible RACE versions response"""

    versions: List[str]


@router.get("/versions", response_model=RaceVersions)
def get_race_versions(rib_state=Depends(get_rib_state)):
    """Get compatible RACE versions"""
    return {"versions": rib_state.config.RACE_VERSIONS}

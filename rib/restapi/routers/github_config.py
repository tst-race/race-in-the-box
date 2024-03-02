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

""" RiB /api/github-config router """

# Python Library Imports
from fastapi import APIRouter, Depends, HTTPException

# Local Python Library Imports
from rib.restapi.dependencies import RaceInTheBoxState, get_rib_state
from rib.utils import docker_utils, github_utils

router = APIRouter(
    prefix="/api/github-config",
    tags=["GitHub configuration"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=github_utils.GitHubConfig)
def get_config():
    """Get current GitHub configuration values"""
    return github_utils.read_github_config()


@router.patch("")
def update_config(
    config: github_utils.GitHubConfig,
    rib_state: RaceInTheBoxState = Depends(get_rib_state),
):
    """Update GitHub configuration values"""
    try:
        github_utils.update_github_config(config)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err).strip()) from None

    updated_config = github_utils.read_github_config()
    if updated_config.access_token and updated_config.username:
        docker_utils.login_docker_registry(
            username=updated_config.username,
            password=updated_config.access_token,
            registry=rib_state.config.CONTAINER_REGISTRY_URL,
            user_state_path=rib_state.config.RIB_PATHS["docker"]["user_state"],
        )
        # Verify docker configuration
        docker_utils.get_docker_client()

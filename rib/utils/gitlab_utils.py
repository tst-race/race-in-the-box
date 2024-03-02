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
    Utilities for interacting with the gitlab API
"""

# Python Library Imports
import logging
import requests
from typing import List, Optional


logger = logging.getLogger(__name__)


def get_project_id(
    gitlab_token: str, gitlab_url: str, namespace: str, project_name: str
) -> Optional[int]:
    """
    Purpose:
        Queries gitlab for the ID of the given project and repo
    Args:
        gitlab_token: Gitlab access token
        gitlab_url: URL to the gitlab server instance
        namespace: Namespace of the project
        project_name: Name of the project
    Return:
        ID of the project, if found
    """

    try:
        result = requests.get(
            f"{gitlab_url}/api/v4/projects?search={project_name}",
            headers={"PRIVATE-TOKEN": gitlab_token},
        )
        if result.status_code == 200:
            for project_info in result.json():
                if (
                    project_info.get("namespace", {}).get("path") == namespace
                    and project_info.get("name") == project_name
                ):
                    return project_info.get("id")
    except Exception as err:
        logger.warning(err)

    return None


def get_registry_repo_id(
    gitlab_token: str,
    gitlab_url: str,
    namespace: str,
    project_name: str,
    repo_name: str,
) -> Optional[int]:
    """
    Purpose:
        Queries gitlab for the ID of the given container registry repository
    Args:
        gitlab_token: Gitlab access token
        gitlab_url: URL to the gitlab server instance
        namespace: Namespace of the project
        project_name: Name of the project
        repo_name: Name of the container registry repository
    Return:
        ID of the registry repo, if found
    """
    response = requests.get(
        # NOTE: the %2F can NOT be replaced with a slash. It will fail if you try. It seems namespace/project_name isn't a path, but a stand-in for the project ID.
        f"{gitlab_url}/api/v4/projects/{namespace}%2F{project_name}/registry/repositories",
        headers={"PRIVATE-TOKEN": gitlab_token},
    )
    if response.status_code == 200:
        for repo_info in response.json():
            if repo_info.get("name") == repo_name:
                return repo_info.get("id")
        # TODO: I feel like if we get to this point we should raise an exception. So from a blackbox view of the function it should either:
        #     * return a valid registry ID
        #     * raise an exception
    else:
        raise Exception(
            f"API query of container registry {namespace}/{project_name} failed with {response.status_code}: {response.reason}"
        )

    return None


def get_registry_repo_tags(
    gitlab_token: str,
    gitlab_url: str,
    namespace: str,
    project_name: str,
    repo_id: int,
) -> List[str]:
    """
    Purpose:
        Queries gitlab for tags in a given container registry repository
    Args:
        gitlab_token: Gitlab access token
        gitlab_url: URL to the gitlab server instance
        namespace: Namespace of the project
        project_name: Name of the project
        repo_id: ID of the container registry repository
    Return:
        List of tag names
    """

    tags = []

    try:
        page = 1
        while page > 0:
            result = requests.get(
                # NOTE: the %2F can NOT be replaced with a slash. It will fail if you try. It seems namespace/project_name isn't a path, but a stand-in for the project ID.
                f"{gitlab_url}/api/v4/projects/{namespace}%2F{project_name}/registry/repositories/{repo_id}/tags?per_page=100&page={page}",
                headers={"PRIVATE-TOKEN": gitlab_token},
            )
            if result.status_code == 200:
                tags.extend([tag_info["name"] for tag_info in result.json()])
                if page < int(result.headers.get("x-total-pages", "0")):
                    page += 1
                else:
                    page = -1
            else:
                page = -1
    except Exception as err:
        logger.warning(err)
        return []

    return tags

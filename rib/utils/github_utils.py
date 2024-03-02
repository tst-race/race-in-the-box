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
    Utilities for interacting with the GitHub API
"""

# Python Library Imports
import json
import logging
import requests
import os
from pydantic import BaseModel
from typing import Dict, Optional, Tuple

# Local Python Library Imports
from rib.utils import error_utils, network_utils, rib_utils


logger = logging.getLogger(__name__)


rib_config = rib_utils.load_race_global_configs()


###
# Config Utilities
###


class GitHubConfig(BaseModel):
    """GitHub configuration"""

    access_token: Optional[str] = None
    username: Optional[str] = None
    default_org: Optional[str] = None
    default_race_images_org: Optional[str] = None
    default_race_images_repo: Optional[str] = None
    default_race_images_tag: Optional[str] = None
    default_race_core_org: Optional[str] = None
    default_race_core_repo: Optional[str] = None
    default_race_core_source: Optional[str] = None


def default_github_config_path() -> str:
    """
    Purpose:
        Gets the default path to the GitHub configuration file.

    Args:
        N/A

    Returns:
        Absolute path to GitHub configuration file
    """
    return os.path.join(rib_config.RIB_PATHS["docker"]["github"], "config.json")


def read_github_config(filename: Optional[str] = None) -> GitHubConfig:
    """
    Purpose:
        Reads the persisted GitHub configuration.

    Args:
        filename: If provided, read from the specified file rather than the default

    Returns:
        Persisted config object
    """
    if not filename:
        filename = default_github_config_path()
    if os.path.exists(filename):
        try:
            return GitHubConfig.parse_file(filename)
        except Exception as err:
            raise error_utils.RIB105(filename, str(err)) from err
    return GitHubConfig()


_cached_config: Optional[GitHubConfig] = None


def _config() -> GitHubConfig:
    """Internal method to use a cached GitHub config if already read"""
    global _cached_config
    if not _cached_config:
        _cached_config = read_github_config()
    return _cached_config


def update_github_config(
    updated_config: GitHubConfig, filename: Optional[str] = None
) -> None:
    """
    Purpose:
        Updates the persisted GitHub configuration.

        The given config object will be merged with the existing config, replacing
        any values defined in the updated config object. Values omitted in the
        updated config object will remain unchanged in the persisted config.

    Args:
        updated_config: Config object with updated values
        filename: If provided, write to the specified file rather than the default

    Returns:
        N/A
    """

    config_dict = read_github_config().dict()
    updated_config_dict = updated_config.dict()

    for key, value in updated_config_dict.items():
        if value is not None:
            config_dict[key] = value

    if not filename:
        filename = default_github_config_path()
    with open(filename, "w") as out:
        json.dump(config_dict, out, indent=2, sort_keys=True)

    global _cached_config
    _cached_config = None


###
# Default Utilities
###


def default_org() -> str:
    """
    Purpose:
        Gets the default GitHub organization

    Args:
        N/A

    Returns:
        Default GitHub organization
    """
    config = _config()
    if not config.default_org:
        raise error_utils.RIB108()
    return config.default_org


def default_race_core_org() -> str:
    """Gets the default RACE core GitHub organization"""
    config = _config()
    org = config.default_race_core_org
    if not org:
        org = default_org()
    return org


def default_race_core_repo() -> str:
    """Gets the default RACE core GitHub repository"""
    config = _config()
    repo = config.default_race_core_repo
    if not repo:
        repo = "race-core"
    return repo


def default_race_core_source() -> str:
    """Gets the default RACE core release (tag)"""
    config = _config()
    if not config.default_race_core_source:
        raise error_utils.RIB106("No default race-core source configured")
    return config.default_race_core_source


def default_image(image: str, tag: Optional[str] = None) -> str:
    """
    Purpose:
        Gets the default GitHub container registry image name

    Args:
        image: Name of image within the images repository
        tag: If specified, the tag to use instead of a configured default tag

    Returns:
        GitHub container registry image name
    """
    config = _config()

    if not tag:
        tag = config.default_race_images_tag
    if not tag:
        tag = "main"

    repo = config.default_race_images_repo
    if not repo:
        repo = "race-images"

    org = config.default_race_images_org
    if not org:
        org = config.default_org
    if not org:
        org = "tst-race"

    return f"ghcr.io/{org}/{repo}/{image}:{tag}"


def apply_defaults_to_image(image: str, default_image_name: str) -> str:
    """
    Purpose:
        Apply defaults to the given image.
    Args:
        image: Given image to which to apply defaults
        default_image_name: Default image name if given image contains only a tag
    Returns:
        Fully-qualified image name with all defaults applied
    """
    # If only a tag specified, apply default domain/org/repo/name
    if image.startswith(":"):
        config = _config()

        domain = "ghcr.io"

        org = config.default_race_images_org
        if not org:
            org = default_org()

        repo = config.default_race_images_repo
        if not repo:
            repo = "race-images"

        tag = image[1:]

        return "/".join([domain, org, repo, ":".join([default_image_name, tag])])

    # Else keep image as specified
    return image


###
# Auth Utilities
###


def get_access_token() -> str:
    """Get configured access token"""
    config = _config()
    if not config.access_token:
        raise error_utils.RIB104()
    return config.access_token


def get_username() -> str:
    """Get configured account username"""
    config = _config()
    if not config.username:
        raise error_utils.RIB110()
    return config.username


###
# API Utilities
###


def _api_headers() -> Dict[str, str]:
    """Create API request headers with access token"""
    return {"Authorization": f"token {get_access_token()}"}


def download_file(
    remote_url: str,
    local_path: str,
    accept_octet_stream: bool = False,
) -> Tuple[bool, int]:
    """
    Purpose:
        Downloads a file from a remote server
    Args:
        remote_url: Remote URL for for the file to be downloaded
        local_path: Local location to which to write the downloaded file
        accept_octet_stream: Set accept headers to octet stream
    Returns:
        Tuple of success boolean and reponse status code
    """
    headers = _api_headers()
    if accept_octet_stream:
        headers["Accept"] = "application/octet-stream"
    return network_utils.download_file(remote_url, local_path, headers=headers)


def get_tag_artifacts(org: str, repo: str, tag: str) -> Dict[str, str]:
    """
    Purpose:
        Get mapping of artifacts available for a tagged release

    Args:
        org: GitHub organization
        repo: GitHub repository
        tag: Release tag

    Returns:
        Mapping of artifact names to download URLs
    """

    api_url = f"https://api.github.com/repos/{org}/{repo}/releases/tags/{tag}"
    resp = requests.get(api_url, headers=_api_headers())
    if resp.status_code != 200:
        raise error_utils.RIB109(
            f"Fetching tag artifacts list for {org}/{repo} {tag}", resp.status_code
        )

    artifacts = {}
    for asset in resp.json()["assets"]:
        artifacts[asset["name"]] = asset["url"]

    return artifacts


def download_tag_artifact(
    org: str, repo: str, tag: str, asset: str, local_path: str
) -> Tuple[bool, int, bool, str]:
    """
    Purpose:
        Downloads a tagged release artifact from GitHub

    Args:
        org: GitHub organization
        repo: GitHub repository
        tag: Release tag
        asset: Release asset
        local_path: Local location to which to write the downloaded file

    Returns:
        Tuple of success boolean, reponse status code, auth-required bool, and URI string
    """

    # Try to download using the unauthenticated URL
    public_uri = f"https://github.com/{org}/{repo}/releases/download/{tag}/{asset}"
    (success, status_code) = network_utils.download_file(public_uri, local_path)
    if success:
        return (True, status_code, False, public_uri)

    artifacts = get_tag_artifacts(org, repo, tag)
    if asset not in artifacts:
        return (False, 404, True, public_uri)

    private_uri = artifacts[asset]
    (success, status_code) = download_file(
        private_uri, local_path, accept_octet_stream=True
    )
    return (success, status_code, True, private_uri)


def get_latest_run_for_branch(
    org: str, repo: str, branch: str, asset: str, max_page=10
) -> Tuple[Optional[str], Optional[str]]:
    """
    Purpose:
        Determines the latest GitHub Actions run for the specified branch

    Args:
        org: GitHub organization
        repo: GitHub repository
        branch: Branch name
        asset: Artifact asset
        max_page: Maximum number of pages to search

    Returns:
        Tuple of workflow run URL and asset download URL if branch is found, else tuple of Nones
    """

    for page in range(1, max_page):
        api_url = f"https://api.github.com/repos/{org}/{repo}/actions/runs?branch={branch}&status=success&page={page}"
        resp = requests.get(api_url, headers=_api_headers())
        if resp.status_code != 200:
            raise error_utils.RIB109(
                f"Fetching workflow runs list for {org}/{repo} {branch=}",
                resp.status_code,
            )

        # Runs are listed in reverse-chronological order, so first satisfying run in the list
        # is the latest
        workflow_url = None
        download_url = None
        for run in resp.json()["workflow_runs"]:
            # Check artifacts for each run
            artifacts_url = run["artifacts_url"]
            download_url = _get_artifact_download_url_for_run(artifacts_url, asset)
            if download_url is not None:
                workflow_url = run["html_url"]
                logger.trace(f"Found {workflow_url=} {download_url=}")
                return (workflow_url, download_url)

    return (None, None)


def _get_artifact_download_url_for_run(url: str, asset: str) -> Optional[str]:
    """
    Invoke the workflow run artifacts API via the given URL and look for an
    artifact with the matching asset name.
    """
    logger.trace(f"Checking {url=} for {asset=}")
    resp = requests.get(url, headers=_api_headers())
    if resp.status_code == 200:
        # Check each artifact for matching asset name
        for artifact in resp.json()["artifacts"]:
            if artifact["name"] == asset:
                return artifact["archive_download_url"]

    return None


def download_branch_artifact(
    workflow_url: str, download_url: str, local_path: str
) -> Tuple[bool, int, bool, str]:
    """
    Purpose:
        Downloads the latest GitHub Actions run artifact from GitHub

    Args:
        org: GitHub organization
        repo: GitHub repository
        branch: Branch name
        asset: Artifact asset
        local_path: Local location to which to write the downloaded file

    Returns:
        Tuple of success boolean, reponse status code, auth-required bool, and URI string
    """

    if not workflow_url or not download_url:
        return (False, 404, True, "")

    (success, status_code) = download_file(download_url, local_path)
    return (success, status_code, True, workflow_url)


def download_action_run_artifact(
    org: str, repo: str, run: str, asset: str, local_path: str
) -> Tuple[bool, int, bool, str]:
    """
    Purpose:
        Downloads the latest GitHub Actions run artifact from GitHub

    Args:
        org: GitHub organization
        repo: GitHub repository
        run: Action run ID
        asset: Artifact asset
        local_path: Local location to which to write the downloaded file

    Returns:
        Tuple of success boolean, reponse status code, auth-required bool, and URI string
    """

    api_url = f"https://api.github.com/repos/{org}/{repo}/actions/runs/{run}/artifacts"
    resp = requests.get(api_url, headers=_api_headers())
    if resp.status_code != 200:
        raise error_utils.RIB109(
            f"Fetching actions artifacts list for {org}/{repo} {run}",
            resp.status_code,
        )

    download_url = None
    for artifact in resp.json()["artifacts"]:
        if artifact["name"] == asset:
            download_url = artifact["archive_download_url"]
            break

    if not download_url:
        return (False, 404, True, api_url)

    workflow_url = f"https://github.com/repos/{org}/{repo}/actions/runs/{run}"

    (success, status_code) = download_file(download_url, local_path)
    return (success, status_code, True, workflow_url)

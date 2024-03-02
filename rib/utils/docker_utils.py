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
        Docker Utilities for interfacing with Docker
"""

# Python Library Imports
from copy import deepcopy
import docker
import json
import logging
import os
import re
import requests
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Set

# Local Library Imports
from rib.utils import error_utils
from rib.utils.status_utils import ContainerStatus, evaluate_container_status


logger = logging.getLogger(__name__)


###
# Base Docker Functions
###


def _get_low_level_client() -> docker.APIClient:
    """Get the low level Docker API client.

    Args:
        N/A
    Returns:
        [type]: The low level Docker API client
    """
    return docker.APIClient()


def get_docker_client() -> docker.client:
    """
    Purpose:
        Get the docker client from the users environment (Verify its connected)
    Args:
        N/A
    Returns:
        docker_client (Docker Client Object): The docker client object connected to the
            Docker API
    """

    return docker.from_env()


def verify_docker_status() -> None:
    """
    Purpose:
        Verify the status of Docker
    Args:
        docker_client (Docker Client Object): The docker client object connected to the
            Docker API
    Returns:
        N/A
    Raises:
        error_utils.RIB203: If rib cannot connect to the host docker client
        error_utils.RIB202: All other errors, reports up to CLI
    """

    docker_client = get_docker_client()

    try:
        docker_client.info()
    except requests.exceptions.ConnectionError:
        raise error_utils.RIB203() from None
    except Exception as err:
        raise error_utils.RIB202(err) from None


def get_deployment_container_status(
    deployment_name: str, rib_mode: str = "local"
) -> Dict[str, ContainerStatus]:
    """
    Purpose:
        Get the status of all containers associated with the given deployment
    Args:
        deployment_name: Name of the deployment (i.e., value of the race.rib.deployment-name label)
        rib_mode: Deployment type (i.e., value of the race.rib.deployment-type label)
    Return:
        Mapping of container name to container status
    """

    container_status = {}

    docker_client = get_docker_client()
    docker_api = _get_low_level_client()

    docker_containers = docker_client.containers.list(
        all=True,
        filters={
            "label": [
                f"race.rib.deployment-name={deployment_name}",
                f"race.rib.deployment-type={rib_mode}",
            ]
        },
    )

    for docker_container in docker_containers:
        container_info = docker_api.inspect_container(docker_container.name)
        container_status[docker_container.name] = evaluate_container_status(
            state=container_info["State"]["Status"],
            # containers with no healthcheck have no State.Health.Status, so they're always healthy
            status=container_info["State"].get("Health", {}).get("Status", "healthy"),
        )

    return container_status


def check_for_expected_containers(
    expected_containers: Set[str],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Purpose:
        Check for running containers from a specified list.
    Args:
        expected_containers: Set of expected containers to be running on the system
    Returns:
        running_containers: List of running containers on the system
        missing_services: List of missing containers on the system (running
            vs expected)
    """

    running_containers = set()

    # Get Running Relevant Containers
    for _, docker_containers in get_docker_containers_by_image().items():
        for docker_container in docker_containers:
            if docker_container in expected_containers:
                running_containers.add(docker_container)

    # Find missing and unexpected containers]
    missing_containers = list(expected_containers - running_containers)

    return list(running_containers), missing_containers


def get_container_health(container_name: str) -> str:
    """
    Purpose:
        Get a containers Health
    Args:
        container_name: Name of container to get health of
    Returns:
        container_health: Health of container
    """

    container_health = None

    docker_health_command = [
        "docker",
        "inspect",
        "--format='{{json .State.Health}}'",
        container_name,
    ]

    docker_health_process = subprocess.Popen(
        docker_health_command,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=False,
    )
    docker_health_process.wait()

    if docker_health_process.returncode == 0:
        container_health = "healthy"
    else:
        container_health = "unhealthy"

    return container_health


###
# Container Registry Functions
###


def login_docker_registry(
    username: str, password: str, registry: str, user_state_path: str
) -> None:
    """
    Purpose:
        Login to docker registry
    Args:
        username: username of docker registry
        password: password of docker registry
        registry: URL docker registry
        user_state_path: the volume mounted path to the RiB user's user state files
    Returns:
        N/A
    """

    # If .docker is a symlink and it's broken remove it. This will be the case
    # the first time a user uses RiB 0.5.1 since this is the first time we're
    # saving the .docker directory
    docker_credentials_path = f"{os.getenv('HOME')}/.docker"
    if os.path.islink(docker_credentials_path):
        if not os.path.exists(os.readlink(docker_credentials_path)):
            os.unlink(docker_credentials_path)

    # Docker Commands to Run
    docker_login_command = ["docker", "login", registry, "-u", username, "-p", password]

    # Run Commands Serially
    docker_login_process = subprocess.Popen(
        docker_login_command,
        shell=False,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    docker_login_process.wait()

    if "Login Succeeded" not in str(docker_login_process.stdout.read()):
        raise error_utils.RIB201()

    # Save .docker directory in user path to save login between sessions
    save_docker_credentials = ["cp", "-r", docker_credentials_path, user_state_path]
    save_docker_credentials_process = subprocess.Popen(
        save_docker_credentials,
        shell=False,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    save_docker_credentials_process.wait()


###
# RACE Specific Docker Functions
###


def get_docker_containers_by_image() -> Dict[str, docker.models.containers.Container]:
    """
    Purpose:
        Get all Docker Containers grouped by image
    Args:
        N/A
    Returns:
        docker_containers_by_image: List of the instances of the container objects
    """

    docker_containers_by_image: Dict[str, docker.models.containers.Container] = {}

    docker_client = docker.from_env()
    # Filter out containers that are still starting or unhealthy
    docker_containers = docker_client.containers.list(
        filters={"health": ["healthy", "none"]}
    )
    for docker_container in docker_containers:
        docker_container_images = docker_container.image.tags
        docker_container_name = docker_container.name

        for docker_container_image in docker_container_images:
            docker_containers_by_image.setdefault(docker_container_image, [])
            docker_containers_by_image[docker_container_image].append(
                docker_container_name
            )

    return docker_containers_by_image


def get_docker_container_by_name(
    container_name: str,
) -> docker.models.containers.Container:
    """
    Purpose:
        Get all Docker Containers by name of the container
    Args:
        container_name: name of the container
    Returns:
        docker_container (Docker Container Obj): instance of the container object
    Raises:
        Exception: If there is no matching container
    """

    docker_container = None

    docker_client = docker.from_env()
    docker_container = docker_client.containers.get(container_name)
    if not docker_container:
        raise Exception("Container does not exist")

    return docker_container


###
# Parse Functions
###


def get_container_labels(container_id: str) -> Dict[str, str]:
    """Get the labels for a given container.

    Args:
        container_id: The container ID or name.
    Returns:
        container_labels: The labels, a set of key value pairs
    """

    low_level_docker_client = _get_low_level_client()

    return (
        low_level_docker_client.inspect_container(container_id)
        .get("Config", {})
        .get("Labels", {})
    )


def get_container_label(container_id: str, label_key: str) -> Optional[str]:
    """Get the value of a specfic label for a container.

    Args:
        container_id: The container ID or name.
        label_key: The key of the label to retrieve.

    Returns:
        container_labe: The value of the label for the given key, or None
            if the key does not exist.
    """
    return get_container_labels(container_id).get(label_key)


def get_all_container_names() -> List[str]:
    """
    Purpose:
        Get a list of names of all containers (running and stopped).
    Args:
        N/A
    Returns:
        List of names of all containers.
    """

    docker_client = get_docker_client()
    containers = docker_client.containers.list(all=True)

    return [container.name for container in containers]


def get_all_running_container_names() -> List[str]:
    """Get a list of names of all running containers.

    Args:
        N/A
    Returns:
        List[str]: List of names of all running containers.
    """

    docker_client = get_docker_client()
    containers = docker_client.containers.list()

    return [container.name for container in containers]


def validate_docker_image_name(docker_image_name: str) -> bool:
    """
    Purpose:
        Validate a Docker image name.

        From Docs: A tag name must be valid ASCII and may contain lowercase and uppercase
        letters, digits, underscores, periods and dashes. A tag name may not start with
        a period or a dash and may contain a maximum of 128 characters.

        https://docs.docker.com/engine/reference/commandline/tag/

        note, container registry may be in path, so adding / and : characters
        as valid
    Args:
        docker_image_name: name of a docker image. can include repository, name,
            tag/version
    Returns:
        is_tag_valid: List of names of all running containers.
    """

    # \w\-\.\ is valid for docker image
    # \: is for the tag version
    # \/ is for container registry path (group/repo)
    # This does not check everything like docker not allowing the
    # first character to be a ., but this should catch 90%+ issues
    # That have caused weird issues
    docker_tag_matcher = re.compile(r"^[\w\-\.\:\/]{1,256}$")

    return bool(docker_tag_matcher.match(docker_image_name))


def verify_docker_tag_exists(docker_tag: str) -> None:
    """
    Purpose:
        Validate a Docker image tag exists locally or in container registry
    Args:
        docker_tag: name of a docker image + tag
    Returns:
        N/A
    Raises:
        error_utils.RIB212: when the docker_tag is not found
    """

    docker_tag_verify_command = [
        "docker",
        "manifest",
        "inspect",
        docker_tag,
    ]

    env = deepcopy(os.environ)
    start_time = time.time()
    docker_tag_verify_process = subprocess.Popen(
        docker_tag_verify_command,
        env=env,
        shell=False,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    docker_tag_verify_process.wait()
    stop_time = time.time()

    if docker_tag_verify_process.returncode != 0:
        raise error_utils.RIB212(docker_tag)


def inspect(obj_name: str) -> Dict[str, Any]:
    """
    Purpose:
        Executes a docker inspect command for the given docker object, returning the output
    Args:
        obj_name: Docker object name to be inspected
    Return:
        Docker object information
    """

    return json.loads(subprocess.check_output(["docker", "inspect", obj_name]))


class DockerImageInfo(TypedDict):
    """Summarized low-level information about a docker image"""

    tag: str
    digest: str
    created: str


def _get_image_info(image_tag: str) -> DockerImageInfo:
    """
    Purpose:
        Gets information about a specific docker image.
    Args:
        image_tag: Docker image tag or ID.
    Return:
        Docker image info.
    """

    image_info = inspect(image_tag)
    if not image_info:
        raise error_utils.RIB208([image_tag])

    image_info = image_info[0]
    if image_info.get("RepoDigests"):
        digest = image_info["RepoDigests"][0]
    else:
        digest = image_info["Id"]

    # If the image doesn't exist anymore (e.g. the image for a container was removed
    # while the continer was still running) then RepoTags will be empty.
    tag = image_info["RepoTags"][0] if image_info["RepoTags"] else None

    return DockerImageInfo(
        tag=tag,
        digest=digest,
        created=image_info["Created"],
    )


class DockerContainerInfo(TypedDict):
    """Summarized low-level information about a docker container"""

    image: DockerImageInfo
    status: str
    health: Optional[str]


def get_container_info(container_name: str) -> DockerContainerInfo:
    """
    Purpose:
        Gets information about a docker container.
    Args:
        container_name: Name or ID of the container.
    Return:
        Docker container info.
    """

    container_info = inspect(container_name)
    if not container_info:
        raise error_utils.RIB202(f"No container found with name {container_name}")
    return DockerContainerInfo(
        image=_get_image_info(container_info[0]["Image"]),
        status=container_info[0]["State"]["Status"],
        health=container_info[0]["State"].get("Health", None),
    )

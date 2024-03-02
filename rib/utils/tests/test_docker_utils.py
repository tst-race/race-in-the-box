#!/usr/bin/env python3

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
        Test File for docker_utils.py
"""

# Python Library Imports
from _pytest.monkeypatch import MonkeyPatch
import docker
import pytest
import requests
from unittest import mock

# Local Library Imports
from rib.utils import docker_utils, error_utils


###
# Mocks
###


class MockDocker(object):
    """
    Purpose:
        Mock for the docker module for testing.
    """

    def from_env(*args, **kwargs):
        """
        Purpose:
            Mock getting DockerClient from Env
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            mocked_docker_client (MockDockerClient Object): A mocked docker client
        """

        return MockDockerClient()


class MockDockerClient(object):
    """
    Purpose:
        Mock docker client for testing.
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            initialize MockDockerClient
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        self.images = MockDockerClientImages()
        self.containers = MockDockerClientContainers()

    def info(self, *args, **kwargs):
        """
        Purpose:
            Mock get_info from docker. Will return an empty dict
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            info (Dict): mocked info
        """

        return {}


class MockDockerClientImages(object):
    """
    Purpose:
        Mock for the docker module for testing.
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            initialize MockDockerClientImages
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        pass

    def list(self, *args, **kwargs):
        """
        Purpose:
            mock list functionality
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        return []

    def search(self, *args, **kwargs):
        """
        Purpose:
            mock search functionality
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        return []

    def build(self, *args, **kwargs):
        """
        Purpose:
            Mock build for docker_client.images
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            mocked_image (MockImage Object): A mocked built image
            mocked_build_logs (List of Strings): list of mocked build logs
        """

        return MockImage(), ["Build mock image"]

    def get(self, *args, **kwargs):
        """
        Purpose:
            Mock get for docker_client.images
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            mocked_image (MockImage Object): A mocked image
        """

        return MockImage()


class MockDockerClientContainers(object):
    """
    Purpose:
        Mock for the docker module for testing.
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            initialize MockDockerClientContainers
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        pass

    def list(self, *args, **kwargs):
        """
        Purpose:
            Mock list for docker_client.containers
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            mocked_containers (List of MockContainer Objects): list of mocked containers
        """

        return [MockContainer("mockContainer1"), MockContainer("mockContainer2")]

    def get(self, container_name):
        """
        Purpose:
            Mock get for docker_client.containers
        Args:
            container_name (String): Name of container
        Returns:
            mocked_container (MockImage Object): A mocked image
        """

        return MockContainer(container_name)


class MockImage(object):
    """
    Purpose:
        Mock docker module Image
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            initialize MockImage
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        self.tags = []

    def tag(self, tag_name):
        """
        Purpose:
            Mock tag for docker image
        Args:
            tag_name (String): tag to add
        Returns:
            N/A
        """

        self.tags.append(tag_name)


class MockContainer(object):
    """
    Purpose:
        Mock docker module Container
    """

    def __init__(self, name, *args, **kwargs):
        """
        Purpose:
            initialize MockContainer
        Args:
            name (String): Name of the container
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        """

        self.name = name
        self.image = MockImage()
        self.image.tag(self.name)


class MockDockerConnErr(object):
    """
    Purpose:
        Mock for the docker module for testing. Assuming conn err
    """

    def from_env(*args, **kwargs):
        """
        Purpose:
            Mock getting DockerClient from Env
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            mocked_docker_client (MockDockerClientConnErr Object): A mocked docker client
                with connection issues
        """

        return MockDockerClientConnErr()


class MockDockerClientConnErr(object):
    """
    Purpose:
        Mock docker client for testing.

        Assuming ConnErr for Docker Client.
    """

    def info(*args, **kwargs):
        """
        Purpose:
            Mock get_info from docker. Will raise exception since the docker
            client is not connected
        Args:
            *args (Tuple): all possible arugments, not used.
            **kwargs (Dict): : all possible keyword arugments, not used.
        Returns:
            N/A
        """

        raise requests.exceptions.ConnectionError()


###
# Data Fixtures
###


@pytest.fixture()
def example_docker_registry():
    """
    Purpose:
        Fixture of a Example Docker Registry. Includes the repository for
        container registry
    Args:
        N/A
    Return:
        example_docker_registry (String): Example Docker Registry. Includes the
            repository for container registry
    """

    return "ghcr.io/tst-race/race-in-the-box"


@pytest.fixture()
def example_docker_image_name():
    """
    Purpose:
        Fixture of a Example Docker Image Name
    Args:
        N/A
    Return:
        example_docker_image_name (String): Example Docker Image Name
    """

    return "race-linux-server"


@pytest.fixture()
def example_docker_image_tag():
    """
    Purpose:
        Fixture of a Example Docker Image Tag
    Args:
        N/A
    Return:
        example_docker_image_tag (String): Example Docker Image Tag
    """

    return "0.2.0"


@pytest.fixture()
def example_docker_build_args():
    """
    Purpose:
        Fixture of a Example Docker Build Args for Building Images
    Args:
        N/A
    Return:
        example_docker_build_args (List of Strings): Example build args that may be
            passed in to rib docker commands
    """

    return [
        "TEST_ARG_1=1",
        "TEST_ARG_2=2=",
        "TEST_ARG_3='some_test_with_quotes'",
        'TEST_ARG_4=\'"someescapedtext"',
    ]


###
# Method Fixtures
###


@pytest.fixture(scope="function", autouse=False)
def docker_mocks(monkeypatch):
    """
    Purpose:
        Set up mocks for Docker
    Args:
        monkeypatch (pytest fixture): monkeypatch allows for patching of
            methods/functions/modules in other files. better testing with mocks
    """

    monkeypatch.setattr(docker, "from_env", MockDocker.from_env)


@pytest.fixture(scope="function", autouse=False)
def docker_mocks_not_connected(monkeypatch):
    """
    Purpose:
        Set up mocks for Docker
    Args:
        monkeypatch (pytest fixture): monkeypatch allows for patching of
            methods/functions/modules in other files. better testing with mocks
    """

    monkeypatch.setattr(docker, "from_env", MockDockerConnErr.from_env)


###
# Test Base Docker Functions
###


def test_get_docker_client(docker_mocks):
    """
    Purpose:
        Test that get_docker_client gets a docker client from the env
    Args:
        docker_mocks (pytest fixture): None. fixture is used to set up docker mocks
            before run
    """

    # Make call
    docker_client = docker_utils.get_docker_client()

    # Confirm we got our Mock Back
    assert type(docker_client) == MockDockerClient


def test_verify_docker_status_connected(docker_mocks):
    """
    Purpose:
        Test that verify_docker_status passes for a connected client
    Args:
        docker_mocks (pytest fixture): None. fixture is used to set up docker mocks
            before run
    """

    # Make calls
    docker_utils.verify_docker_status()

    # Assertion is that there should be no raise, so just assert True
    assert True


def test_verify_docker_status_not_connected(docker_mocks_not_connected):
    """
    Purpose:
        Test that verify_docker_status fails for a non-connected client
    Args:
        docker_mocks_not_connected (pytest fixture): None. fixture is used to set up docker mocks
            before run of a docker that is not properly connected
    """

    # Make calls
    with pytest.raises(error_utils.RIB203):
        docker_utils.verify_docker_status()

    # Assertion is that there should be no raise, so just assert True
    assert True


###
# Test RACE Specific Docker Functions
###


def test_get_docker_containers_by_image(docker_mocks):
    """
    Purpose:
        Test that get_docker_containers_by_image works for a connected client.

        Should return mocked containers/image tags
    Args:
        docker_mocks (pytest fixture): None. fixture is used to set up docker mocks
            before run
    """

    expected_docker_containers_by_image = {
        "mockContainer1": ["mockContainer1"],
        "mockContainer2": ["mockContainer2"],
    }

    docker_containers_by_image = docker_utils.get_docker_containers_by_image()

    assert expected_docker_containers_by_image == docker_containers_by_image


def test_get_docker_container_by_name(docker_mocks):
    """
    Purpose:
        Test that get_docker_container_by_name works for a connected client.

        Should return a conatiner for mockContainer1 and raise exception if it
        does not exist
    Args:
        docker_mocks (pytest fixture): None. fixture is used to set up docker mocks
            before run
    """

    expected_container_name = "mockContainer2"
    docker_container_by_name = docker_utils.get_docker_container_by_name(
        expected_container_name
    )
    assert docker_container_by_name.name == expected_container_name


def test_check_for_expected_containers(docker_mocks):
    """
    Purpose:
        Test that test_check_for_expected_containers works for a connected client.

        Should return a conatiners based on the mock
    Args:
        docker_mocks (pytest fixture): None. fixture is used to set up docker mocks
            before run
    """

    expected_docker_containers = set(["mockContainer1", "mockContainer2"])

    (
        running_containers,
        missing_containers,
    ) = docker_utils.check_for_expected_containers(expected_docker_containers)

    assert missing_containers == []
    assert running_containers == list(expected_docker_containers)


###
# Test Container Health
###


@mock.patch("subprocess.Popen")
def test_get_container_health_healthy(mock_subprocess_popen):
    """
    Purpose:
        Test that get_container_health returns "healthy" with a 0 return
        code
    Args:
        mock_subprocess_popen (mock path obj): a patch object for subprocess.Popen
    """

    attrs = {"wait.return_value": None, "returncode": 0}

    subprocess_mock = mock.Mock()
    subprocess_mock.configure_mock(**attrs)

    mock_subprocess_popen.return_value = subprocess_mock

    container_health = docker_utils.get_container_health("test")

    assert container_health == "healthy"


@mock.patch("subprocess.Popen")
def test_get_container_health_unhealthy(mock_subprocess_popen):
    """
    Purpose:
        Test that get_container_health returns "healthy" with a 0 return
        code
    Args:
        mock_subprocess_popen (mock path obj): a patch object for subprocess.Popen
    """

    attrs = {"wait.return_value": None, "returncode": 1}

    subprocess_mock = mock.Mock()
    subprocess_mock.configure_mock(**attrs)

    mock_subprocess_popen.return_value = subprocess_mock

    container_health = docker_utils.get_container_health("test")

    assert container_health == "unhealthy"


###
# validate_docker_image_name
###


def test_validate_docker_image_name_valid() -> int:
    """
    Purpose:
        Test that validate_docker_image_name returns True for valid names
    """

    valid_docker_images = [
        "registry.example.com/org/image-name",
        "registry/org/image-name",
        "registry/image-name",
        "image-name",
        "registry.example.com/org/image-name:version",
        "registry/org/image-name:version",
        "registry/image-name:version",
        "image-name:version",
        "registryELB-999514288.eu-west-1.elb.amazonaws.com:5000/ghorvath/test-haproxy:latest",
        "docker.elastic.co/elasticsearch/elasticsearch:7.6.0",
        "ghcr.io/tst-race/race-images/race-base:1.1.0",
        "ghcr.io/tst-race/race-images/race-base:1.1.1",
        "ghcr.io/tst-race/race-images/race-base:latest",
        "ghcr.io/tst-race/race-images/race-base:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-base:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-compile:1.1.0",
        "ghcr.io/tst-race/race-images/race-compile:1.1.1",
        "ghcr.io/tst-race/race-images/race-compile:latest",
        "ghcr.io/tst-race/race-images/race-compile:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-compile:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-ndk:1.1.0",
        "ghcr.io/tst-race/race-images/race-ndk:1.1.1",
        "ghcr.io/tst-race/race-images/race-ndk:latest",
        "ghcr.io/tst-race/race-images/race-ndk:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-ndk:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-runtime:1.1.0",
        "ghcr.io/tst-race/race-images/race-runtime:1.1.1",
        "ghcr.io/tst-race/race-images/race-runtime:latest",
        "ghcr.io/tst-race/race-images/race-runtime:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-runtime:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-client-complete:1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-server-complete:1.1.1",
        "ghcr.io/tst-race/race-images/race-android-x86_64-client:1.1.0",
        "ghcr.io/tst-race/race-images/race-android-x86_64-client:1.1.1",
        "ghcr.io/tst-race/race-images/race-android-x86_64-client:latest",
        "ghcr.io/tst-race/race-images/race-android-x86_64-client:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-android-x86_64-client:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-android-arm64-v8a-client:1.1.0",
        "ghcr.io/tst-race/race-images/race-android-arm64-v8a-client:1.1.1",
        "ghcr.io/tst-race/race-images/race-android-arm64-v8a-client:latest",
        "ghcr.io/tst-race/race-images/race-android-arm64-v8a-client:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-android-arm64-v8a-client:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-client:1.1.0",
        "ghcr.io/tst-race/race-images/race-linux-client:1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-client:latest",
        "ghcr.io/tst-race/race-images/race-linux-client:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-linux-client:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-server:1.1.0",
        "ghcr.io/tst-race/race-images/race-linux-server:1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-server:latest",
        "ghcr.io/tst-race/race-images/race-linux-server:rc-1.1.0",
        "ghcr.io/tst-race/race-images/race-linux-server:rc-1.1.1",
        "ghcr.io/tst-race/race-core/race-sdk:1.1.0",
        "ghcr.io/tst-race/race-core/race-sdk:1.1.1",
        "ghcr.io/tst-race/race-core/race-sdk:latest",
        "ghcr.io/tst-race/race-core/race-sdk:rc-1.1.0",
        "ghcr.io/tst-race/race-core/race-sdk:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-linux-client:1.0.0",
        "ghcr.io/tst-race/race-in-the-box/race-in-the-box:1.1.0",
        "ghcr.io/tst-race/race-in-the-box/race-in-the-box:1.1.1",
        "ghcr.io/tst-race/race-in-the-box/race-in-the-box:1.1.2",
        "ghcr.io/tst-race/race-in-the-box/race-in-the-box:rc-1.1.0",
        "ghcr.io/tst-race/race-in-the-box/race-in-the-box:rc-1.1.0:latest",
        "ghcr.io/tst-race/race-in-the-box/race-in-the-box:rc-1.1.1",
        "ghcr.io/tst-race/race-images/race-core/twosix-whiteboard:0.1.2",
        "ghcr.io/tst-race/race-images/race-linux-client:latest",
        "ghcr.io/tst-race/race-images/race-linux-server:latest",
        "jaegertracing/jaegerquery:1.18",
        "python:3.7",
        "python:3.8",
        "race-base:1.1.1",
        "race-base:latest",
        "race-compile:1.1.1",
        "race-in-the-box:1.1.0",
        "race-in-the-box:1.1.1",
        "race-in-the-box:1.1.2",
        "race-linux-client:1.1.1",
        "race-linux-client:latest",
        "race-linux-client-complete:1.1.1",
        "race-linux-client-complete:latest",
        "race-linux-server:1.1.1",
        "race-linux-server:latest",
        "race-linux-server-complete:1.1.1",
        "race-linux-server-complete:latest",
        "race-ndk:1.1.1",
        "race-runtime:1.1.1",
        "race-runtime:latest",
        "race-sdk:1.1.1",
        "redis:6.0.6",
    ]

    for docker_image in valid_docker_images:
        assert docker_utils.validate_docker_image_name(docker_image) == True


def test_validate_docker_image_name_invalid() -> int:
    """
    Purpose:
        Test that validate_docker_image_name returns False for invalid names
    """

    invalid_docker_images = [
        "invalid=",
        "invalid,",
    ]

    for docker_image in invalid_docker_images:
        assert docker_utils.validate_docker_image_name(docker_image) == False

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
    Tests for race_node_utils.py
"""

# Python Library Imports
import pytest
from mock import MagicMock, patch
from typing import Dict, Optional

# Local Library Imports
from rib.utils import race_node_utils, redis_utils


###
# Mocks/fixtures
###


@pytest.fixture
def mock_redis_client() -> MagicMock:
    """
    Purpose:
        Creates a mock redis client instance
    """
    return MagicMock()


@pytest.fixture(autouse=True)
def mock_create_redis_client(mock_redis_client: MagicMock) -> None:
    """
    Purpose:
        Monkeypatches the return value for `redis_utils.create_redis_client`.
    Args:
        N/A
    Return:
        N/A
    """
    redis_utils.create_redis_client = MagicMock(return_value=mock_redis_client)


def mock_redis_client_get(values: Dict[str, Optional[str]]) -> MagicMock:
    """
    Purpose:
        Creates a monkeypatched `get` function for a mock redis client that returns
        values according to the given mapping of mock values
    Args:
        values: Dictionary of mock keys to return values
    Return:
        Mocked `get` function
    """
    return MagicMock(side_effect=lambda key: values.get(key))


###
# Tests
###


################################################################################
# race_node_utils.get_daemon_status
################################################################################


@patch("rib.utils.redis_utils.is_connected", MagicMock(return_value=False))
def test_get_daemon_status_when_not_connected(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get({})

    race_node_interface = race_node_utils.RaceNodeInterface()
    daemon_status = race_node_interface.get_daemon_status("race-client-00001")
    assert daemon_status["is_alive"] == False
    assert daemon_status["installed"] == False


def test_get_daemon_status_when_no_is_alive_key_or_status_key_exists(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get({})

    race_node_interface = race_node_utils.RaceNodeInterface()
    daemon_status = race_node_interface.get_daemon_status("race-client-00001")
    assert daemon_status["is_alive"] == False
    assert daemon_status["installed"] == False


def test_get_daemon_status_when_no_is_alive_key_exists(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get(
        {"race.node.status:race-client-00001": '{"installed":true}'}
    )

    race_node_interface = race_node_utils.RaceNodeInterface()
    daemon_status = race_node_interface.get_daemon_status("race-client-00001")
    assert daemon_status["is_alive"] == False
    assert daemon_status["installed"] == True


def test_get_daemon_status_when_no_status_key_exists(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get(
        {"race.node.is.alive:race-client-00001": "true"}
    )

    race_node_interface = race_node_utils.RaceNodeInterface()
    daemon_status = race_node_interface.get_daemon_status("race-client-00001")
    assert daemon_status["is_alive"] == True
    assert daemon_status["installed"] == False


def test_get_daemon_status_when_all_keys_exist(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get(
        {
            "race.node.is.alive:race-client-00001": "true",
            "race.node.status:race-client-00001": '{"installed":true}',
        }
    )

    race_node_interface = race_node_utils.RaceNodeInterface()
    daemon_status = race_node_interface.get_daemon_status("race-client-00001")
    assert daemon_status["is_alive"] == True
    assert daemon_status["installed"] == True


################################################################################
# race_node_utils.get_app_status
################################################################################


def test_get_app_status_when_no_is_alive_key_or_status_key_exists(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get({})

    race_node_interface = race_node_utils.RaceNodeInterface()
    app_status = race_node_interface.get_app_status("race-client-00001")
    assert app_status["is_alive"] == False
    assert app_status["timestamp"] == ""


def test_get_app_status_when_no_is_alive_key_exists(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get(
        {"race.app.status:race-client-00001": '{"timestamp":"now"}'}
    )

    race_node_interface = race_node_utils.RaceNodeInterface()
    app_status = race_node_interface.get_app_status("race-client-00001")
    assert app_status["is_alive"] == False
    assert app_status["timestamp"] == "now"


def test_get_app_status_when_no_status_key_exists(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get(
        {"race.app.is.alive:race-client-00001": "true"}
    )

    race_node_interface = race_node_utils.RaceNodeInterface()
    app_status = race_node_interface.get_app_status("race-client-00001")
    assert app_status["is_alive"] == True
    assert app_status["timestamp"] == ""


def test_get_app_status_when_all_keys_exist(mock_redis_client):
    mock_redis_client.get = mock_redis_client_get(
        {
            "race.app.is.alive:race-client-00001": "true",
            "race.app.status:race-client-00001": '{"timestamp":"now"}',
        }
    )

    race_node_interface = race_node_utils.RaceNodeInterface()
    app_status = race_node_interface.get_app_status("race-client-00001")
    assert app_status["is_alive"] == True
    assert app_status["timestamp"] == "now"

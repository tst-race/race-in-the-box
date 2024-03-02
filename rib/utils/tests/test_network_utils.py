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
        Test File for network_utils.py
"""

# Python Library Imports
import os
import pytest
from typing import Any, Dict

# Local Library Imports
from rib.utils import network_utils


###
# Fixtures
###


@pytest.fixture
def os_environ() -> Dict[str, Any]:
    old_environ = dict(os.environ)
    try:
        yield os.environ
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


###
# Mocked Functions
###


# N/A


###
# Tests
###


def test_get_public_ip_works(requests_mock: object) -> None:
    """
    Purpose:
        Test that `get_public_ip` returns the API
    Args:
        requests_mock (requests Obj): the mock of the requests.
            This is a built-in mock object: https://requests-mock.readthedocs.io/en/latest/mocker.html
    """

    expected_ip = "1.2.3.4"

    # Mocking IP Calls
    requests_mock.register_uri(
        "GET", "https://checkip.amazonaws.com", text=expected_ip, status_code=200
    )
    found_ip = network_utils.get_public_ip()

    assert expected_ip == found_ip


def test_get_public_ip_fails(requests_mock: object) -> None:
    """
    Purpose:
        Test that `get_public_ip` fails when get request fails
    Args:
        requests_mock (requests Obj): the mock of the requests
    """

    # Mocking IP Calls
    requests_mock.register_uri(
        "GET", "https://checkip.amazonaws.com", text="failed", status_code=500
    )

    with pytest.raises(Exception, match=r".*Could not get IP Address.*"):
        public_ip = network_utils.get_public_ip()


def test_get_lan_ip_works(os_environ) -> None:
    os_environ["HOST_LAN_IP_ADDRESS"] = "127.0.0.1"
    assert "127.0.0.1" == network_utils.get_lan_ip()


def test_get_lan_ip_fails(os_environ) -> None:
    if "HOST_LAN_IP_ADDRESS" in os_environ:
        del os_environ["HOST_LAN_IP_ADDRESS"]
    with pytest.raises(Exception, match=r".*Host IP address not set.*"):
        network_utils.get_lan_ip()

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
        Test File for ssh_utils.py
"""

# Python Library Imports
import os
import sys
import paramiko
import pathlib
import pytest
import socket
from Crypto.PublicKey import RSA
from mock import patch
from unittest.mock import MagicMock
from unittest import mock

# Local Library Imports
from rib.utils import error_utils, ssh_utils


###
# Mocks/Data Fixtures
###


@pytest.fixture()
def rsa_private_key_filename(tmp_path: pathlib.PosixPath) -> str:
    """
    Purpose:
        Fixture of an example keyfile on disk (saved to temp path)
    Args:
        tmp_path: temporary path on disk to write file to
    Return:
        rsa_private_key_filename: example filename of an RSA private key
    """

    rsa_private_key_filename = tmp_path / "rsa.pem"
    rsa_private_key = RSA.generate(2048)
    with open(rsa_private_key_filename, "wb") as rsa_private_key_file_obj:
        rsa_private_key_file_obj.write(rsa_private_key.export_key("PEM"))

    return rsa_private_key_filename


@pytest.fixture()
@patch("getpass.getpass", MagicMock(return_value=None))
def rsa_private_key(rsa_private_key_filename) -> str:
    """
    Purpose:
        Fixture of an example keyfile on disk (saved to temp path)
    Args:
        rsa_private_key_filename: example filename of an RSA private key
    Return:
        rsa_private_key: loaded RSA private key
    """

    key_obj, key_type = ssh_utils.get_ssh_key_from_file(rsa_private_key_filename)

    return key_obj


###
# Test Functions
###


# SSH Key Functions


################################################################################
# get_rib_ssh_key
################################################################################


@patch("rib.utils.ssh_utils.get_ssh_key_from_file", MagicMock(return_value=(None)))
@patch("paramiko.Agent")
def test_get_rib_ssh_key_from_agent(agent, rsa_private_key) -> int:
    """
    Purpose:
        Test that get_rib_ssh_key uses key from ssh-agent
    Args:
        agent: Mocked paramiko Agent class
        rsa_private_key: Private key test fixture
    """
    agent.return_value.get_keys.return_value = (rsa_private_key,)
    assert ssh_utils.get_rib_ssh_key() == rsa_private_key


@patch("rib.utils.ssh_utils.get_ssh_key_from_file")
@patch("paramiko.Agent")
def test_get_rib_ssh_key_from_file(
    agent, get_ssh_key_from_file, rsa_private_key
) -> int:
    """
    Purpose:
    Args:
        agent: Mocked paramiko Agent class
        get_ssh_key_from_file: Mocked ssh_utils.get_ssh_key_from_file function
        rsa_private_key: Private key test fixture
    """
    agent.return_value.get_keys.return_value = ()
    get_ssh_key_from_file.return_value = (rsa_private_key, "rsa")
    assert ssh_utils.get_rib_ssh_key() == rsa_private_key


################################################################################
# get_ssh_key_from_file
################################################################################


@patch("getpass.getpass", MagicMock(return_value=None))
def test_get_ssh_key_from_file_rsa(rsa_private_key_filename) -> int:
    """
    Purpose:
        Test get_ssh_key_from_file returns an rsa key object
    Args:
        rsa_private_key_filename: example filename of an RSA private key
    """

    key_obj, key_type = ssh_utils.get_ssh_key_from_file(rsa_private_key_filename)

    assert isinstance(key_obj, paramiko.rsakey.RSAKey)
    assert key_type == "rsa"


# SSH Client Functions


################################################################################
# connect_ssh_client
################################################################################


@patch("paramiko.SSHClient", MagicMock())
def test_connect_ssh_client_return_client(rsa_private_key) -> int:
    """
    Purpose:
        Test connect_ssh_client succeeds
    Args:
        rsa_private_key: loaded RSA private key
    """

    returned_ssh_client = ssh_utils.connect_ssh_client(
        "fake_host", "fake_user", rsa_private_key, port=22, timeout=10
    )

    assert returned_ssh_client.set_missing_host_key_policy.call_count == 1
    assert returned_ssh_client.connect.call_count == 1


################################################################################
# disconnect_ssh_client
################################################################################


@patch("paramiko.SSHClient", MagicMock())
def test_connect_ssh_client_closes_client() -> int:
    """
    Purpose:
        Test connect_ssh_client succeeds
    Args:
        N/A
    """

    ssh_client = paramiko.SSHClient()
    ssh_utils.disconnect_ssh_client(ssh_client)

    assert ssh_client.close.call_count == 1


@patch("paramiko.SSHClient", MagicMock())
def test_connect_ssh_client_excepts() -> int:
    """
    Purpose:
        Test connect_ssh_client excepts
    Args:
        N/A
    """

    ssh_client = paramiko.SSHClient()
    ssh_client.close.side_effect = Exception()

    with pytest.raises(error_utils.RIB006) as raise_err:
        ssh_utils.disconnect_ssh_client(ssh_client)


################################################################################
# check_ssh_client_connected
################################################################################


@patch("paramiko.SSHClient", MagicMock())
def test_check_ssh_client_connected_connected(rsa_private_key) -> int:
    """
    Purpose:
        Test check_ssh_client_connected returns open
    Args:
        N/A
    """

    class MockConnectedTransport:
        """
        Mock active transport
        """

        def is_active(self):
            return True

    ssh_client = paramiko.SSHClient()
    ssh_client.get_transport.return_value = MockConnectedTransport()
    ssh_utils.check_ssh_client_connected(ssh_client)


@patch("paramiko.SSHClient", MagicMock())
def test_check_ssh_client_connected_disconnected() -> int:
    """
    Purpose:
        Test check_ssh_client_connected returns closed
    Args:
        N/A
    """

    class MockDisconnectedTransport:
        """
        Mock disconnected transport
        """

        def is_active(self):
            return False

    ssh_client = paramiko.SSHClient()
    ssh_client.get_transport.return_value = MockDisconnectedTransport()
    ssh_client.check_ssh_client_connected(ssh_client)


################################################################################
# run_ssh_command
################################################################################


# SCP Functions


################################################################################
# connect_scp_client
################################################################################


################################################################################
# check_scp_client_connected
################################################################################


################################################################################
# scp_file_or_dir
################################################################################

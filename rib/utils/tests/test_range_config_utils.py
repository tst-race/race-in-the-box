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
    Tests for range_config_utils.py
"""

# Python Library Imports
import pytest
from unittest import TestCase

# Local Library Imports
from rib.utils import error_utils, range_config_utils


def test_create_local_range_config():
    actual_range_config = range_config_utils.create_local_range_config(
        name="test-config",
        android_client_count=1,
        linux_client_count=1,
        linux_server_count=2,
        bastion={"ip": "127.0.0.1"},
    )
    expected_range_config = {
        "range": {
            "name": "test-config",
            "bastion": {"ip": "127.0.0.1"},
            "RACE_nodes": [
                {
                    "name": "race-client-00001",
                    "type": "client",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-client-00002",
                    "type": "client",
                    "enclave": "global",
                    "environment": "phone",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "android",
                    "architecture": "x86_64",
                    "uiEnabled": False,
                },
                {
                    "name": "race-server-00001",
                    "type": "server",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-server-00002",
                    "type": "server",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
            ],
            "services": [],
            "enclaves": [{"name": "global", "ip": "localhost", "port_mapping": {}}],
        }
    }
    TestCase().assertDictEqual(expected_range_config, actual_range_config)


def test_create_bootstrap_range_config():
    actual_range_config = range_config_utils.create_local_range_config(
        name="test-config",
        android_client_count=3,
        android_client_uninstalled_count=1,
        android_ui_enabled_patterns=["race-client-*"],
        linux_client_count=3,
        linux_client_uninstalled_count=2,
        linux_gpu_client_count=1,
        linux_server_count=3,
        linux_server_uninstalled_count=1,
        linux_gpu_server_count=1,
        bastion={"ip": "127.0.0.1"},
    )
    expected_range_config = {
        "range": {
            "name": "test-config",
            "bastion": {"ip": "127.0.0.1"},
            "RACE_nodes": [
                {
                    "name": "race-client-00001",
                    "type": "client",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-client-00002",
                    "type": "client",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": False,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-client-00003",
                    "type": "client",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": False,
                    "gpu": True,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-client-00004",
                    "type": "client",
                    "enclave": "global",
                    "environment": "phone",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "android",
                    "architecture": "x86_64",
                    "uiEnabled": True,
                },
                {
                    "name": "race-client-00005",
                    "type": "client",
                    "enclave": "global",
                    "environment": "phone",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "android",
                    "architecture": "x86_64",
                    "uiEnabled": True,
                },
                {
                    "name": "race-client-00006",
                    "type": "client",
                    "enclave": "global",
                    "environment": "phone",
                    "nat": False,
                    "identities": [],
                    "genesis": False,
                    "gpu": False,
                    "bridge": False,
                    "platform": "android",
                    "architecture": "x86_64",
                    "uiEnabled": True,
                },
                {
                    "name": "race-server-00001",
                    "type": "server",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-server-00002",
                    "type": "server",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": True,
                    "gpu": False,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
                {
                    "name": "race-server-00003",
                    "type": "server",
                    "enclave": "global",
                    "environment": "any",
                    "nat": False,
                    "identities": [],
                    "genesis": False,
                    "gpu": True,
                    "bridge": False,
                    "platform": "linux",
                    "architecture": "x86_64",
                },
            ],
            "services": [],
            "enclaves": [{"name": "global", "ip": "localhost", "port_mapping": {}}],
        }
    }
    TestCase().assertDictEqual(expected_range_config, actual_range_config)

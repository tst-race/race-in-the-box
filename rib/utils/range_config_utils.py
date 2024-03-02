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
        Utilities for parsing and generating range configs
"""

# Python Library Imports
import re
from typing import Any, Dict, List, Mapping, Optional

# Local Python Library Imports
from rib.utils import error_utils, rib_utils


RIB_CONFIG = rib_utils.load_race_global_configs()


def create_local_range_config(
    name: str,
    android_client_count: int,
    linux_client_count: int,
    linux_server_count: int,
    android_client_arch: str = "x86_64",
    linux_client_arch: str = "x86_64",
    linux_server_arch: str = "x86_64",
    android_client_uninstalled_count: int = 0,
    linux_client_uninstalled_count: int = 0,
    linux_server_uninstalled_count: int = 0,
    android_client_bridge_count: int = 0,
    linux_client_bridge_count: int = 0,
    linux_server_bridge_count: int = 0,
    linux_gpu_client_count: int = 0,
    linux_gpu_server_count: int = 0,
    registry_client_count: int = 0,
    registry_client_arch: str = "x86_64",
    registry_client_uninstalled_count: int = 0,
    gpu_registry_client_count: int = 0,
    bastion: Optional[Mapping[str, Any]] = None,
    android_ui_enabled_patterns: Optional[List[str]] = None,
) -> Mapping[Any, Any]:
    """
    Purpose:
        Creates a valid range-config with the specified number of clients
        and servers for local deployment (single enclave, no services or identities).
    Args:
        name: Name of the deployment
        android_client_count: Number of Android client nodes
        android_client_arch: Architecture of managed Android client nodes
        android_client_uninstalled_count: Number of Android client nodes without RACE
            installed
        android_client_bridge_count: Number of Android client nodes for bridge mode
        android_ui_enabled_patterns: Patterns of Android client names for which
            to enable user input UI
        linux_client_count: Number of Linux client nodes
        linux_client_arch: Architecture of managed Linux client nodes
        linux_client_uninstalled_count: Number of Linux client nodes without RACE
            installed
        linux_client_bridge_count: Number of Linux client nodes for bridge mode
        linux_server_count: Number of Linux server nodes
        linux_server_arch: Architecture of managed Linux server nodes
        linux_server_uninstalled_count: Number of Linux server nodes without RACE
            installed
        linux_server_bridge_count: Number of Linux server nodes for bridge mode
        linux_gpu_client_count: Number of Linux client nodes that have GPU support
        linux_gpu_server_count: Number of Linux server nodes that have GPU support
        registry_client_count: Number of artifact manager registry client nodes
        registry_client_arch: Architecture of registry client nodes
        registry_client_uninstalled_count: Number of artifact manager registry client nodes without RACE installed
        gpu_registry_client_count: Number of artifact manager registry client nodes with GPU support
        bastion: Bastion configuration
    Returns:
        Range-config dictionary
    """

    if android_client_count + linux_client_count + linux_server_count == 0:
        raise error_utils.RIB308(name, "Must include at least one node")

    # Verify linux uninstalled count is a subset of linux client count
    if (
        linux_client_uninstalled_count
        and linux_client_count < linux_client_uninstalled_count
    ):
        raise error_utils.RIB336(
            base_param="linux client count",
            comparison="greater than or equal to",
            subset_param="linux client uninstalled count",
        )
    # Verify android uninstalled count is a subset of android client count
    if (
        android_client_uninstalled_count
        and android_client_count < android_client_uninstalled_count
    ):
        raise error_utils.RIB336(
            base_param="android client count",
            comparison="greater than or equal to",
            subset_param="android client uninstalled count",
        )
    # Verify at least one genesis client when any are uninstalled
    if (linux_client_count + android_client_count) - (
        linux_client_uninstalled_count + android_client_uninstalled_count
    ) <= 0:
        raise error_utils.RIB336(
            base_param="genesis client count",
            comparison="greater than",
            subset_param="uninstalled client count",
        )
    # ensure at least one genesis linux server
    if (
        linux_server_uninstalled_count
        and linux_server_count <= linux_server_uninstalled_count
    ):
        raise error_utils.RIB336(
            base_param="linux server count",
            comparison="greater than",
            subset_param="linux server uninstalled count",
        )

    # bridge mode checks
    if linux_client_bridge_count and linux_client_count < linux_client_bridge_count:
        raise error_utils.RIB336(
            base_param="linux client count",
            comparison="greater than or equal to",
            subset_param="linux client bridge count",
        )
    if linux_server_bridge_count and linux_server_count < linux_server_bridge_count:
        raise error_utils.RIB336(
            base_param="linux server count",
            comparison="greater than or equal to",
            subset_param="linux server bridge count",
        )
    if (
        android_client_bridge_count
        and android_client_count < android_client_bridge_count
    ):
        raise error_utils.RIB336(
            base_param="android client count",
            comparison="greater than or equal to",
            subset_param="android client bridge count",
        )

    # GPU count checks
    if linux_gpu_client_count and linux_client_count < linux_gpu_client_count:
        raise error_utils.RIB336(
            base_param="linux client count",
            comparison="greater than or equal to",
            subset_param="linux gpu client count",
        )

    if linux_gpu_server_count and linux_server_count < linux_gpu_server_count:
        raise error_utils.RIB336(
            base_param="linux server count",
            comparison="greater than or equal to",
            subset_param="linux gpu server count",
        )

    if not bastion:
        bastion = {}

    range_config: Dict[str, Any] = {"name": name, "bastion": bastion}

    node_configs = []

    client_count = 0
    for num in range(linux_client_count):
        client_count += 1
        node_configs.append(
            {
                "name": f"race-client-{str(client_count).zfill(RIB_CONFIG.NODE_ID_WIDTH)}",
                "type": "client",
                "enclave": "global",
                "nat": False,
                "identities": [],
                # Genesis nodes are the first (count - uninstalled_count) nodes
                "genesis": num < linux_client_count - linux_client_uninstalled_count,
                # GPU nodes are the last (count - gpu-count) nodes
                "gpu": num >= linux_client_count - linux_gpu_client_count,
                # Bridge nodes are the last (count - bridge-count) nodes
                "bridge": num >= linux_client_count - linux_client_bridge_count,
                "platform": "linux",
                "architecture": (
                    "auto"
                    if num >= linux_client_count - linux_client_bridge_count
                    else linux_client_arch
                ),
                "environment": "any",
            }
        )

    for num in range(android_client_count):
        client_count += 1
        node_name = f"race-client-{str(client_count).zfill(RIB_CONFIG.NODE_ID_WIDTH)}"
        node_configs.append(
            {
                "name": node_name,
                "type": "client",
                "enclave": "global",
                "nat": False,
                "identities": [],
                # Genesis nodes are the first (count - uninstalled_count) nodes
                "genesis": (
                    num < android_client_count - android_client_uninstalled_count
                ),
                # Android clients are always gpu false
                "gpu": False,
                # Bridge nodes are the last (count - bridge-count) nodes
                "bridge": num >= android_client_count - android_client_bridge_count,
                "platform": "android",
                "architecture": (
                    "auto"
                    if num >= android_client_count - android_client_bridge_count
                    else android_client_arch
                ),
                "environment": "phone",
                "uiEnabled": is_ui_enabled(node_name, android_ui_enabled_patterns),
            }
        )

    server_count = 0
    for num in range(linux_server_count):
        server_count += 1
        node_configs.append(
            {
                "name": f"race-server-{str(server_count).zfill(RIB_CONFIG.NODE_ID_WIDTH)}",
                "type": "server",
                "enclave": "global",
                "nat": False,
                "identities": [],
                # Genesis nodes are the first (count - uninstalled_count) nodes
                "genesis": num < linux_server_count - linux_server_uninstalled_count,
                # GPU nodes are the last (count - gpu-count) nodes
                "gpu": num >= linux_server_count - linux_gpu_server_count,
                # Bridge nodes are the last (count - bridge-count) nodes
                "bridge": num >= linux_server_count - linux_server_bridge_count,
                "platform": "linux",
                "architecture": (
                    "auto"
                    if num >= linux_server_count - linux_server_bridge_count
                    else linux_server_arch
                ),
                "environment": "any",
            }
        )

    registry_count = 0
    for num in range(registry_client_count):
        registry_count += 1
        node_configs.append(
            {
                "name": f"race-registry-{str(registry_count).zfill(RIB_CONFIG.NODE_ID_WIDTH)}",
                "type": "registry",
                "enclave": "global",
                "nat": False,
                "identities": [],
                # Genesis nodes are the first (count - uninstalled_count) nodes
                "genesis": num
                < registry_client_count - registry_client_uninstalled_count,
                # GPU nodes are the last (count - gpu-count) nodes
                "gpu": num >= registry_client_count - gpu_registry_client_count,
                "bridge": False,  # bridge mode unsupported for registry clients
                "platform": "linux",
                "architecture": (
                    "auto"
                    if num >= linux_client_count - linux_client_bridge_count
                    else registry_client_arch
                ),
                "environment": "any",
            }
        )

    range_config["RACE_nodes"] = node_configs
    range_config["services"] = []

    range_config["enclaves"] = [
        {"name": "global", "ip": "localhost", "port_mapping": {}}
    ]
    range_config["name"] = name

    return {"range": range_config}


def is_ui_enabled(name: str, patterns: Optional[List[str]] = None) -> bool:
    """
    Purpose:
        Determines if the given node should have the user input UI enabled
        by checking if the name matches any of the given name patterns. If
        no patterns were provided, the node will not have the UI enabled
        (and all user inputs will come from the automated responses).
    Args:
        name: Node name
        patterns: Patterns of names for which to enable user input UI
    Returns:
        True if node has user input UI enabled
    """
    if patterns:
        for pattern in patterns:
            if re.search(pattern, name):
                return True
    # Default to false when no patterns provided
    return False

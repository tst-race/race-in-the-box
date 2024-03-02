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
    Files and directories for RiB deployments
"""

# Python Library Imports
from copy import deepcopy
from functools import cached_property
import logging
import os
from typing import Dict, List, Tuple

# Local Python Library Imports


###
# Globals
###

logger = logging.getLogger(__name__)


###
# Types
###


class RibDeploymentPaths:
    """
    Purpose:
        Files and Dir Paths for a deployment
    """

    rib_mode = None

    platforms = ["linux", "android"]
    architectures = ["x86_64", "arm64-v8a"]
    node_types = ["client", "server", "registry"]
    tas = ["network-manager", "comms", "core", "artifact-manager"]

    dirs = {}
    files = {}
    filenames = {
        "config": "deployment_config.json",
        "metadata": "deployment_metadata.json",
        "channel_list": "channel_list.json",
        "race_config": "race-config.json",
    }

    global_config_filenames = [
        "android/race.json",
        "linux/race.json",
    ]

    global_etc_filenames = {
        "testapp_config": "testapp-config.json",
        "jaeger_config": "jaeger-config.json",
        "user_responses": "user-responses.json",
    }

    def __init__(self, name: str) -> None:
        """
        Purpose:
            Initialize the object
        Args:
            name: Deployment name
        Returns:
            N/A
        """

        # Base Dirs/Files/Filenames
        self.dirs = {}
        self.files = {}

        self.make_dirs_dict(name)
        self.make_files_dict()

    @cached_property
    def supported_platform_arch_node_type_combinations(
        self,
    ) -> List[Tuple[str, str, str]]:
        """
        Purpose:
            Get the list of supported machines (platform, architecture, node type)
        Args:
        Returns:
            List of Tuples, each representing a supported configuration of platform, architecture,
            and node type
        """
        supported_combinations = []
        for platform in self.platforms:
            for architecture in self.architectures:
                for node_type in self.node_types:
                    if platform == "android" and node_type == "server":
                        continue
                    supported_combinations.append((platform, architecture, node_type))
        return supported_combinations

    def get_plugin_artifacts_base_dir_key(
        self, platform: str, architecture: str, node_type: str
    ) -> str:
        # registries use the same dirs as clients
        if node_type == "registry":
            node_type = "client"
        return f"plugins_{platform}_{architecture}_{node_type}_dir"

    def get_plugin_artifacts_base_dir_name(
        self, platform: str, architecture: str, node_type: str
    ) -> str:
        # registries use the same dirs as clients
        if node_type == "registry":
            node_type = "client"
        return f"{platform}-{architecture}-{node_type}"

    def get_plugin_artifacts_ta_dir_key(
        self, platform: str, architecture: str, node_type: str, ta: str
    ) -> str:
        # registries use the same dirs as clients
        if node_type == "registry":
            node_type = "client"
        return f"plugins_{platform}_{architecture}_{node_type}_{ta}"

    def make_dirs_dict(
        self, name: str, mode_specific_dirs: Dict[str, str] = {}
    ) -> None:
        """
        Purpose:
            Create the directories dictionary for the specific deployment
        Args:
            name: Deployment name
            mode_specific_dirs: Initial set of dirs
        Returns:
        """
        self.dirs = deepcopy(RibDeploymentPaths.dirs)
        self.dirs.update(deepcopy(mode_specific_dirs))
        base_dir = os.path.join(self.dirs["mode"], name)
        race_configs = os.path.join(base_dir, "configs")
        self.dirs.update(
            {
                "base": base_dir,
                "race_configs": race_configs,
                "global_configs": os.path.join(race_configs, "global"),
                "global_android_configs": os.path.join(
                    race_configs, "global", "android"
                ),
                "global_linux_configs": os.path.join(race_configs, "global", "linux"),
                "network_manager_configs_base": os.path.join(
                    race_configs, "network-manager"
                ),
                "comms_configs_base": os.path.join(race_configs, "comms"),
                "artifact_manager_configs_base": os.path.join(
                    race_configs, "artifact-manager"
                ),
                "data": os.path.join(base_dir, "data"),
                "logs": os.path.join(base_dir, "logs"),
                "previous-runs": os.path.join(base_dir, "previous-run-logs"),
                "runtime-configs": os.path.join(base_dir, "runtime-configs"),
                "etc": os.path.join(base_dir, "etc"),
                "plugins": os.path.join(base_dir, "plugins"),
                "distribution_artifacts": os.path.join(base_dir, "plugins", "dist"),
                "device-prepare-archives": os.path.join(
                    base_dir, "android-device-prepare-archives"
                ),
            }
        )

        # Plugin Base Directories (Platform/Node Type Dirs, distribution artifacts dir, etc.)
        self.dirs.update({"plugins": f"{self.dirs['base']}/plugins"})
        for (
            platform,
            architecture,
            node_type,
        ) in self.supported_platform_arch_node_type_combinations:
            if node_type == "registry":
                continue  # registry nodes use the same plugin artifacts as client nodes
            platform_base_dir = self.get_plugin_artifacts_base_dir_key(
                platform, architecture, node_type
            )
            self.dirs.update(
                {
                    platform_base_dir: f"{self.dirs['plugins']}/{self.get_plugin_artifacts_base_dir_name(platform, architecture, node_type)}"
                }
            )
            for ta in self.tas:
                self.dirs.update(
                    {
                        self.get_plugin_artifacts_ta_dir_key(
                            platform, architecture, node_type, ta
                        ): f"{self.dirs[platform_base_dir]}/{ta}",
                    }
                )

    def make_files_dict(self) -> None:
        """
        Purpose:
            Create the files dictionary for the specific deployment
        Args:
        Returns:
        """
        self.files = deepcopy(RibDeploymentPaths.files)
        self.files.update(
            {
                "config": os.path.join(self.dirs["base"], self.filenames["config"]),
                "metadata": os.path.join(self.dirs["base"], self.filenames["metadata"]),
                "race_config": os.path.join(
                    self.dirs["race_configs"], self.filenames["race_config"]
                ),
                "channel_list": os.path.join(
                    self.dirs["race_configs"], self.filenames["channel_list"]
                ),
            }
        )

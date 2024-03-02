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
    Files and directories for RiB AWS deployments
"""

# Python Library Imports
import os

# Local Python Library Imports
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.paths.rib_deployment_paths import RibDeploymentPaths

###
# Globals
###


###
# Types
###


class RibAwsDeploymentPaths(RibDeploymentPaths):
    """
    Purpose:
        Files and Dir Paths for a deployment
    """

    ###
    # Class Attributes
    ###
    rib_mode = "aws"

    # Base Dirs/Files/Filenames
    dirs = {
        "mode": RibDeployment.rib_config.RIB_PATHS["docker"]["deployments"][rib_mode],
        "templates": (
            f"{RibDeployment.rib_config.RIB_PATHS['docker']['artifacts']}"
            f"/deployments/{rib_mode}/templates"
        ),
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
        super().__init__(name)

    def make_dirs_dict(self, name: str) -> None:
        """
        Purpose:
            Create the directories dictionary for the specific deployment
        Args:
            name: Deployment name
        Returns:
        """

        super().make_dirs_dict(name, RibAwsDeploymentPaths.dirs)

        self.dirs.update(
            {
                "docker_compose": os.path.join(self.dirs["base"], "docker-compose"),
                "mounted_artifacts": os.path.join(
                    self.dirs["base"], "mounted-artifacts"
                ),
            }
        )

    def make_files_dict(self) -> None:
        """
        Purpose:
            Create the files dictionary for the specific deployment
        Args:
        Returns:
        """

        super().make_files_dict()
        self.files.update(
            {
                "ansible_stand_up_playbook": os.path.join(
                    self.dirs["base"], "ansible/stand-up.yml"
                ),
                "ansible_tear_down_playbook": os.path.join(
                    self.dirs["base"], "ansible/tear-down.yml"
                ),
                "node_distribution": os.path.join(
                    self.dirs["base"], "node_distribution.json"
                ),
                "node_topology": os.path.join(self.dirs["base"], "node_topology.json"),
            }
        )

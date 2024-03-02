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
    Files and directories for RiB Local deployments
"""

# Python Library Imports

# Local Python Library Imports
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.paths.rib_deployment_paths import RibDeploymentPaths

###
# Globals
###


###
# Types
###


class RibLocalDeploymentPaths(RibDeploymentPaths):
    """
    Purpose:
        Files and Dir Paths for a deployment
    """

    ###
    # Class Attributes
    ###
    rib_mode = "local"

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

        super().make_dirs_dict(name, RibLocalDeploymentPaths.dirs)

        self.dirs.update(
            {  # Base Dirs (For Mounting in Nodes)
                "dnsproxy": f"{self.dirs['base']}/dnsproxy",
                "vpn": f"{self.dirs['base']}/vpn",
                # Config/Data Subdirs, For Sub Configs/Data/Opentracing
                "keys": f"{self.dirs['data']}/keys",
                "opentracing": f"{self.dirs['logs']}/opentracing",
                "elasticsearch": f"{self.dirs['logs']}/opentracing/elasticsearch",
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
            {  # Important Files for the Deployment
                "docker_compose": f"{self.dirs['base']}/docker-compose.yml",
            }
        )

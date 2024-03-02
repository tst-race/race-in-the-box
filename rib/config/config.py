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
        Config Class for RACE. Will hold constants and config values that are
        critical for the RACE, but are not configured by the user of the tool. Allows
        for production, qa, and dev environments.
"""

# Python Library Imports
import logging
import os
from typing import Any, Dict, List


###
# RACE Config Class
###


class Config:
    """
    Base Config Class for RACE. Will hold constants and config values that are
    critical for the RACE, but are not configured by the user of the tool. Allows
    for production, qa, and dev environments.
    """

    @classmethod
    def get(cls, environment=None) -> object:
        """
        Purpose:
            Get specific Config instance (prod, qa, dev)

            This method will use the value of the environment argument (if provided)
            to determine which configuration tier to use.  If not supplied,
            the method will default to the tier that can be determined from
            the hostname command.
        Args:
            environment: pointer to which environment to load configs for
        Returns:
            CONFIGS (Config Obj): Object of the config class specfied from the
                environmental variable or the  argument. Defaults to development
                if nothing is set
        """

        # If environment is not passed in get it from environmental variables
        if not environment:
            environment = os.getenv("ENVIRONMENT", "development")

        # Get subclass depending on envrionment, default to development in all edge
        # cases
        if environment in ("prod", "production"):
            configs = cls.Production()
        elif environment in ("test", "testing", "qa"):
            configs = cls.Qa()
        elif environment in ("dev", "development"):
            configs = cls.Development()
        else:
            print(f"{environment} is not a vaild tier, defaulting to development")
            configs = cls.Development()

        return configs

    class Production:
        """
        Production insance of base class
        """

        ENVIRONMENT = "production"

        ###
        # Get Environmental Variables
        ###

        RIB_VERSION = os.getenv("RIB_VERSION")
        if not RIB_VERSION:
            RIB_VERSION = "production"
        RACE_VERSIONS = [
            "2.4.0",
            "2.4.1",
            "2.4.2",
        ]

        ###
        # RACE Node Config
        ###

        NODE_ID_WIDTH = 5

        ###
        # RiB Path
        ###

        # TODO: should we raise an exception if this variable is not set? Would've saved
        # me an hour of debugging if we had. Let's do that at some point, but doing it
        # now causes 44 unit test failues. Would prefer setting this via a config file
        # instead of an env var. -GP
        HOST_RIB_STATE_PATH = os.getenv("HOST_RIB_STATE_PATH")
        # if HOST_RIB_STATE_PATH is None:
        #     raise Exception("environment variable HOST_RIB_STATE_PATH is not set")
        DOCKER_RIB_STATE_PATH = f"{os.getenv('HOME')}/.race/rib"
        RIB_PATHS: Dict[str, Dict[str, Any]] = {
            "host": {
                "artifacts": None,
                "aws_envs": {"root": f"{HOST_RIB_STATE_PATH}/aws-envs"},
                "aws_state": f"{HOST_RIB_STATE_PATH}/aws",
                "build_outputs": f"{HOST_RIB_STATE_PATH}/build-outputs",
                "code": os.getenv("HOST_CODE_PATH"),
                "deployments": {
                    "aws": f"{HOST_RIB_STATE_PATH}/deployments/aws",
                    "local": f"{HOST_RIB_STATE_PATH}/deployments/local",
                    "root": f"{HOST_RIB_STATE_PATH}/deployments",
                },
                "te_active_deployment_configs": f"{HOST_RIB_STATE_PATH}/te_active_deployment_configs",
                "plugins-cache": f"{HOST_RIB_STATE_PATH}/plugins-cache",
                "range_configs": f"{HOST_RIB_STATE_PATH}/range-configs",
                "rib_logs": f"{HOST_RIB_STATE_PATH}/logs",
                "rib_path": None,
                "rib_state": HOST_RIB_STATE_PATH,
                "ssh": None,
                "user_state": f"{HOST_RIB_STATE_PATH}/user-state",
            },
            "docker": {
                "artifacts": "/race_in_the_box/rib/artifacts",
                "aws_envs": {"root": f"{DOCKER_RIB_STATE_PATH}/aws-envs"},
                "aws_state": f"{DOCKER_RIB_STATE_PATH}/aws",
                "build_outputs": f"{DOCKER_RIB_STATE_PATH}/build-outputs",
                "cache": f"{DOCKER_RIB_STATE_PATH}/cache",
                "code": "/code/",
                "deployments": {
                    "aws": f"{DOCKER_RIB_STATE_PATH}/deployments/aws",
                    "local": f"{DOCKER_RIB_STATE_PATH}/deployments/local",
                    "root": f"{DOCKER_RIB_STATE_PATH}/deployments",
                },
                "github": f"{DOCKER_RIB_STATE_PATH}/github",
                "te_active_deployment_configs": "/te_active_deployment_configs",
                "plugins-cache": f"{DOCKER_RIB_STATE_PATH}/plugins-cache",
                "rib_logs": f"{DOCKER_RIB_STATE_PATH}/logs",
                "rib_path": "/race_in_the_box",
                "rib_state": DOCKER_RIB_STATE_PATH,
                "range_configs": f"{DOCKER_RIB_STATE_PATH}/range-configs",
                "ssh": f"{os.getenv('HOME')}/.ssh",
                "user_state": f"{DOCKER_RIB_STATE_PATH}/user-state",
            },
            "portable": {},  # HOST_RIB_STATE_PATH must be set as an environment variable when calling operations on host
        }
        RIB_USER_STATE_FILENAME = "rib.json"
        RIB_SSH_KEY_FILENAME = "rib_private_key"
        RIB_SSH_KEY_FILE = f"{RIB_PATHS['docker']['ssh']}/{RIB_SSH_KEY_FILENAME}"

        ###
        # Git Globals
        ###

        RACE_REPOSITORIES = [
            "plugin-network-manager-twosix-cpp",
            "plugin-network-manager-twosix-python",
            "plugin-network-manager-twosix-java",
            "plugin-network-manager-twosix-test-harness",
            "plugin-comms-twosix-cpp",
            "plugin-comms-twosix-golang",
            "plugin-comms-twosix-python",
            "plugin-comms-twosix-rust",
            "plugin-comms-twosix-java",
            "race-images",
            "raceclient-linux",
            "raceclient-android",
            "racesdk-common",
            "racesdk-core",
            "racesdk-language-shims",
            "racesdk-java-shims",
            "raceserver-linux",
            "racetestapp-linux",
            "twosix-whiteboard",
        ]

        ###
        # Container Registry Config
        ###

        CONTAINER_REGISTRY_HOST = "ghcr.io"
        CONTAINER_REGISTRY_URL = CONTAINER_REGISTRY_HOST
        CONTAINER_REGISTRY_REPOS = {
            "race-in-the-box": "race-in-the-box",
            "race-base": "race-images-base",
            "race-compile": "race-images-base",
            "race-runtime": "race-images-base",
            "race-ndk": "race-images-base",
            "race-sdk": "racesdk",
            "race-android-x86_64-client": "race-images-base",
            "race-android-x86_64-client-exemplar": "race-images-exemplar",
            "race-android-x86_64-client-complete": "race-images-complete",
            "race-android-arm64-v8a-client": "race-images-base",
            "race-android-arm64-v8a-client-exemplar": "race-images-exemplar",
            "race-android-arm64-v8a-client-complete": "race-images-complete",
            "race-linux-client": "race-images-base",
            "race-linux-client-exemplar": "race-images-exemplar",
            "race-linux-client-complete": "race-images-complete",
            "race-linux-server": "race-images-base",
            "race-linux-server-exemplar": "race-images-exemplar",
            "race-linux-server-complete": "race-images-complete",
        }

        ###
        # Deployment Configs
        ###

        DEPLOYMENT_MODES = [
            "local",  # Docker compose on local machine
            "aws",  # Deploy nodes to AWS
        ]
        SERVER_PORT_START = 47000
        CLIENT_PORT_START = 45000
        LOCAL_BASTION_IP = "172.25.1.254"

        ###
        # System Configs
        ###

        SYSTEM_REQUIREMENTS = {
            "local": {
                "supported_systems": {
                    "Darwin": "mac",
                    "Linux": "linux",
                    "Windows": "windows",
                },
                "min_docker_cpu": 4.0,
                "min_docker_memory_gig": 4.0,
            },
            "aws": {
                "supported_systems": {
                    "Darwin": "mac",
                    "Linux": "linux",
                    "Windows": "windows",
                },
                "min_docker_cpu": 1.0,
                "min_docker_memory_gig": 1.0,
            },
        }

        ###
        # AWS Configs
        ###

        # These are the public AMIs available to all AWS users, so there should be
        # no need to share an AMI

        # Amazon Linux 2 Kernel 5.10 AMI 2.0.20221004.0 x86_64 HVM gp2
        LINUX_x86_64_AMI = "ami-09d3b3274b6c5d4aa"
        # Amazon Linux 2 LTS Arm64 Kernel 5.10 AMI 2.0.20221004.0 arm64 HVM gp2
        LINUX_ARM64_AMI = "ami-081dc0707789c2daf"
        # Deep Learning Base AMI (Amazon Linux 2) Version 53.0
        LINUX_GPU_x86_64_AMI = "ami-00f6c6c9a6475dfeb"
        # NVIDIA GPU-Optimized ARM64 22.06.0-8c85b20b-d7b9-4aa6-8d9c-584018f77e4e
        LINUX_GPU_ARM64_AMI = "ami-0126d561b2bb55618"

        # Setting the default SSH port to the EC2 instance to non-default 22 so that
        # 22 can be used to SSH to bastion
        RACE_AWS_MANAGE_SSH_PORT = 2222

        ###
        # Logging
        ###

        LOG_LEVEL = logging.INFO

        ###
        # OpenVPN Configs
        ###

        OPENVPN_FOR_ANDROID_VERSION = "0-7-33"

    class Qa(Production):
        """
        Purpose:
            Qa instance of base class. Used for QA of the code (developer testing) and
            release candidate testing. Non-customer facing.
        """

        ENVIRONMENT = "qa"

    class Development(Qa):
        """
        Purpose:
            Development instance of base class. Used as the sandbox of the project, for
            local testing, or proof of concepts.
        """

        ENVIRONMENT = "development"
        RIB_VERSION = "development"

        ###
        # Logging
        ###

        LOG_LEVEL = logging.DEBUG

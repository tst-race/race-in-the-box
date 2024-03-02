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
    Files and directories for AWS environments
"""

# Python Library Imports
import logging
import os
import shutil
from pydantic import ValidationError
from typing import Any, Mapping, Optional, cast

# Local Python Library Imports
from .rib_aws_env_config import (
    AwsEnvCache,
    AwsEnvConfig,
    AwsEnvMetadata,
)
from rib.utils import general_utils, rib_utils


###
# Globals
###

logger = logging.getLogger(__name__)
rib_config = rib_utils.load_race_global_configs()
root_dir: str = rib_config.RIB_PATHS["docker"]["aws_envs"]["root"]
templates_dir = os.path.join(
    rib_config.RIB_PATHS["docker"]["artifacts"], "envs", "aws", "templates"
)
template_ansible_inventory_file = os.path.join(
    templates_dir, "ansible", "inventory.aws_ec2.yml"
)


###
# Types
###


class AwsEnvFileException(Exception):
    """Error reading or parsing an AWS environment file"""


class AwsEnvFiles:
    """Files and directories for a specific AWS environment"""

    def __init__(self, name: str) -> None:
        """
        Purpose:
            Initializes the files for a given AWS environment
        Args:
            name: AWS environment name
        Return:
            N/A
        """

        self.root_dir = root_dir
        self.base_dir = os.path.join(self.root_dir, name)
        self.ansible_dir = os.path.join(self.base_dir, "ansible")

        self.config_file = os.path.join(self.base_dir, "aws_env_config.json")
        self.metadata_file = os.path.join(self.base_dir, "aws_env_metadata.json")
        self.cache_file = os.path.join(self.base_dir, "aws_env_cache.json")

        self.ssh_key_file = rib_config.RIB_SSH_KEY_FILE

        self.ansible_inventory_file = os.path.join(
            self.ansible_dir, "inventory.aws_ec2.yml"
        )
        self.ansible_provision_playbook_file = os.path.join(
            self.ansible_dir, "provision.yml"
        )
        self.ansible_unprovision_playbook_file = os.path.join(
            self.ansible_dir, "unprovision.yml"
        )

    def create_directories(self) -> None:
        """
        Purpose:
            Creates all directories for an AWS environment
        Args:
            N/A
        Return:
            N/A
        """

        os.makedirs(self.base_dir, exist_ok=True)

    def copy_templates(self) -> None:
        """
        Purpose:
            Copies all template files into the AWS environment
        """

        shutil.copytree(templates_dir, self.base_dir, dirs_exist_ok=True)

    def read_config(self) -> AwsEnvConfig:
        """
        Purpose:
            Reads the config file for the AWS environment
        Args:
            N/A
        Return:
            AWS environment configuration
        Raises:
            AwsEnvFileException if unable to read, parse, or validate
        """

        try:
            if os.path.exists(self.config_file):
                return AwsEnvConfig.parse_file(self.config_file)
        except ValidationError as err:
            raise AwsEnvFileException(f"Invalid AWS env config: {str(err)}") from None
        except Exception as err:
            raise AwsEnvFileException(
                f"Unable to read AWS env config file: {repr(err)}"
            ) from err

        raise AwsEnvFileException("AWS env config file does not exist")

    def read_config_dict(self) -> Mapping[str, Any]:
        """
        Purpose:
            Reads the config file for the AWS environment as an unvalidated dictionary
        Args:
            N/A
        Return:
            Unvalidated AWS environment configuration dictionary
        Raises:
            AwsEnvFileException if unable to read or parse
        """

        try:
            if os.path.exists(self.config_file):
                return general_utils.load_file_into_memory(
                    self.config_file, data_format="json"
                )
        except Exception as err:
            raise AwsEnvFileException(
                f"Unable to read AWS env config: {repr(err)}"
            ) from err

        raise AwsEnvFileException("AWS env config file does not exist")

    def write_config(self, config: AwsEnvConfig) -> None:
        """
        Purpose:
            Writes the AWS environment configuration to the config file
        Args:
            config: AWS environment configuration
        Return:
            N/A
        """

        general_utils.write_data_to_file(
            filename=self.config_file,
            data=config.dict(),
            data_format="json",
            overwrite=True,
        )

    def read_metadata(self) -> AwsEnvMetadata:
        """
        Purpose:
            Reads the metadata file for the AWS environment
        Args:
            N/A
        Return:
            AWS environment metadata
        Raises:
            AwsEnvFileException if unable to read, parse, or validate
        """

        try:
            if os.path.exists(self.metadata_file):
                metadata = general_utils.load_file_into_memory(
                    self.metadata_file, data_format="json"
                )
                return cast(AwsEnvMetadata, metadata)
        except Exception as err:
            raise AwsEnvFileException(
                f"Unable to read AWS env metadata: {repr(err)}"
            ) from err

        raise AwsEnvFileException("AWS env metadata file does not exist")

    def write_metadata(self, metadata: AwsEnvMetadata) -> None:
        """
        Purpose:
            Writes the AWS environment metadata to the metadata file
        Args:
            metadata: AWS environment metadata
        Return:
            N/A
        """

        general_utils.write_data_to_file(
            filename=self.metadata_file,
            data=metadata,
            data_format="json",
            overwrite=True,
        )

    def read_cache(self) -> AwsEnvCache:
        """
        Purpose:
            Reads the cache file for the AWS environment
        Args:
            N/A
        Return:
            AWS environment info cache
        """

        try:
            if os.path.exists(self.cache_file):
                cache = general_utils.load_file_into_memory(
                    self.cache_file, data_format="json"
                )
                return cast(AwsEnvCache, cache)
        except Exception as err:
            logger.warning(f"Unable to read AWS environment cache: {err}")
        return AwsEnvCache(instances={})

    def write_cache(self, cache: AwsEnvCache) -> None:
        """
        Purpose:
            Writes the AWS environment cache to the cache file
        Args:
            cache: AWS environment cache
        Return:
            N/A
        """

        general_utils.write_data_to_file(
            filename=self.cache_file,
            data=cache,
            data_format="json",
            overwrite=True,
        )

    @staticmethod
    def actuate_yaml_template(
        file_path: str,
        template_vars: Mapping[str, Any],
        template_file_path: Optional[str] = None,
    ) -> None:
        """
        Purpose:
            Replace all template values in the specified file using values from the
            given vars dictionary
        Args:
            file_path: Path to file to be actuated
            template_vars: Template variables dictionary
            template_file_path: Optional, source template file to be actuated if not doing an
                in-place actuation
        Return:
            N/A
        """
        if not template_file_path:
            template_file_path = file_path
        actuated = general_utils.format_yaml_template(template_file_path, template_vars)
        general_utils.write_data_to_file(
            file_path, actuated, data_format="yaml", overwrite=True
        )

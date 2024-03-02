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
    Test file for rib_aws_env_files.py
"""

# Python Library Imports
import pytest
from unittest.mock import MagicMock, patch
from typing import Any

# Local Python Library Imports
from rib.aws_env.rib_aws_env_files import AwsEnvFiles, AwsEnvFileException


###
# Fixtures
###


@pytest.fixture
def files() -> AwsEnvFiles:
    return AwsEnvFiles("test-env-name")


@pytest.fixture
def json_content() -> Any:
    return {"name": "test-env-name"}


@pytest.fixture
def config_json_content() -> Any:
    instance_config = {
        "instance_type": "test-instance-type",
        "instance_ami": "test-instance-ami",
        "ebs_size": 42,
    }
    instance_group_config = {**instance_config, "instance_count": 1}
    return {
        "name": "test-env-name",
        "rib_version": "test-rib-version",
        "ssh_key_name": "test-ssh-key-name",
        "remote_username": "test-remote-username",
        "region": "test-region",
        "cluster_manager": instance_config,
        "service_host": instance_config,
        "linux_arm64_hosts": instance_group_config,
        "linux_x86_64_hosts": instance_group_config,
        "linux_gpu_arm64_hosts": instance_group_config,
        "linux_gpu_x86_64_hosts": instance_group_config,
        "android_arm64_hosts": instance_group_config,
        "android_x86_64_hosts": instance_group_config,
    }


@pytest.fixture
def yaml_content() -> Any:
    return {"key": "value"}


###
# read_config
###


@patch("os.path.exists", MagicMock(return_value=False))
def test_read_config_raises_when_file_does_not_exist(files):
    with pytest.raises(AwsEnvFileException):
        files.read_config()


@patch("os.path.exists", MagicMock(return_value=True))
def test_read_config_raises_when_read_fails(files):
    with pytest.raises(AwsEnvFileException):
        files.read_config()


@patch("os.path.exists", MagicMock(return_value=True))
@patch("pydantic.main.load_file")
def test_read_config_raises_when_validation_fails(load_file, files, json_content):
    load_file.return_value = json_content
    with pytest.raises(AwsEnvFileException):
        files.read_config()


@patch("os.path.exists", MagicMock(return_value=True))
@patch("pydantic.main.load_file")
def test_read_config_return_obj_when_validation_passed(
    load_file, files, config_json_content
):
    load_file.return_value = config_json_content
    assert config_json_content == files.read_config()


###
# read_config_dict
###


@patch("os.path.exists", MagicMock(return_value=False))
def test_read_config_dict_raises_when_file_does_not_exist(files):
    with pytest.raises(AwsEnvFileException):
        files.read_config_dict()


@patch("os.path.exists", MagicMock(return_value=True))
@patch(
    "rib.utils.general_utils.load_file_into_memory", MagicMock(side_effect=Exception)
)
def test_read_config_dict_raises_when_read_fails(files):
    with pytest.raises(AwsEnvFileException):
        files.read_config_dict()


@patch("os.path.exists", MagicMock(return_value=True))
@patch("rib.utils.general_utils.load_file_into_memory")
def test_read_config_dict_returns_file_contents(
    mock_load_file_into_memory, files, json_content
):
    mock_load_file_into_memory.return_value = json_content
    assert json_content == files.read_config_dict()


###
# read_metadata
###


@patch("os.path.exists", MagicMock(return_value=False))
def test_read_metadata_raises_when_file_does_not_exist(files):
    with pytest.raises(AwsEnvFileException):
        files.read_metadata()


@patch("os.path.exists", MagicMock(return_value=True))
@patch(
    "rib.utils.general_utils.load_file_into_memory", MagicMock(side_effect=Exception)
)
def test_read_metadata_raises_when_read_fails(files):
    with pytest.raises(AwsEnvFileException):
        files.read_metadata()


@patch("os.path.exists", MagicMock(return_value=True))
@patch("rib.utils.general_utils.load_file_into_memory")
def test_read_metadata_return_obj_read_success(
    mock_load_file_into_memory, files, json_content
):
    mock_load_file_into_memory.return_value = json_content
    assert json_content == files.read_metadata()


###
# read_cache
###


@patch("os.path.exists", MagicMock(return_value=False))
def test_read_cache_returns_empty_cache_when_file_does_not_exist(files):
    assert {"instances": {}} == files.read_cache()


@patch("os.path.exists", MagicMock(return_value=True))
@patch(
    "rib.utils.general_utils.load_file_into_memory", MagicMock(side_effect=Exception)
)
def test_read_cache_returns_empty_cache_when_read_fails(files):
    assert {"instances": {}} == files.read_cache()


@patch("os.path.exists", MagicMock(return_value=True))
@patch("rib.utils.general_utils.load_file_into_memory")
def test_read_cache_return_obj_read_success(
    mock_load_file_into_memory, files, json_content
):
    mock_load_file_into_memory.return_value = json_content
    assert json_content == files.read_cache()


###
# actuate_yaml_template
###


@patch("rib.utils.general_utils.format_yaml_template")
@patch("rib.utils.general_utils.write_data_to_file")
def test_actuate_yaml_template_updates_file_in_place(
    mock_write_data_to_file,
    mock_format_yaml_template,
    files,
    json_content,
    yaml_content,
):
    mock_format_yaml_template.return_value = yaml_content
    files.actuate_yaml_template("test-file.yml", json_content)

    mock_format_yaml_template.assert_called_with("test-file.yml", json_content)
    mock_write_data_to_file.assert_called_with(
        "test-file.yml", yaml_content, data_format="yaml", overwrite=True
    )


@patch("rib.utils.general_utils.format_yaml_template")
@patch("rib.utils.general_utils.write_data_to_file")
def test_actuate_yaml_template_updates_file_from_template(
    mock_write_data_to_file,
    mock_format_yaml_template,
    files,
    json_content,
    yaml_content,
):
    mock_format_yaml_template.return_value = yaml_content
    files.actuate_yaml_template("test-file.yml", json_content, "template-file.yml")

    mock_format_yaml_template.assert_called_with("template-file.yml", json_content)
    mock_write_data_to_file.assert_called_with(
        "test-file.yml", yaml_content, data_format="yaml", overwrite=True
    )

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
    Test file for rib_aws_env.py
"""

# Python Library Imports
import os
import paramiko
import pytest
import shutil
import socket
import tempfile
from datetime import datetime
from requests import Response
from unittest.mock import MagicMock, patch

# Local Library Imports
from rib.aws_env import rib_aws_env_files
from rib.aws_env.rib_aws_env import AwsEnvFiles, RibAwsEnv
from rib.aws_env.rib_aws_env_config import (
    AwsEnvConfig,
    AwsEnvMetadata,
    Ec2InstanceConfig,
    Ec2InstanceGroupConfig,
)
from rib.aws_env.rib_aws_env_status import (
    ActiveAwsEnvs,
    AwsComponentStatus,
    AwsEnvStatus,
    IncompatibleAwsEnv,
    StatusReport,
)
from rib.utils import error_utils, rib_utils
from rib.utils.aws_topology_utils import (
    InstanceCounts,
    InstanceEbsSizes,
    InstanceTypeNames,
)


###
# Fixtures
###


@pytest.fixture(autouse=True)
def get_current_time() -> None:
    """Mock out the general_utils.get_current_time function to return a fixed time"""
    with patch(
        "rib.utils.general_utils.get_current_time",
        MagicMock(return_value=datetime(2022, 1, 3, 11, 22, 33).isoformat()),
    ):
        yield


@pytest.fixture
def rib_state_path() -> str:
    """Copies test RiB state path contents to a temporary location"""
    # Copy the test files
    src = os.path.join(os.path.dirname(os.path.realpath(__file__)), "rib_state_path")
    dest = os.path.join(tempfile.gettempdir(), "rib-unit-test-state-path")
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest)
    # Redirect AWS env files to the test files
    orig_root_dir = rib_aws_env_files.root_dir
    orig_templates_dir = rib_aws_env_files.templates_dir
    orig_template_ansible_inventory_file = (
        rib_aws_env_files.template_ansible_inventory_file
    )
    rib_aws_env_files.root_dir = rib_aws_env_files.root_dir.replace(
        os.getenv("HOME"), dest
    )
    # Go up 2 directories to get to the source templates dir
    rib_aws_env_files.templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "artifacts",
        "envs",
        "aws",
        "templates",
    )
    rib_aws_env_files.template_ansible_inventory_file = os.path.join(
        rib_aws_env_files.templates_dir, "ansible", "inventory.aws_ec2.yml"
    )
    # Execute test
    yield dest
    # Reset
    shutil.rmtree(dest, ignore_errors=True)
    rib_aws_env_files.root_dir = orig_root_dir
    rib_aws_env_files.templates_dir = orig_templates_dir
    rib_aws_env_files.template_ansible_inventory_file = (
        orig_template_ansible_inventory_file
    )


@pytest.fixture
def rib_config() -> rib_utils.Config:
    """Set up a mock RiB config to be returned by load_race_global_configs"""
    config = rib_utils.load_race_global_configs()
    with patch(
        "rib.utils.rib_utils.load_race_global_configs", MagicMock(return_value=config)
    ):
        yield config


@pytest.fixture(autouse=True)
def connect_aws_session() -> None:
    with patch("rib.utils.aws_utils.connect_aws_session_with_profile", MagicMock()):
        yield


@pytest.fixture(autouse=True)
def rib_ssh_key() -> None:
    with patch("rib.utils.ssh_utils.get_rib_ssh_key", MagicMock()):
        yield


@pytest.fixture
def aws_env_config() -> AwsEnvConfig:
    """AWS environment configuration for an env with some of each type of host instance"""
    return AwsEnvConfig(
        name="test-aws-env",
        rib_version="test-rib-version",
        ssh_key_name="test-ssh-key-pair",
        remote_username="test-user",
        region="test-region",
        cluster_manager=Ec2InstanceConfig(
            instance_type="test-cluster-manager-instance-type",
            instance_ami="test-linux-x86-ami",
            ebs_size=64,
        ),
        service_host=Ec2InstanceConfig(
            instance_type="test-service-instance-type",
            instance_ami="test-linux-x86-ami",
            ebs_size=64,
        ),
        linux_arm64_hosts=Ec2InstanceGroupConfig(
            instance_count=2,
            instance_type="test-linux-arm64-instance-type",
            instance_ami="test-linux-arm-ami",
            ebs_size=64,
        ),
        linux_x86_64_hosts=Ec2InstanceGroupConfig(
            instance_count=3,
            instance_type="test-linux-x86_64-instance-type",
            instance_ami="test-linux-x86-ami",
            ebs_size=64,
        ),
        linux_gpu_arm64_hosts=Ec2InstanceGroupConfig(
            instance_count=3,
            instance_type="test-gpu-arm64-instance-type",
            instance_ami="test-linux-gpu-arm-ami",
            ebs_size=128,
        ),
        linux_gpu_x86_64_hosts=Ec2InstanceGroupConfig(
            instance_count=2,
            instance_type="test-gpu-x86_64-instance-type",
            instance_ami="test-linux-gpu-x86-ami",
            ebs_size=128,
        ),
        android_arm64_hosts=Ec2InstanceGroupConfig(
            instance_count=2,
            instance_type="test-android-arm64-instance-type",
            instance_ami="test-linux-arm-ami",
            ebs_size=128,
        ),
        android_x86_64_hosts=Ec2InstanceGroupConfig(
            instance_count=1,
            instance_type="test-android-x86_64-instance-type",
            instance_ami="test-linux-x86-ami",
            ebs_size=128,
        ),
    )


@pytest.fixture
def aws_env_metadata() -> AwsEnvMetadata:
    """AWS environment metadata"""
    return AwsEnvMetadata(
        rib_image={
            "digest": "rib-image-digest",
            "created": "rib-image-created",
        },
        create_command="test-create-command",
        create_date="2022-01-03T11:22:33",
        last_provision_command=None,
        last_provision_time=None,
        last_unprovision_command=None,
        last_unprovision_time=None,
    )


@pytest.fixture
def aws_env_files(aws_env_config, aws_env_metadata) -> AwsEnvFiles:
    """Mocked AWS environment files instance"""
    # We want to allow all the original attributes, but mock out all the functions
    files = AwsEnvFiles("test-aws-env")
    files.create_directories = MagicMock()
    files.copy_templates = MagicMock()
    files.read_config = MagicMock(return_value=aws_env_config)
    files.write_config = MagicMock()
    files.read_metadata = MagicMock(return_value=aws_env_metadata)
    files.write_metadata = MagicMock()
    files.read_cache = MagicMock(return_value={"instances": {}})
    files.write_cache = MagicMock()
    files.actuate_yaml_template = MagicMock()
    return files


@pytest.fixture
def aws_env(aws_env_config, aws_env_files, aws_env_metadata) -> RibAwsEnv:
    """AWS environment configured with one of each type of host instance"""
    env = RibAwsEnv(
        config=aws_env_config,
        files=aws_env_files,
        metadata=aws_env_metadata,
    )
    return env


###
# aws_env_exists
###


@pytest.mark.usefixtures("rib_state_path")
def test_aws_env_exists():
    assert RibAwsEnv.aws_env_exists("does-not-exist") == False
    assert RibAwsEnv.aws_env_exists("compatible-env") == True
    assert RibAwsEnv.aws_env_exists("incompatible-env") == True


###
# load_aws_env
###


@pytest.mark.usefixtures("rib_state_path")
def test_load_aws_env_non_existent_env():
    assert RibAwsEnv.load_aws_env("does-not-exist") == None


@pytest.mark.usefixtures("rib_state_path")
def test_load_aws_env_bad_config_file():
    assert RibAwsEnv.load_aws_env("bad-config-file") == None


@pytest.mark.usefixtures("rib_state_path")
def test_load_aws_env_bad_metadata_file():
    assert RibAwsEnv.load_aws_env("bad-metadata-file") == None


@pytest.mark.usefixtures("rib_state_path")
def test_load_aws_env_incompatible_env():
    assert RibAwsEnv.load_aws_env("incompatible-env") == None


@pytest.mark.usefixtures("rib_state_path")
def test_load_aws_env_compatible_env():
    assert isinstance(RibAwsEnv.load_aws_env("compatible-env"), RibAwsEnv)


###
# get_aws_env_or_fail
###


@pytest.mark.usefixtures("rib_state_path")
def test_get_aws_env_or_fail_raises_with_alternatives():
    with pytest.raises(error_utils.RIB709):
        RibAwsEnv.get_aws_env_or_fail("incompatible-env")


@pytest.mark.usefixtures("rib_state_path")
def test_get_aws_env_or_fail_raises_with_no_alternatives():
    shutil.rmtree(os.path.join(rib_aws_env_files.root_dir, "compatible-env"))
    with pytest.raises(error_utils.RIB708):
        RibAwsEnv.get_aws_env_or_fail("incompatible-env")


@pytest.mark.usefixtures("rib_state_path")
def test_get_aws_env_or_fail_compatible_env():
    assert isinstance(RibAwsEnv.get_aws_env_or_fail("compatible-env"), RibAwsEnv)


###
# get_local_aws_envs
###


@pytest.mark.usefixtures("rib_state_path")
def test_get_local_aws_envs():
    envs = RibAwsEnv.get_local_aws_envs()
    assert envs.compatible == {"compatible-env"}
    assert envs.incompatible == {
        IncompatibleAwsEnv(name="bad-config-file", rib_version="unknown"),
        IncompatibleAwsEnv(name="bad-metadata-file", rib_version="test-rib-version"),
        IncompatibleAwsEnv(name="incompatible-env", rib_version="dev"),
        IncompatibleAwsEnv(name="not-a-valid-env", rib_version="unknown"),
    }


###
# get_active_aws_envs
###


@pytest.mark.usefixtures("rib_state_path")
@patch("rib.utils.aws_utils.get_cf_stacks", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_cf_stacks_by_tags_and_state",
    MagicMock(
        return_value={
            "race-unowned-env": {"tags": {"AwsEnvName": "unowned-env"}},
            "race-incompatible": {"tags": {"AwsEnvName": "incompatible-env"}},
            "race-compatible": {"tags": {"AwsEnvName": "compatible-env"}},
        }
    ),
)
def test_get_active_aws_envs():
    envs = RibAwsEnv.get_active_aws_envs()
    assert envs.owned == {"compatible-env", "incompatible-env"}
    assert envs.unowned == {"unowned-env"}


###
# remove_legacy_aws_env
###


@pytest.mark.usefixtures("rib_state_path")
def test_remove_legacy_aws_env():
    # shouldn't do anything
    RibAwsEnv.remove_legacy_aws_env("does-not-exist")

    env_dir = os.path.join(rib_aws_env_files.root_dir, "incompatible-env")
    assert os.path.isdir(env_dir)
    RibAwsEnv.remove_legacy_aws_env("incompatible-env")
    assert not os.path.isdir(env_dir)


###
# create
###


@pytest.mark.usefixtures("rib_state_path")
@patch(
    "rib.utils.docker_utils.get_container_info",
    MagicMock(
        return_value={
            "image": {
                "digest": "rib-image-digest",
                "created": "rib-image-created",
            }
        }
    ),
)
@patch("rib.utils.aws_topology_utils.get_instance_type_details", MagicMock())
@patch(
    "rib.utils.aws_utils.get_rib_aws_preferences",
    MagicMock(
        return_value={
            "linux_x86_64_ami": "test-linux-x86-ami",
            "linux_arm64_ami": "test-linux-arm-ami",
            "linux_gpu_x86_64_ami": "test-linux-gpu-x86-ami",
            "linux_gpu_arm64_ami": "test-linux-gpu-arm-ami",
        }
    ),
)
def test_create(aws_env_config, aws_env_metadata, rib_config):
    rib_config.RIB_VERSION = "test-rib-version"
    RibAwsEnv.create(
        aws_env_name="test-aws-env",
        create_command="test-create-command",
        instance_counts=InstanceCounts(
            android_arm64_instances=2,
            android_x86_64_instances=1,
            linux_gpu_arm64_instances=3,
            linux_gpu_x86_64_instances=2,
            linux_arm64_instances=2,
            linux_x86_64_instances=3,
        ),
        instance_ebs_sizes=InstanceEbsSizes(
            android_instance_ebs_size_gb=128,
            linux_gpu_instance_ebs_size_gb=128,
            linux_instance_ebs_size_gb=64,
            cluster_manager_instance_ebs_size_gb=64,
            service_host_instance_ebs_size_gb=64,
        ),
        instance_type_names=InstanceTypeNames(
            android_arm64_instance_type_name="test-android-arm64-instance-type",
            android_x86_64_instance_type_name="test-android-x86_64-instance-type",
            linux_gpu_arm64_instance_type_name="test-gpu-arm64-instance-type",
            linux_gpu_x86_64_instance_type_name="test-gpu-x86_64-instance-type",
            linux_arm64_instance_type_name="test-linux-arm64-instance-type",
            linux_x86_64_instance_type_name="test-linux-x86_64-instance-type",
            cluster_manager_instance_type_name="test-cluster-manager-instance-type",
            service_host_instance_type_name="test-service-instance-type",
        ),
        region="test-region",
        remote_username="test-user",
        ssh_key_name="test-ssh-key-pair",
    )
    env = RibAwsEnv.get_aws_env_or_fail("test-aws-env")
    assert env.config == aws_env_config
    assert env.metadata == aws_env_metadata
    assert os.path.isdir(env.files.ansible_dir)
    with open(env.files.ansible_inventory_file, "r") as inventory:
        inventory_content = inventory.read()
        assert "test-aws-env" in inventory_content
        assert "test-region" in inventory_content


###
# _connect_ssh_client
###


@patch("rib.utils.ssh_utils.connect_ssh_client")
def test__connect_ssh_client_creates_client_when_none_exist(
    connect_ssh_client, aws_env
):
    connect_ssh_client.return_value = MagicMock()
    assert connect_ssh_client.return_value == aws_env._connect_ssh_client(
        hostname="host-address",
        port=2222,
        username="remote-username",
    )
    connect_ssh_client.assert_called_once()


@patch("rib.utils.ssh_utils.check_ssh_client_connected", MagicMock(return_value=False))
@patch("rib.utils.ssh_utils.connect_ssh_client")
def test__connect_ssh_client_creates_client_when_disconnected(
    connect_ssh_client, aws_env
):
    aws_env._ssh_clients["remote-username@host-address:2222"] = MagicMock()
    connect_ssh_client.return_value = MagicMock()
    assert connect_ssh_client.return_value == aws_env._connect_ssh_client(
        hostname="host-address",
        port=2222,
        username="remote-username",
    )
    connect_ssh_client.assert_called_once()


@patch("rib.utils.ssh_utils.check_ssh_client_connected", MagicMock(return_value=True))
@patch("rib.utils.ssh_utils.connect_ssh_client")
def test__connect_ssh_client_returns_cached_client(connect_ssh_client, aws_env):
    existing_client = MagicMock()
    aws_env._ssh_clients["remote-username@host-address:2222"] = existing_client
    assert existing_client == aws_env._connect_ssh_client(
        hostname="host-address",
        port=2222,
        username="remote-username",
    )
    connect_ssh_client.assert_not_called()


###
# _is_ec2_instances_cache_valid
###


def test__is_ec2_instances_cache_valid_returns_false_when_no_cluster_manager_role(
    aws_env,
):
    assert not aws_env._is_ec2_instances_cache_valid({})


def test__is_ec2_instances_cache_valid_returns_false_when_no_cluster_manager_ips(
    aws_env,
):
    assert not aws_env._is_ec2_instances_cache_valid({"cluster-manager": []})


@patch("requests.get", MagicMock(side_effect=Exception))
def test__is_ec2_instances_cache_valid_returns_false_when_exception_pinging_cluster_manager(
    aws_env,
):
    assert not aws_env._is_ec2_instances_cache_valid(
        {"cluster-manager": ["11.22.33.44"]}
    )


@patch("requests.get")
def test__is_ec2_instances_cache_valid_returns_false_when_failed_pinging_cluster_manager(
    mock_get,
    aws_env,
):
    response = Response()
    response.status_code = 404
    mock_get.return_value = response
    assert not aws_env._is_ec2_instances_cache_valid(
        {"cluster-manager": ["11.22.33.44"]}
    )


@patch("requests.get")
def test__is_ec2_instances_cache_valid_returns_true_when_success_pinging_cluster_manager(
    mock_get,
    aws_env,
):
    response = Response()
    response.status_code = 200
    mock_get.return_value = response
    assert aws_env._is_ec2_instances_cache_valid({"cluster-manager": ["11.22.33.44"]})


###
# _get_ec2_instance_ips
###


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
def test__get_ec2_instance_ips_performs_lookup_when_no_cache(aws_env):
    aws_env._ec2_instance_roles = [("role", 1)]
    assert aws_env._get_ec2_instance_ips() == {"role": ["11.22.33.44"]}


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
def test__get_ec2_instance_ips_performs_lookup_when_cache_is_invalid(aws_env):
    aws_env.files.read_cache.return_value = {"instances": {"role": ["44.33.22.11"]}}
    aws_env._is_ec2_instances_cache_valid = MagicMock(return_value=False)
    aws_env._ec2_instance_roles = [("role", 1)]
    assert aws_env._get_ec2_instance_ips() == {"role": ["11.22.33.44"]}


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
def test__get_ec2_instance_ips_performs_lookup_when_force_refresh(aws_env):
    aws_env.files.read_cache.return_value = {"instances": {"role": ["44.33.22.11"]}}
    aws_env._is_ec2_instances_cache_valid = MagicMock(return_value=True)
    aws_env._ec2_instance_roles = [("role", 1)]
    assert aws_env._get_ec2_instance_ips(force_refresh=True) == {
        "role": ["11.22.33.44"]
    }


@patch("rib.utils.aws_utils.get_ec2_instances")
def test__get_ec2_instance_ips_returns_cache_when_valid(get_ec2_instances, aws_env):
    aws_env.files.read_cache.return_value = {"instances": {"role": ["44.33.22.11"]}}
    aws_env._is_ec2_instances_cache_valid = MagicMock(return_value=True)
    aws_env._ec2_instance_roles = [("role", 1)]
    assert aws_env._get_ec2_instance_ips() == {"role": ["44.33.22.11"]}
    get_ec2_instances.assert_not_called()


@patch("rib.utils.aws_utils.get_ec2_instances")
def test__get_ec2_instance_ips_returns_cache_when_validation_disabled(
    get_ec2_instances, aws_env
):
    aws_env.files.read_cache.return_value = {"instances": {"role": ["44.33.22.11"]}}
    aws_env._is_ec2_instances_cache_valid = MagicMock(return_value=False)
    aws_env._ec2_instance_roles = [("role", 1)]
    assert aws_env._get_ec2_instance_ips(validate=False) == {"role": ["44.33.22.11"]}
    aws_env._is_ec2_instances_cache_valid.assert_not_called()
    get_ec2_instances.assert_not_called()


###
# _is_active
###


@patch(
    "rib.aws_env.rib_aws_env.RibAwsEnv.get_active_aws_envs",
    MagicMock(return_value=ActiveAwsEnvs(owned={"test-aws-env"}, unowned={})),
)
def test__is_active_when_active(aws_env):
    assert aws_env._is_active()


@patch(
    "rib.aws_env.rib_aws_env.RibAwsEnv.get_active_aws_envs",
    MagicMock(return_value=ActiveAwsEnvs(owned={}, unowned={})),
)
def test__is_active_when_not_active(aws_env):
    assert not aws_env._is_active()


###
# _is_in_use
###


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock(side_effect=socket.timeout))
def test__is_in_use_when_ssh_connection_failure(aws_env):
    assert not aws_env._is_in_use()


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock())
@patch("rib.utils.ssh_utils.run_ssh_command", MagicMock(return_value=(["[]"], None)))
def test__is_in_use_when_no_containers_running(aws_env):
    assert not aws_env._is_in_use()


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock())
@patch(
    "rib.utils.ssh_utils.run_ssh_command",
    MagicMock(return_value=(['[{"State":"stopped"}]'], None)),
)
def test__is_in_use_when_containers_stopped(aws_env):
    assert not aws_env._is_in_use()


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value=[]))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={"instance-id": {"addresses": {"public": {"ip": "11.22.33.44"}}}}
    ),
)
@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock())
@patch(
    "rib.utils.ssh_utils.run_ssh_command",
    MagicMock(return_value=(['[{"State":"running"}]'], None)),
)
def test__is_in_use_when_containers_running(aws_env):
    assert aws_env._is_in_use()


###
# _update_metadata
###


def test__update_metadata_rejects_invalid_keys(aws_env):
    with pytest.raises(error_utils.RIB700):
        aws_env._update_metadata({"not-a-metadata-key": "value"})


def test__update_metadata_accepts_valid_keys(aws_env):
    aws_env._update_metadata({"last_provision_command": "last-prov-cmd"})
    assert "last-prov-cmd" == aws_env.metadata["last_provision_command"]


###
# rename
###


@pytest.mark.usefixtures("rib_state_path")
def test_rename_raises_when_active():
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=True)
    with pytest.raises(error_utils.RIB724):
        old_env.rename("new-env-name")


@pytest.mark.usefixtures("rib_state_path")
def test_rename_when_inactive():
    assert not RibAwsEnv.aws_env_exists("new-env-name")
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=False)
    old_env.rename("new-env-name")
    assert not RibAwsEnv.aws_env_exists("compatible-env")
    new_env = RibAwsEnv.get_aws_env_or_fail("new-env-name")
    assert new_env.config.name == "new-env-name"
    assert "new-env-name" in new_env.metadata["create_command"]
    assert "compatible-env" not in new_env.metadata["create_command"]
    with open(new_env.files.ansible_inventory_file, "r") as inventory:
        inventory_content = inventory.read()
        assert "new-env-name" in inventory_content
        assert "compatible-env" not in inventory_content


###
# copy
###


@pytest.mark.usefixtures("rib_state_path")
def test_copy_raises_when_active():
    assert not RibAwsEnv.aws_env_exists("new-env-name")
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=True)
    with pytest.raises(error_utils.RIB724):
        old_env.copy("new-env-name")


@pytest.mark.usefixtures("rib_state_path")
def test_copy_with_force_when_active():
    assert not RibAwsEnv.aws_env_exists("new-env-name")
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=True)
    old_env.copy("new-env-name", force=True)
    assert RibAwsEnv.aws_env_exists("new-env-name")


@pytest.mark.usefixtures("rib_state_path")
def test_copy_when_inactive():
    assert not RibAwsEnv.aws_env_exists("new-env-name")
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=False)
    old_env.copy("new-env-name")
    assert RibAwsEnv.aws_env_exists("compatible-env")
    new_env = RibAwsEnv.get_aws_env_or_fail("new-env-name")
    assert new_env.config.name == "new-env-name"
    assert "new-env-name" in new_env.metadata["create_command"]
    assert "compatible-env" not in new_env.metadata["create_command"]
    with open(new_env.files.ansible_inventory_file, "r") as inventory:
        inventory_content = inventory.read()
        assert "new-env-name" in inventory_content
        assert "compatible-env" not in inventory_content


###
# remove
###


@pytest.mark.usefixtures("rib_state_path")
def test_remove_raises_when_active():
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=True)
    with pytest.raises(error_utils.RIB724):
        old_env.remove()


@pytest.mark.usefixtures("rib_state_path")
def test_remove_with_force_when_active():
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=True)
    old_env.remove(force=True)
    assert not RibAwsEnv.aws_env_exists("compatible-env")


@pytest.mark.usefixtures("rib_state_path")
def test_remove_when_inactive():
    old_env = RibAwsEnv.get_aws_env_or_fail("compatible-env")
    old_env._is_active = MagicMock(return_value=False)
    old_env.remove()
    assert not RibAwsEnv.aws_env_exists("compatible-env")


###
# _get_cloudformation_status
###


@patch("rib.utils.aws_utils.get_cf_stacks", MagicMock(return_value={}))
def test_cloudformation_status_when_no_stacks_present(aws_env):
    assert (
        aws_env._get_cloudformation_status()["status"] == AwsComponentStatus.NOT_PRESENT
    )


@patch(
    "rib.utils.aws_utils.get_cf_stacks",
    MagicMock(
        return_value={
            "race-test-aws-env-android-arm64-node-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-android-x86-64-node-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-cluster-manager": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-efs": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-linux-gpu-arm64-node-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-linux-gpu-x86-64-node-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-linux-arm64-node-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-linux-x86-64-node-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-network": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-service-host": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
        }
    ),
)
def test_cloudformation_status_when_all_stacks_are_ready(aws_env):
    assert aws_env._get_cloudformation_status()["status"] == AwsComponentStatus.READY


@patch(
    "rib.utils.aws_utils.get_cf_stacks",
    MagicMock(
        return_value={
            # Android node host stack is completely absent
            "race-test-aws-env-cluster-manager": {
                "status": "CREATE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-efs": {
                "status": "CREATE_IN_PROGRESS",
                "status_reason": "",
            },
            "race-test-aws-env-linux-gpu-x86-64-node-host": {
                "status": "CREATE_FAILED",
                "status_reason": "",
            },
            "race-test-aws-env-linux-arm64-node-host": {
                "status": "DELETE_COMPLETE",
                "status_reason": "",
            },
            "race-test-aws-env-network": {
                "status": "DELETE_FAILED",
                "status_reason": "",
            },
            "race-test-aws-env-service-host": {
                "status": "DELETE_IN_PROGRESS",
                "status_reason": "",
            },
        }
    ),
)
def test_cloudformation_status_when_stacks_have_mixed_statuses(aws_env):
    assert aws_env._get_cloudformation_status()["status"] == AwsComponentStatus.ERROR


def test_cloudformation_status_with_all_host_types(aws_env):
    assert (
        "race-test-aws-env-android-arm64-node-host"
        in aws_env._get_cloudformation_status()["children"]
    )
    assert (
        "race-test-aws-env-android-x86-64-node-host"
        in aws_env._get_cloudformation_status()["children"]
    )
    assert (
        "race-test-aws-env-linux-gpu-arm64-node-host"
        in aws_env._get_cloudformation_status()["children"]
    )
    assert (
        "race-test-aws-env-linux-gpu-x86-64-node-host"
        in aws_env._get_cloudformation_status()["children"]
    )
    assert (
        "race-test-aws-env-linux-arm64-node-host"
        in aws_env._get_cloudformation_status()["children"]
    )
    assert (
        "race-test-aws-env-linux-x86-64-node-host"
        in aws_env._get_cloudformation_status()["children"]
    )


def test_cloudformation_status_when_no_android_arm64_hosts(aws_env):
    aws_env.config.android_arm64_hosts.instance_count = 0
    assert (
        "race-test-aws-env-android-arm64-node-host"
        not in aws_env._get_cloudformation_status()["children"]
    )


def test_cloudformation_status_when_no_android_x86_64_hosts(aws_env):
    aws_env.config.android_x86_64_hosts.instance_count = 0
    assert (
        "race-test-aws-env-android-x86-64-node-host"
        not in aws_env._get_cloudformation_status()["children"]
    )


def test_cloudformation_status_when_no_gpu_arm64_hosts(aws_env):
    aws_env.config.linux_gpu_arm64_hosts.instance_count = 0
    assert (
        "race-test-aws-env-linux-gpu-arm64-node-host"
        not in aws_env._get_cloudformation_status()["children"]
    )


def test_cloudformation_status_when_no_gpu_x86_64_hosts(aws_env):
    aws_env.config.linux_gpu_x86_64_hosts.instance_count = 0
    assert (
        "race-test-aws-env-linux-gpu-x86-64-node-host"
        not in aws_env._get_cloudformation_status()["children"]
    )


def test_cloudformation_status_when_no_linux_arm64_hosts(aws_env):
    aws_env.config.linux_arm64_hosts.instance_count = 0
    assert (
        "race-test-aws-env-linux-arm64-node-host"
        not in aws_env._get_cloudformation_status()["children"]
    )


def test_cloudformation_status_when_no_linux_x86_64_hosts(aws_env):
    aws_env.config.linux_x86_64_hosts.instance_count = 0
    assert (
        "race-test-aws-env-linux-x86-64-node-host"
        not in aws_env._get_cloudformation_status()["children"]
    )


###
# _get_host_requirements_status
###


@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock(side_effect=socket.timeout))
def test__get_host_requirements_status_when_socket_timeout(aws_env):
    assert aws_env._get_host_requirements_status(
        {"addresses": {"public": {"ip": "11.22.33.44"}}}
    ) == StatusReport(
        status=AwsComponentStatus.NOT_READY,
        reason=None,
        children={
            "ssh": StatusReport(
                status=AwsComponentStatus.NOT_READY,
                reason="SSH timeout/no connection",
            )
        },
    )


@patch(
    "rib.utils.ssh_utils.connect_ssh_client",
    MagicMock(
        side_effect=paramiko.ssh_exception.NoValidConnectionsError(
            errors={("11.22.33.44, 2222"): "error"}
        )
    ),
)
def test__get_host_requirements_status_when_no_valid_connections(aws_env):
    assert aws_env._get_host_requirements_status(
        {"addresses": {"public": {"ip": "11.22.33.44"}}}
    ) == StatusReport(
        status=AwsComponentStatus.NOT_READY,
        reason=None,
        children={
            "ssh": StatusReport(
                status=AwsComponentStatus.NOT_READY,
                reason="SSH timeout/no connection",
            )
        },
    )


@patch(
    "rib.utils.ssh_utils.connect_ssh_client",
    MagicMock(side_effect=paramiko.ssh_exception.AuthenticationException),
)
def test__get_host_requirements_status_when_no_valid_connections(aws_env):
    assert aws_env._get_host_requirements_status(
        {"addresses": {"public": {"ip": "11.22.33.44"}}}
    ) == StatusReport(
        status=AwsComponentStatus.ERROR,
        reason=None,
        children={
            "ssh": StatusReport(
                status=AwsComponentStatus.ERROR,
                reason="Invalid SSH credentials: AuthenticationException()",
            )
        },
    )


@patch(
    "rib.utils.ssh_utils.connect_ssh_client",
    MagicMock(side_effect=Exception()),
)
def test__get_host_requirements_status_when_unhandled_exception(aws_env):
    assert aws_env._get_host_requirements_status(
        {"addresses": {"public": {"ip": "11.22.33.44"}}}
    ) == StatusReport(
        status=AwsComponentStatus.ERROR,
        reason=None,
        children={
            "ssh": StatusReport(
                status=AwsComponentStatus.ERROR,
                reason="Unhandled SSH error: Exception()",
            )
        },
    )


@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock(return_value=None))
@patch(
    "rib.utils.ssh_utils.run_ssh_command",
    MagicMock(
        side_effect=[
            (["inactive"], []),  # docker info
            (["mountpoint: /data: No such file or directory"], []),
        ]
    ),
)
def test__get_host_requirements_status_when_not_ready(aws_env):
    assert aws_env._get_host_requirements_status(
        {"addresses": {"public": {"ip": "11.22.33.44"}}}
    ) == StatusReport(
        status=AwsComponentStatus.NOT_READY,
        reason=None,
        children={
            "ssh": StatusReport(status=AwsComponentStatus.READY),
            "docker": StatusReport(
                status=AwsComponentStatus.NOT_READY, reason="Docker swarm is not active"
            ),
            "data_mount": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )


@patch("rib.utils.ssh_utils.connect_ssh_client", MagicMock(return_value=None))
@patch(
    "rib.utils.ssh_utils.run_ssh_command",
    MagicMock(
        side_effect=[
            (["active"], []),  # docker info
            (["/data is a mountpoint"], []),
        ]
    ),
)
def test__get_host_requirements_status_when_ready(aws_env):
    assert aws_env._get_host_requirements_status(
        {"addresses": {"public": {"ip": "11.22.33.44"}}}
    ) == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "ssh": StatusReport(status=AwsComponentStatus.READY),
            "docker": StatusReport(status=AwsComponentStatus.READY),
            "data_mount": StatusReport(status=AwsComponentStatus.READY),
        },
    )


###
# _get_ec2_instance_status
###


def test__get_ec2_instance_status_when_not_ready(aws_env):
    assert aws_env._get_ec2_instance_status(
        {"state": {"Name": "pending"}}
    ) == StatusReport(
        status=AwsComponentStatus.NOT_READY,
        reason=None,
        children={
            "EC2_state": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )


def test__get_ec2_instance_status_when_ready(aws_env):
    aws_env._get_host_requirements_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_instance_status(
        {"state": {"Name": "running"}}
    ) == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "EC2_state": StatusReport(status=AwsComponentStatus.READY),
            "host_requirements": StatusReport(status=AwsComponentStatus.READY),
        },
    )


###
# _get_ec2_role_status
###


@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id-1": {
                "addresses": {"public": {"dns": "instance-1-name"}},
                "id": "instance-id-1",
            },
            "instance-id-2": {
                "addresses": {"public": {"dns": None}},
                "id": "instance-id-2",
            },
        }
    ),
)
def test__get_ec2_role_status_when_not_ready(aws_env):
    aws_env._get_ec2_instance_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.NOT_READY),
    )
    assert aws_env._get_ec2_role_status(
        role="linux-host", expected_count=2, all_instances={}
    ) == StatusReport(
        status=AwsComponentStatus.NOT_READY,
        reason=None,
        children={
            "instance-1-name": StatusReport(status=AwsComponentStatus.NOT_READY),
            "instance-id-2": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )


@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id-1": {
                "addresses": {"public": {"dns": "instance-1-name"}},
                "id": "instance-id-1",
                "_mock_instance_status": StatusReport(status=AwsComponentStatus.READY),
            },
            "instance-id-2": {
                "addresses": {"public": {"dns": "instance-2-name"}},
                "id": "instance-id-2",
                "_mock_instance_status": StatusReport(status=AwsComponentStatus.READY),
            },
            "instance-id-3": {
                "addresses": {"public": {"dns": None}},
                "id": "instance-id-3",
                "_mock_instance_status": StatusReport(
                    status=AwsComponentStatus.NOT_PRESENT
                ),
            },
        }
    ),
)
def test__get_ec2_role_status_when_ready(aws_env):
    aws_env._get_ec2_instance_status = MagicMock(
        side_effect=lambda instance: instance["_mock_instance_status"],
    )
    assert aws_env._get_ec2_role_status(
        role="linux-host", expected_count=2, all_instances={}
    ) == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "instance-1-name": StatusReport(status=AwsComponentStatus.READY),
            "instance-2-name": StatusReport(status=AwsComponentStatus.READY),
            "instance-id-3": StatusReport(status=AwsComponentStatus.NOT_PRESENT),
        },
    )


@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id-1": {
                "addresses": {"public": {"dns": "instance-1-name"}},
                "id": "instance-id-1",
                "_mock_instance_status": StatusReport(status=AwsComponentStatus.READY),
            },
            "instance-id-2": {
                "addresses": {"public": {"dns": "instance-2-name"}},
                "id": "instance-id-2",
                "_mock_instance_status": StatusReport(status=AwsComponentStatus.READY),
            },
            "instance-id-3": {
                "addresses": {"public": {"dns": None}},
                "id": "instance-id-3",
                "_mock_instance_status": StatusReport(
                    status=AwsComponentStatus.NOT_READY
                ),
            },
        }
    ),
)
def test__get_ec2_role_status_when_more_instances_than_expected(aws_env):
    aws_env._get_ec2_instance_status = MagicMock(
        side_effect=lambda instance: instance["_mock_instance_status"],
    )
    assert aws_env._get_ec2_role_status(
        role="linux-host", expected_count=2, all_instances={}
    ) == StatusReport(
        status=AwsComponentStatus.ERROR,
        reason="Expected 2 instances but found 3",
        children={
            "instance-1-name": StatusReport(status=AwsComponentStatus.READY),
            "instance-2-name": StatusReport(status=AwsComponentStatus.READY),
            "instance-id-3": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )


@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(return_value={}),
)
def test__get_ec2_role_status_when_no_instances_running(aws_env):
    assert aws_env._get_ec2_role_status(
        role="linux-host", expected_count=2, all_instances={}
    ) == StatusReport(status=AwsComponentStatus.NOT_PRESENT)


###
# _get_ec2_status
###


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_all_host_types(aws_env):
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_no_android_arm64_hosts(aws_env):
    aws_env.config.android_arm64_hosts.instance_count = 0
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_no_android_x86_64_hosts(aws_env):
    aws_env.config.android_x86_64_hosts.instance_count = 0
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_no_gpu_arm64_hosts(aws_env):
    aws_env.config.linux_gpu_arm64_hosts.instance_count = 0
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_no_gpu_x86_64_hosts(aws_env):
    aws_env.config.linux_gpu_x86_64_hosts.instance_count = 0
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_no_linux_arm64_hosts(aws_env):
    aws_env.config.linux_arm64_hosts.instance_count = 0
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
def test__get_ec2_status_when_no_linux_x86_64_hosts(aws_env):
    aws_env.config.linux_x86_64_hosts.instance_count = 0
    aws_env._get_ec2_role_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    assert aws_env._get_ec2_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "cluster-manager": StatusReport(status=AwsComponentStatus.READY),
            "service-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "linux-gpu-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-arm64-node-host": StatusReport(status=AwsComponentStatus.READY),
            "android-x86-64-node-host": StatusReport(status=AwsComponentStatus.READY),
        },
    )


###
# _get_efs_status
###


@patch(
    "rib.utils.aws_utils.get_efs_filesystems",
    MagicMock(
        return_value={
            "race-test-aws-env-DataFileSystem": {"state": "available"},
        }
    ),
)
def test__get_efs_status(aws_env):
    assert aws_env._get_efs_status() == StatusReport(
        status=AwsComponentStatus.READY,
        reason=None,
        children={
            "race-test-aws-env-DataFileSystem": StatusReport(
                status=AwsComponentStatus.READY
            ),
        },
    )


###
# get_status_report
###


def test_get_status_report(aws_env):
    aws_env._get_cloudformation_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.READY)
    )
    aws_env._get_ec2_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.NOT_PRESENT)
    )
    aws_env._get_efs_status = MagicMock(
        return_value=StatusReport(status=AwsComponentStatus.NOT_READY)
    )
    assert aws_env.get_status_report() == AwsEnvStatus(
        status=AwsComponentStatus.NOT_READY,
        components={
            "cloud_formation": StatusReport(status=AwsComponentStatus.READY),
            "ec2_instance": StatusReport(status=AwsComponentStatus.NOT_PRESENT),
            "efs": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )


###
# get_runtime_info
###


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id": {
                "addresses": {
                    "public": {
                        "dns": "public-dns-name",
                        "ip": "11.22.33.44",
                    },
                    "private": {
                        "dns": "private-dns-name",
                        "ip": "10.0.0.2",
                    },
                },
                "tags": {
                    "AwsEnvName": "test-aws-name",
                    "aws:internal-tag": "internal-tag-value",
                },
            }
        }
    ),
)
def test_get_runtime_info_missing_container_status_for_role(aws_env):
    aws_env.run_remote_command = MagicMock(return_value={})

    aws_env.config.android_arm64_hosts.instance_count = 0
    aws_env.config.android_x86_64_hosts.instance_count = 0
    aws_env.config.linux_gpu_arm64_hosts.instance_count = 0
    aws_env.config.linux_gpu_x86_64_hosts.instance_count = 0
    aws_env.config.linux_arm64_hosts.instance_count = 0
    aws_env.config.linux_x86_64_hosts.instance_count = 0
    assert aws_env.get_runtime_info() == {
        "cluster-manager": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {},
            }
        ],
        "service-host": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {},
            }
        ],
    }


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id": {
                "addresses": {
                    "public": {
                        "dns": "public-dns-name",
                        "ip": "11.22.33.44",
                    },
                    "private": {
                        "dns": "private-dns-name",
                        "ip": "10.0.0.2",
                    },
                },
                "tags": {
                    "AwsEnvName": "test-aws-name",
                    "aws:internal-tag": "internal-tag-value",
                },
            }
        }
    ),
)
def test_get_runtime_info_missing_container_status_for_instance(aws_env):
    aws_env.run_remote_command = MagicMock(
        return_value={
            "cluster-manager": {},
            "service-host": {"11.22.33.44": {"success": False}},
        }
    )

    aws_env.config.android_arm64_hosts.instance_count = 0
    aws_env.config.android_x86_64_hosts.instance_count = 0
    aws_env.config.linux_gpu_arm64_hosts.instance_count = 0
    aws_env.config.linux_gpu_x86_64_hosts.instance_count = 0
    aws_env.config.linux_arm64_hosts.instance_count = 0
    aws_env.config.linux_x86_64_hosts.instance_count = 0
    assert aws_env.get_runtime_info() == {
        "cluster-manager": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {},
            }
        ],
        "service-host": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {},
            }
        ],
    }


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id": {
                "addresses": {
                    "public": {
                        "dns": "public-dns-name",
                        "ip": "11.22.33.44",
                    },
                    "private": {
                        "dns": "private-dns-name",
                        "ip": "10.0.0.2",
                    },
                },
                "tags": {
                    "AwsEnvName": "test-aws-name",
                    "aws:internal-tag": "internal-tag-value",
                },
            }
        }
    ),
)
def test_get_runtime_info_bad_container_status_json(aws_env):
    aws_env.run_remote_command = MagicMock(
        return_value={
            "cluster-manager": {
                "11.22.33.44": {
                    "success": True,
                    "stdout": ["not a json object"],
                }
            },
            "service-host": {
                "11.22.33.44": {
                    "success": True,
                    "stdout": ['["not a json object"]'],
                }
            },
        }
    )

    aws_env.config.android_arm64_hosts.instance_count = 0
    aws_env.config.android_x86_64_hosts.instance_count = 0
    aws_env.config.linux_gpu_arm64_hosts.instance_count = 0
    aws_env.config.linux_gpu_x86_64_hosts.instance_count = 0
    aws_env.config.linux_arm64_hosts.instance_count = 0
    aws_env.config.linux_x86_64_hosts.instance_count = 0
    assert aws_env.get_runtime_info() == {
        "cluster-manager": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {},
            }
        ],
        "service-host": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {},
            }
        ],
    }


@patch("rib.utils.aws_utils.get_ec2_instances", MagicMock(return_value={}))
@patch(
    "rib.utils.aws_utils.filter_ec2_instances_by_tags_and_state",
    MagicMock(
        return_value={
            "instance-id": {
                "addresses": {
                    "public": {
                        "dns": "public-dns-name",
                        "ip": "11.22.33.44",
                    },
                    "private": {
                        "dns": "private-dns-name",
                        "ip": "10.0.0.2",
                    },
                },
                "tags": {
                    "AwsEnvName": "test-aws-name",
                    "aws:internal-tag": "internal-tag-value",
                },
            }
        }
    ),
)
def test_get_runtime_info_with_container_status(aws_env):
    aws_env.run_remote_command = MagicMock(
        return_value={
            "cluster-manager": {
                "11.22.33.44": {
                    "success": True,
                    "stdout": ['[{"Names":["container_name"],"State":"running"}]'],
                }
            },
            "service-host": {
                "11.22.33.44": {
                    "success": True,
                    "stdout": [
                        '[{"Names":["container_name"],',
                        '"Labels":{"race.rib.deployment-name":"name_of_deployment"},'
                        '"State":"unhealthy"}]',
                    ],
                }
            },
        }
    )

    aws_env.config.android_arm64_hosts.instance_count = 0
    aws_env.config.android_x86_64_hosts.instance_count = 0
    aws_env.config.linux_gpu_arm64_hosts.instance_count = 0
    aws_env.config.linux_gpu_x86_64_hosts.instance_count = 0
    aws_env.config.linux_arm64_hosts.instance_count = 0
    aws_env.config.linux_x86_64_hosts.instance_count = 0
    assert aws_env.get_runtime_info() == {
        "cluster-manager": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {
                    "container_name": {
                        "deployment_name": "",
                        "state": "running",
                        "status": "",
                    }
                },
            }
        ],
        "service-host": [
            {
                "public_dns": "public-dns-name",
                "public_ip": "11.22.33.44",
                "private_dns": "private-dns-name",
                "private_ip": "10.0.0.2",
                "tags": {"AwsEnvName": "test-aws-name"},
                "containers": {
                    "container_name": {
                        "deployment_name": "name_of_deployment",
                        "state": "unhealthy",
                        "status": "",
                    }
                },
            }
        ],
    }


###
# provision
###


def test_provision_raises_when_in_use(aws_env):
    aws_env._is_in_use = MagicMock(return_value=True)
    with pytest.raises(error_utils.RIB723):
        aws_env.provision(
            provision_command="test-provision-command",
            current_username="test@unit-test.com",
        )


@patch("rib.utils.ansible_utils.run_playbook", MagicMock())
@patch("rib.utils.system_utils.get_cpu_count", MagicMock(return_value=2))
@patch("rib.utils.network_utils.get_public_ip", MagicMock(return_value="11.22.33.44"))
def test_provision_with_force_when_in_use(aws_env):
    aws_env._is_in_use = MagicMock(return_value=True)
    aws_env._update_metadata = MagicMock()
    aws_env.get_status_report = MagicMock(
        return_value=AwsEnvStatus(status=AwsComponentStatus.READY, components={})
    )
    aws_env.provision(
        provision_command="test-provision-command",
        current_username="test@unit-test.com",
        force=True,
    )


@patch("rib.utils.ansible_utils.run_playbook", MagicMock())
@patch("rib.utils.system_utils.get_cpu_count", MagicMock(return_value=2))
@patch("rib.utils.network_utils.get_public_ip", MagicMock(return_value="11.22.33.44"))
def test_provision_raises_when_post_status_is_not_ready(aws_env):
    aws_env._is_in_use = MagicMock(return_value=False)
    aws_env._update_metadata = MagicMock()
    aws_env.get_status_report = MagicMock(
        return_value=AwsEnvStatus(status=AwsComponentStatus.NOT_READY, components={})
    )
    with pytest.raises(error_utils.RIB712):
        aws_env.provision(
            provision_command="test-provision-command",
            current_username="test@unit-test.com",
        )


###
# unprovision
###


def test_unprovision_raises_when_in_use(aws_env):
    aws_env._is_in_use = MagicMock(return_value=True)
    with pytest.raises(error_utils.RIB723):
        aws_env.unprovision(unprovision_command="test-unprovision-command")


@patch("rib.utils.ansible_utils.run_playbook", MagicMock())
@patch("rib.utils.system_utils.get_cpu_count", MagicMock(return_value=2))
def test_unprovision_with_force_when_in_use(aws_env):
    aws_env._is_in_use = MagicMock(return_value=True)
    aws_env._update_metadata = MagicMock()
    aws_env.get_status_report = MagicMock(
        return_value=AwsEnvStatus(status=AwsComponentStatus.NOT_PRESENT, components={})
    )
    aws_env.unprovision(
        unprovision_command="test-unprovision-command",
        force=True,
    )


@patch("rib.utils.ansible_utils.run_playbook", MagicMock())
@patch("rib.utils.system_utils.get_cpu_count", MagicMock(return_value=2))
def test_unprovision_raises_when_post_status_isnt_not_present(aws_env):
    aws_env._is_in_use = MagicMock(return_value=False)
    aws_env._update_metadata = MagicMock()
    aws_env.get_status_report = MagicMock(
        return_value=AwsEnvStatus(status=AwsComponentStatus.NOT_READY, components={})
    )
    with pytest.raises(error_utils.RIB712):
        aws_env.unprovision(unprovision_command="test-unprovision-command")


@patch("rib.utils.ansible_utils.run_playbook")
@patch("rib.utils.system_utils.get_cpu_count", MagicMock(return_value=2))
def test_unprovision_sets_timeout_per_cf_stack(run_playbook, aws_env):
    aws_env._is_in_use = MagicMock(return_value=False)
    aws_env._update_metadata = MagicMock()
    aws_env.get_status_report = MagicMock(
        return_value=AwsEnvStatus(status=AwsComponentStatus.NOT_PRESENT, components={})
    )
    aws_env.unprovision(
        unprovision_command="test-unprovision-command",
        timeout=125,
    )

    assert run_playbook.call_args.kwargs["playbook_vars"]["stackDeleteTimeout"] == 125
    # network, efs, cluster-manager, service-host, linux/gpu/android arm/x86 hosts = 10 stacks
    assert run_playbook.call_args.kwargs["timeout"] == 125 * 10


###
# get_cluster_manager_ip
###


def test_get_cluster_manager_ip_when_no_cluster_manager_role(aws_env):
    aws_env._get_ec2_instance_ips = MagicMock(return_value={})
    assert aws_env.get_cluster_manager_ip() == None


def test_get_cluster_manager_ip_when_no_cluster_manager_ips(aws_env):
    aws_env._get_ec2_instance_ips = MagicMock(return_value={"cluster-manager": []})
    assert aws_env.get_cluster_manager_ip() == None


def test_get_cluster_manager_ip_when_cluster_manager_ip_exists(aws_env):
    aws_env._get_ec2_instance_ips = MagicMock(
        return_value={"cluster-manager": ["11.22.33.44"]}
    )
    assert aws_env.get_cluster_manager_ip() == "11.22.33.44"


###
# run_playbook
###


@patch("rib.utils.ansible_utils.run_playbook")
@patch("rib.utils.system_utils.get_cpu_count", MagicMock(return_value=2))
def test_run_playbook(run_playbook, aws_env):
    aws_env.run_playbook(
        dry_run=True,
        playbook_file="test-playbook-file",
        playbook_vars={"key": "value"},
        timeout=123,
        verbosity=2,
    )
    assert run_playbook.call_args.args[0] == "test-playbook-file"
    assert run_playbook.call_args.kwargs["dry_run"]
    assert run_playbook.call_args.kwargs["playbook_vars"] == {"key": "value"}
    assert run_playbook.call_args.kwargs["timeout"] == 123
    assert run_playbook.call_args.kwargs["verbosity"] == 2

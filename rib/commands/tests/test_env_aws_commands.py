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
    Test file for env_aws_commands.py
"""

# Python Library Imports
import click
import json
import os
import pytest
import yaml
from click.testing import CliRunner
from unittest.mock import MagicMock, patch, create_autospec

# Local Library Imports
from rib.aws_env.rib_aws_env import RibAwsEnv
from rib.aws_env.rib_aws_env_status import (
    ActiveAwsEnvs,
    AwsComponentStatus,
    AwsEnvStatus,
    IncompatibleAwsEnv,
    LocalAwsEnvs,
)
from rib.commands import env_aws_commands
from rib.utils import error_utils
from rib.utils.aws_topology_utils import (
    InstanceCounts,
    InstanceEbsSizes,
    InstanceTypeNames,
    NodeInstanceCapacity,
    NodeInstanceTopology,
)
from rib.utils.status_utils import StatusReport


###
# Fixtures
###


class RibState:
    """Mock RiB state object"""

    pass


@pytest.fixture
def rib_state() -> object:
    """Mock RiB state object"""
    state = RibState()
    state.detail_level = 0
    return state


@pytest.fixture
def rib_aws_env() -> RibAwsEnv:
    """Mocked RibAwsEnv class"""
    with patch(
        "rib.commands.env_aws_commands.RibAwsEnv", create_autospec(RibAwsEnv)
    ) as env:
        yield env


###
# active
###


def test_active_no_active_envs(rib_aws_env):
    rib_aws_env.get_active_aws_envs.return_value = ActiveAwsEnvs(owned={}, unowned={})

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.active, [])

    assert "No Active AWS Environments Found" in result.output
    assert "My Active AWS Environments" not in result.output
    assert "Other Active AWS Environments" not in result.output


def test_active_with_owned_and_unowned_envs(rib_aws_env):
    rib_aws_env.get_active_aws_envs.return_value = ActiveAwsEnvs(
        owned={"my-env"}, unowned={"their-env"}
    )

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.active, [])

    assert "No Active AWS Environments Found" not in result.output
    assert "My Active AWS Environments" in result.output
    assert "my-env" in result.output
    assert "Other Active AWS Environments" in result.output
    assert "their-env" in result.output


###
# copy
###


def test_copy_raises_when_new_env_already_exists(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.copy, ["--from=old-env-name", "--to=new-env-name"]
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, error_utils.RIB707)


def test_copy(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = False
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env

    runner = CliRunner()

    # no force
    result = runner.invoke(
        env_aws_commands.copy, ["--from=old-env-name", "--to=new-env-name"]
    )
    assert result.exit_code == 0
    rib_aws_env.get_aws_env_or_fail.assert_called_with("old-env-name")
    rib_aws_env.copy.assert_called_with(name="new-env-name", force=False)

    # with force
    result = runner.invoke(
        env_aws_commands.copy, ["--from=old-env-name", "--to=new-env-name", "--force"]
    )
    assert result.exit_code == 0
    rib_aws_env.get_aws_env_or_fail.assert_called_with("old-env-name")
    rib_aws_env.copy.assert_called_with(name="new-env-name", force=True)


###
# create
###


@patch("rib.utils.aws_topology_utils.read_topology_from_file")
@patch("click.confirm", MagicMock(side_effect=click.Abort))
def test_create_from_topology_file(read_topology_from_file):
    read_topology_from_file.return_value = NodeInstanceTopology(
        android_arm64_instances=[NodeInstanceCapacity(android_client_count=1)],
        android_x86_64_instances=[
            NodeInstanceCapacity(android_client_count=1) for _ in range(2)
        ],
        linux_gpu_arm64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1) for _ in range(3)
        ],
        linux_gpu_x86_64_instances=[
            NodeInstanceCapacity(linux_gpu_client_count=1) for _ in range(4)
        ],
        linux_arm64_instances=[
            NodeInstanceCapacity(linux_client_count=1) for _ in range(5)
        ],
        linux_x86_64_instances=[
            NodeInstanceCapacity(linux_client_count=1) for _ in range(6)
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--topology=./topology.json",
        ],
    )

    read_topology_from_file.assert_called_with("./topology.json")
    assert "1 a1.metal EC2 instances for RACE nodes" in result.output
    assert "2 c5.metal EC2 instances for RACE nodes" in result.output
    assert "3 g5g.2xlarge EC2 instances for RACE nodes" in result.output
    assert "4 p3.2xlarge EC2 instances for RACE nodes" in result.output
    assert "5 t4g.xlarge EC2 instances for RACE nodes" in result.output
    assert "6 t3a.2xlarge EC2 instances for RACE nodes" in result.output
    assert "1 t3a.2xlarge EC2 instance as the cluster manager" in result.output
    assert "1 t3a.2xlarge EC2 instance as the external service host" in result.output


def test_create_raises_when_no_node_host_counts_provided():
    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
        ],
    )
    assert isinstance(result.exception, error_utils.RIB720)


@patch("click.confirm", MagicMock(side_effect=click.Abort))
def test_create_with_explicit_instance_counts_provided():
    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--android-arm64-instance-count=1",
            "--android-x86_64-instance-count=2",
            "--linux-gpu-arm64-instance-count=3",
            "--linux-gpu-x86_64-instance-count=4",
            "--linux-arm64-instance-count=5",
            "--linux-x86_64-instance-count=6",
        ],
    )

    assert "1 a1.metal EC2 instances for RACE nodes" in result.output
    assert "2 c5.metal EC2 instances for RACE nodes" in result.output
    assert "3 g5g.2xlarge EC2 instances for RACE nodes" in result.output
    assert "4 p3.2xlarge EC2 instances for RACE nodes" in result.output
    assert "5 t4g.xlarge EC2 instances for RACE nodes" in result.output
    assert "6 t3a.2xlarge EC2 instances for RACE nodes" in result.output
    assert "1 t3a.2xlarge EC2 instance as the cluster manager" in result.output
    assert "1 t3a.2xlarge EC2 instance as the external service host" in result.output


@patch("click.confirm", MagicMock())
def test_create_raises_when_env_already_exists(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--linux-x86_64-instance-count=1",
        ],
    )
    assert isinstance(result.exception, error_utils.RIB707)


@patch("click.confirm", MagicMock())
def test_create_removes_existing_env_with_force(rib_aws_env, rib_state):
    rib_aws_env.aws_env_exists.return_value = True
    rib_aws_env.load_aws_env.return_value = rib_aws_env

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--linux-x86_64-instance-count=1",
            "--force",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    rib_aws_env.remove.assert_called_once()


@patch("click.confirm", MagicMock(side_effect=[True, False]))
def test_create_aborts_when_legacy_env_removal_is_not_confirmed(rib_aws_env, rib_state):
    rib_aws_env.aws_env_exists.return_value = True
    rib_aws_env.load_aws_env.return_value = None

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--linux-x86_64-instance-count=1",
            "--force",
        ],
        obj=rib_state,
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, SystemExit)

    rib_aws_env.remove.assert_not_called()
    rib_aws_env.remove_legacy_aws_env.assert_not_called()


@patch("click.confirm", MagicMock(side_effect=[True, True]))
def test_create_removes_legacy_existing_env_with_force(rib_aws_env, rib_state):
    rib_aws_env.aws_env_exists.return_value = True
    rib_aws_env.load_aws_env.return_value = None

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--linux-x86_64-instance-count=1",
            "--force",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0

    rib_aws_env.remove.assert_not_called()
    rib_aws_env.remove_legacy_aws_env.assert_called_with("test-aws-env")


@patch("click.confirm", MagicMock())
@patch(
    "rib.utils.click_utils.get_run_command",
    MagicMock(return_value="test-create-command"),
)
def test_create_with_default_parameters(rib_aws_env, rib_state):
    rib_aws_env.aws_env_exists.return_value = False

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--linux-x86_64-instance-count=1",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0

    rib_aws_env.create.assert_called_with(
        aws_env_name="test-aws-env",
        create_command="test-create-command",
        instance_counts=InstanceCounts(linux_x86_64_instances=1),
        instance_ebs_sizes=InstanceEbsSizes(
            android_instance_ebs_size_gb=128,
            linux_gpu_instance_ebs_size_gb=128,
            linux_instance_ebs_size_gb=64,
            cluster_manager_instance_ebs_size_gb=64,
            service_host_instance_ebs_size_gb=64,
        ),
        instance_type_names=InstanceTypeNames(
            android_arm64_instance_type_name="a1.metal",
            android_x86_64_instance_type_name="c5.metal",
            linux_gpu_arm64_instance_type_name="g5g.2xlarge",
            linux_gpu_x86_64_instance_type_name="p3.2xlarge",
            linux_arm64_instance_type_name="t4g.xlarge",
            linux_x86_64_instance_type_name="t3a.2xlarge",
            cluster_manager_instance_type_name="t3a.2xlarge",
            service_host_instance_type_name="t3a.2xlarge",
        ),
        region="us-east-1",
        remote_username="rib",
        ssh_key_name="test-ssh-key-pair",
    )


@patch(
    "rib.utils.click_utils.get_run_command",
    MagicMock(return_value="test-create-command"),
)
def test_create_with_explicit_parameters(rib_aws_env, rib_state):
    rib_aws_env.aws_env_exists.return_value = False

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.create,
        [
            "--name=test-aws-env",
            "--ssh-key-name=test-ssh-key-pair",
            "--remote-username=test-user",
            "--region=test-region",
            "--android-arm64-instance-type=test-android-arm-instance-type.large",
            "--android-x86_64-instance-type=test-android-x86-instance-type.large",
            "--linux-arm64-instance-type=test-linux-arm-instance-type.large",
            "--linux-x86_64-instance-type=test-linux-x86-instance-type.large",
            "--linux-gpu-arm64-instance-type=test-gpu-arm-instance-type.large",
            "--linux-gpu-x86_64-instance-type=test-gpu-x86-instance-type.large",
            "--cluster-manager-instance-type=test-cluster-manager-instance-type.large",
            "--service-host-instance-type=test-service-instance-type.large",
            "--android-instance-ebs-size=768",
            "--linux-instance-ebs-size=32",
            "--linux-gpu-instance-ebs-size=512",
            "--cluster-manager-instance-ebs-size=128",
            "--service-host-instance-ebs-size=1024",
            "--android-x86_64-instance-count=1",
            "--linux-x86_64-instance-count=2",
            "--linux-gpu-x86_64-instance-count=3",
            "--android-arm64-instance-count=4",
            "--linux-arm64-instance-count=5",
            "--linux-gpu-arm64-instance-count=6",
            "--yes",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0

    rib_aws_env.create.assert_called_with(
        aws_env_name="test-aws-env",
        create_command="test-create-command",
        instance_counts=InstanceCounts(
            android_arm64_instances=4,
            android_x86_64_instances=1,
            linux_gpu_arm64_instances=6,
            linux_gpu_x86_64_instances=3,
            linux_arm64_instances=5,
            linux_x86_64_instances=2,
        ),
        instance_ebs_sizes=InstanceEbsSizes(
            android_instance_ebs_size_gb=768,
            linux_gpu_instance_ebs_size_gb=512,
            linux_instance_ebs_size_gb=32,
            cluster_manager_instance_ebs_size_gb=128,
            service_host_instance_ebs_size_gb=1024,
        ),
        instance_type_names=InstanceTypeNames(
            android_arm64_instance_type_name="test-android-arm-instance-type.large",
            android_x86_64_instance_type_name="test-android-x86-instance-type.large",
            linux_gpu_arm64_instance_type_name="test-gpu-arm-instance-type.large",
            linux_gpu_x86_64_instance_type_name="test-gpu-x86-instance-type.large",
            linux_arm64_instance_type_name="test-linux-arm-instance-type.large",
            linux_x86_64_instance_type_name="test-linux-x86-instance-type.large",
            cluster_manager_instance_type_name="test-cluster-manager-instance-type.large",
            service_host_instance_type_name="test-service-instance-type.large",
        ),
        region="test-region",
        remote_username="test-user",
        ssh_key_name="test-ssh-key-pair",
    )


###
# info
###


def test_info_with_default_yaml_format(rib_aws_env):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.config = MagicMock()
    rib_aws_env.config.dict = MagicMock(return_value={"name": "test-aws-env"})
    rib_aws_env.metadata = {"created": "just now"}

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.info,
        [
            "--name=test-aws-env",
        ],
    )
    assert result.exit_code == 0
    assert yaml.safe_load(result.output) == {
        "config": {"name": "test-aws-env"},
        "metadata": {"created": "just now"},
    }


def test_info_with_json_format(rib_aws_env):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.config = MagicMock()
    rib_aws_env.config.dict = MagicMock(return_value={"name": "test-aws-env"})
    rib_aws_env.metadata = {"created": "just now"}

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.info,
        [
            "--name=test-aws-env",
            "--format=json",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "config": {"name": "test-aws-env"},
        "metadata": {"created": "just now"},
    }


###
# list
###


def test_list_no_defined_envs(rib_aws_env):
    rib_aws_env.get_local_aws_envs.return_value = LocalAwsEnvs(
        compatible={}, incompatible={}
    )

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.list_envs, [])

    assert "No AWS Environments Found" in result.output
    assert "Compatible AWS Environments" not in result.output
    assert "Incompatible AWS Environments" not in result.output


def test_list_with_compatible_and_incompatible_envs(rib_aws_env):
    rib_aws_env.get_local_aws_envs.return_value = LocalAwsEnvs(
        compatible={"compatible-env"},
        incompatible={
            IncompatibleAwsEnv(name="incompatible-env", rib_version="old-rib-version")
        },
    )

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.list_envs, [])

    assert "No AWS Environments Found" not in result.output
    assert "Compatible AWS Environments" in result.output
    assert "compatible-env" in result.output
    assert "Incompatible AWS Environments" in result.output
    assert "incompatible-env (RiB old-rib-version)" in result.output


###
# provision
###


@patch(
    "rib.utils.click_utils.get_run_command",
    MagicMock(return_value="test-provision-command"),
)
def test_provision_with_default_parameters(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env

    os.environ["HOST_USER"] = "test-user"

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.provision,
        [
            "--name=test-aws-env",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    rib_aws_env.provision.assert_called_with(
        current_username="test-user",
        dry_run=False,
        force=False,
        provision_command="test-provision-command",
        timeout=3_600,
        verbosity=2,
    )


@patch(
    "rib.utils.click_utils.get_run_command",
    MagicMock(return_value="test-provision-command"),
)
def test_provision_with_explicit_parameters(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env

    os.environ["HOST_USER"] = "test-user"

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.provision,
        [
            "--name=test-aws-env",
            "--timeout=750",
            "--force",
            "--dry-run",
            "--ansible-verbosity=3",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    rib_aws_env.provision.assert_called_with(
        current_username="test-user",
        dry_run=True,
        force=True,
        provision_command="test-provision-command",
        timeout=750,
        verbosity=3,
    )


###
# remove
###


def test_remove_raises_when_source_env_does_not_exist(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = False

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.remove, ["--name=test-aws-env"])
    assert result.exit_code == 0
    assert "No AWS Environment exists: test-aws-env" in result.output


def test_remove_compatible_env(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = True
    rib_aws_env.load_aws_env.return_value = rib_aws_env

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.remove, ["--name=test-aws-env"])
    assert result.exit_code == 0
    rib_aws_env.remove.assert_called_once()


@patch("click.confirm", MagicMock(return_value=False))
def test_remove_aborts_when_legacy_env_removal_rejected(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = True
    rib_aws_env.load_aws_env.return_value = None

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.remove, ["--name=test-aws-env"])
    assert result.exit_code == 0
    rib_aws_env.remove.assert_not_called()
    rib_aws_env.remove_legacy_aws_env.assert_not_called()


@patch("click.confirm", MagicMock(return_value=True))
def test_remove_legacy_env_when_confirmed(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = True
    rib_aws_env.load_aws_env.return_value = None

    runner = CliRunner()
    result = runner.invoke(env_aws_commands.remove, ["--name=test-aws-env"])
    assert result.exit_code == 0
    rib_aws_env.remove.assert_not_called()
    rib_aws_env.remove_legacy_aws_env.assert_called_with("test-aws-env")


###
# rename
###


def test_rename_raises_when_dest_env_already_exists(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.rename, ["--from=old-aws-env", "--to=new-aws-env"]
    )
    assert result.exit_code != 0
    assert isinstance(result.exception, error_utils.RIB707)


def test_rename(rib_aws_env):
    rib_aws_env.aws_env_exists.return_value = False
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.rename, ["--from=old-aws-env", "--to=new-aws-env"]
    )
    assert result.exit_code == 0
    rib_aws_env.rename.assert_called_with("new-aws-env")


###
# runtime-info
###


def test_runtime_info_with_default_yaml_format(rib_aws_env):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.get_runtime_info.return_value = {"key": "value"}

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.runtime_info,
        [
            "--name=test-aws-env",
        ],
    )
    assert result.exit_code == 0
    assert yaml.safe_load(result.output) == {"key": "value"}


def test_runtime_info_with_json_format(rib_aws_env):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.get_runtime_info.return_value = {"key": "value"}

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.runtime_info,
        [
            "--name=test-aws-env",
            "--format=json",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.output) == {"key": "value"}


###
# status
###


def test_status_with_yaml_format(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.get_status_report.return_value = AwsEnvStatus(
        status=AwsComponentStatus.NOT_READY,
        components={
            "cloud_formation": StatusReport(status=AwsComponentStatus.READY),
            "ec2_instance": StatusReport(status=AwsComponentStatus.NOT_PRESENT),
            "efs": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.status,
        [
            "--name=test-aws-env",
            "--format=yaml",
            "-dd",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    assert yaml.safe_load(result.output) == {
        "cloud_formation": {"status": "ready"},
        "ec2_instance": {"status": "not present"},
        "efs": {"status": "not ready"},
    }


def test_status_with_json_format(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.get_status_report.return_value = AwsEnvStatus(
        status=AwsComponentStatus.NOT_READY,
        components={
            "cloud_formation": StatusReport(status=AwsComponentStatus.READY),
            "ec2_instance": StatusReport(status=AwsComponentStatus.NOT_PRESENT),
            "efs": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.status,
        [
            "--name=test-aws-env",
            "--format=json",
            "-dd",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "cloud_formation": {"status": "ready"},
        "ec2_instance": {"status": "not present"},
        "efs": {"status": "not ready"},
    }


def test_status_with_no_details(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.get_status_report.return_value = AwsEnvStatus(
        status=AwsComponentStatus.NOT_READY,
        components={
            "cloud_formation": StatusReport(status=AwsComponentStatus.READY),
            "ec2_instance": StatusReport(status=AwsComponentStatus.NOT_PRESENT),
            "efs": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.status,
        [
            "--name=test-aws-env",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    assert "AWS Environment test-aws-env is not ready" in result.output
    assert "cloud" not in result.output
    assert "ec2" not in result.output
    assert "efs" not in result.output


def test_status_with_details(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env
    rib_aws_env.get_status_report.return_value = AwsEnvStatus(
        status=AwsComponentStatus.NOT_READY,
        components={
            "cloud_formation": StatusReport(status=AwsComponentStatus.READY),
            "ec2_instance": StatusReport(status=AwsComponentStatus.NOT_PRESENT),
            "efs": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.status,
        [
            "--name=test-aws-env",
            "-dd",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    assert "AWS Environment test-aws-env is not ready" in result.output
    assert "cloud formation: ready" in result.output
    assert "ec2 instance: not present" in result.output
    assert "efs: not ready" in result.output


###
# unprovision
###


@patch(
    "rib.utils.click_utils.get_run_command",
    MagicMock(return_value="test-unprovision-command"),
)
def test_unprovision_with_default_parameters(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.unprovision,
        [
            "--name=test-aws-env",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    rib_aws_env.unprovision.assert_called_with(
        dry_run=False,
        force=False,
        timeout=600,
        unprovision_command="test-unprovision-command",
        verbosity=2,
    )


@patch(
    "rib.utils.click_utils.get_run_command",
    MagicMock(return_value="test-unprovision-command"),
)
def test_unprovision_with_explicit_parameters(rib_aws_env, rib_state):
    rib_aws_env.get_aws_env_or_fail.return_value = rib_aws_env

    runner = CliRunner()
    result = runner.invoke(
        env_aws_commands.unprovision,
        [
            "--name=test-aws-env",
            "--timeout=750",
            "--force",
            "--dry-run",
            "--ansible-verbosity=3",
        ],
        obj=rib_state,
    )
    assert result.exit_code == 0
    rib_aws_env.unprovision.assert_called_with(
        dry_run=True,
        force=True,
        timeout=750,
        unprovision_command="test-unprovision-command",
        verbosity=3,
    )

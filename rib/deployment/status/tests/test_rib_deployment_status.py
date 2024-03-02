#!/usr/bin/env python3

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
        Test File for rib_deployment_status.py
"""

# Python Library Imports
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

# Local Library Imports
from rib.deployment.status.rib_local_deployment_status import RibLocalDeploymentStatus
from rib.deployment.status.rib_deployment_status import Require
from rib.utils import error_utils, status_utils
from rib.utils.status_utils import StatusReport

###
# Mocks
###


@pytest.fixture
def deployment():
    deployment = MagicMock()
    deployment.config["name"] = "test-deployment"
    return deployment


@pytest.fixture
def status(deployment):
    status = RibLocalDeploymentStatus(deployment)
    status._orig_verify_deployment_is_active = status.verify_deployment_is_active
    return status


###
# Tests
###

################################################################################
# verify_deployment_is_down
################################################################################


def test_verify_deployment_is_down_with_force(status):
    status.verify_deployment_is_down(action="test", force=True)


def test_verify_deployment_is_down_raises_when_not_down(status):
    status.is_down = MagicMock(return_value=False)
    with pytest.raises(error_utils.RIB341):
        status.verify_deployment_is_down(action="test")


def test_verify_deployment_is_down_passes_when_down(status):
    status.is_down = MagicMock(return_value=True)
    status.verify_deployment_is_down(action="test")


################################################################################
# verify_deployment_is_active
################################################################################


def test_verify_deployment_is_active_when_none_active(status):
    # restore original, un-mocked function
    status.verify_deployment_is_active = status._orig_verify_deployment_is_active
    status.get_active = MagicMock(return_value=None)
    with pytest.raises(error_utils.RIB343):
        status.verify_deployment_is_active("test")


def test_verify_deployment_is_active_when_none_active_and_none_ok(status):
    status.deployment.config = {"name": "test-deployment"}
    # restore original, un-mocked function
    status.verify_deployment_is_active = status._orig_verify_deployment_is_active
    status.deployment.get_active = MagicMock(return_value=None)
    status.verify_deployment_is_active("test", none_ok=True)


def test_verify_deployment_is_active_when_other_is_active(status):
    status.deployment.config = {"name": "test-deployment"}
    # restore original, un-mocked function
    status.verify_deployment_is_active = status._orig_verify_deployment_is_active
    status.deployment.get_active = MagicMock(return_value="other_deployment")
    with pytest.raises(error_utils.RIB343):
        status.verify_deployment_is_active("test")


def test_verify_deployment_is_active_when_deployment_is_active(status):
    status.deployment.config = {"name": "test-deployment"}
    # restore original, un-mocked function
    status.verify_deployment_is_active = status._orig_verify_deployment_is_active
    status.deployment.get_active = MagicMock(return_value="test-deployment")
    status.verify_deployment_is_active("test")


################################################################################
# get_containers_that_match_status
################################################################################


def test_get_containers_that_match_status_with_force(status):
    assert status.get_containers_that_match_status(
        action="test",
        names=["race-client-00001", "race-server-00003"],
        container_status=[status_utils.ContainerStatus.RUNNING],
        force=True,
    ) == {"race-client-00001", "race-server-00003"}


def test_get_containers_that_match_status_no_matches(status):
    status.get_container_status_report = MagicMock(
        return_value={
            "children": {
                "race-client-00001": {
                    "status": status_utils.ContainerStatus.NOT_PRESENT
                }
            },
        }
    )
    with pytest.raises(error_utils.RIB331):
        status.get_containers_that_match_status(
            action="test",
            names=["race-client-00001", "race-server-00003"],
            container_status=[status_utils.ContainerStatus.RUNNING],
        )


def test_get_containers_that_match_status_no_matches_none_required(status):
    status.get_container_status_report = MagicMock(
        return_value={
            "children": {
                "race-client-00001": {
                    "status": status_utils.ContainerStatus.NOT_PRESENT
                }
            },
        }
    )
    assert (
        status.get_containers_that_match_status(
            action="test",
            names=["race-client-00001", "race-server-00003"],
            container_status=[status_utils.ContainerStatus.RUNNING],
            require=Require.NONE,
        )
        == set()
    )


def test_get_containers_that_match_status_partial_match(status):
    status.get_container_status_report = MagicMock(
        return_value={
            "children": {
                "race-client-00001": {"status": status_utils.ContainerStatus.RUNNING},
                "race-server-00003": {"status": status_utils.ContainerStatus.UNHEALTHY},
            },
        }
    )
    assert status.get_containers_that_match_status(
        action="test",
        names=["race-client-00001", "race-server-00003"],
        container_status=[status_utils.ContainerStatus.RUNNING],
        quiet=True,
    ) == {"race-client-00001"}


def test_get_containers_that_match_status_partial_match_all_required(status):
    status.get_container_status_report = MagicMock(
        return_value={
            "children": {
                "race-client-00001": {"status": status_utils.ContainerStatus.RUNNING},
                "race-server-00003": {"status": status_utils.ContainerStatus.UNHEALTHY},
            },
        }
    )
    with pytest.raises(error_utils.RIB342):
        status.get_containers_that_match_status(
            action="test",
            names=["race-client-00001", "race-server-00003"],
            container_status=[status_utils.ContainerStatus.RUNNING],
            require=Require.ALL,
        )


def test_get_containers_that_match_status_all_match(status):
    status.get_container_status_report = MagicMock(
        return_value={
            "children": {
                "race-client-00001": {"status": status_utils.ContainerStatus.RUNNING},
                "race-server-00003": {"status": status_utils.ContainerStatus.RUNNING},
            },
        }
    )
    assert status.get_containers_that_match_status(
        action="test",
        names=["race-client-00001", "race-server-00003"],
        container_status=[status_utils.ContainerStatus.RUNNING],
    ) == {"race-client-00001", "race-server-00003"}
    assert status.get_containers_that_match_status(
        action="test",
        names=["race-client-00001", "race-server-00003"],
        container_status=[status_utils.ContainerStatus.RUNNING],
        quiet=True,
        require=Require.ALL,
    ) == {"race-client-00001", "race-server-00003"}


################################################################################
# wait_for_containers_to_match_status
################################################################################


@patch("rib.deployment.status.rib_deployment_status.datetime")
@patch("time.sleep")
@patch("click.echo", MagicMock())
def test_wait_for_containers_to_match_status_waits_until_all_match_criteria(
    mock_sleep, mock_datetime, status
):
    status.get_containers_that_match_status = MagicMock(
        side_effect=[
            set(),
            {"race-client-00001"},
            {"race-client-00001", "race-server-00003"},
        ]
    )
    mock_datetime.now.side_effect = [
        datetime(2022, 2, 2, 10, 0, 0),  # Start time
        datetime(2022, 2, 2, 10, 0, 0),  # Time after first check
        datetime(2022, 2, 2, 10, 0, 1),  # Time after second check
    ]

    status.wait_for_containers_to_match_status(
        action="test",
        names=["race-client-00001", "race-server-00003"],
        container_status=[status_utils.ContainerStatus.RUNNING],
    )

    assert status.get_containers_that_match_status.call_count == 3
    assert mock_sleep.call_count == 2


@patch("rib.deployment.status.rib_deployment_status.datetime")
@patch("time.sleep")
@patch("click.echo", MagicMock())
def test_wait_for_containers_to_match_status_raises_when_timeout_occurs(
    mock_sleep, mock_datetime, status
):
    status.get_containers_that_match_status = MagicMock(
        return_value={"race-client-00001"}
    )
    mock_datetime.now.side_effect = [
        datetime(2022, 2, 2, 10, 0, 0),  # Start time
        datetime(2022, 2, 2, 10, 0, 0),  # Time after first check
        datetime(2022, 2, 2, 10, 0, 1),  # Time after second check
        datetime(2022, 2, 2, 10, 0, 29),  # Time after "30th" check
        datetime(2022, 2, 2, 10, 0, 30),  # Time after "31st" check
        datetime(2022, 2, 2, 10, 0, 59),  # Time after "60th" check
        datetime(2022, 2, 2, 10, 1, 0),  # Time after "61st" check
        datetime(2022, 2, 2, 10, 1, 1),  # Time after "62nd" check (timeout occurs)
        datetime(2022, 2, 2, 10, 1, 2),  # Time after "63rd" check
    ]

    with pytest.raises(error_utils.RIB332):
        status.wait_for_containers_to_match_status(
            action="test",
            names=["race-client-00001", "race-server-00003"],
            container_status=[status_utils.ContainerStatus.RUNNING],
            timeout=60,
        )

    assert status.get_containers_that_match_status.call_count == 7
    assert mock_sleep.call_count == 6


################################################################################
# get_nodes_that_match_status
################################################################################


def test_get_nodes_that_match_status_with_force(status):
    assert status.get_nodes_that_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
        app_status=[status_utils.AppStatus.RUNNING],
        force=True,
    ) == {"race-client-00001", "race-server-00003"}


def test_get_nodes_that_match_status_no_matches(status):
    status._get_node_status_report = MagicMock(
        return_value={
            "status": status_utils.NodeStatus.READY_TO_START,
            "children": {
                "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                "app": {"status": status_utils.AppStatus.NOT_RUNNING},
                "race": {"status": status_utils.RaceStatus.NOT_REPORTING},
            },
        }
    )
    with pytest.raises(error_utils.RIB331):
        status.get_nodes_that_match_status(
            action="test",
            personas=["race-client-00001", "race-server-00003"],
            app_status=[status_utils.AppStatus.RUNNING],
        )


def test_get_nodes_that_match_status_no_matches_none_required(status):
    status._get_node_status_report = MagicMock(
        return_value={
            "status": status_utils.NodeStatus.READY_TO_START,
            "children": {
                "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                "app": {"status": status_utils.AppStatus.NOT_RUNNING},
                "race": {"status": status_utils.AppStatus.NOT_REPORTING},
            },
        }
    )
    assert (
        status.get_nodes_that_match_status(
            action="test",
            personas=["race-client-00001", "race-server-00003"],
            app_status=[status_utils.AppStatus.RUNNING],
            require=Require.NONE,
        )
        == set()
    )


def test_get_nodes_that_match_status_partial_match(status):
    status._get_node_status_report = MagicMock(
        side_effect=[
            {
                "status": status_utils.NodeStatus.READY_TO_START,
                "children": {
                    "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                    "app": {"status": status_utils.AppStatus.NOT_RUNNING},
                    "race": {"status": status_utils.RaceStatus.NOT_REPORTING},
                },
            },
            {
                "status": status_utils.NodeStatus.RUNNING,
                "children": {
                    "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                    "app": {"status": status_utils.AppStatus.RUNNING},
                    "race": {"status": status_utils.RaceStatus.RUNNING},
                },
            },
        ]
    )
    assert status.get_nodes_that_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
        app_status=[status_utils.AppStatus.RUNNING],
        quiet=True,
    ) == {"race-server-00003"}


def test_get_nodes_that_match_status_partial_match_all_required(status):
    status._get_node_status_report = MagicMock(
        side_effect=[
            {
                "status": status_utils.NodeStatus.READY_TO_START,
                "children": {
                    "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                    "app": {"status": status_utils.AppStatus.NOT_RUNNING},
                    "race": {"status": status_utils.RaceStatus.NOT_REPORTING},
                },
            },
            {
                "status": status_utils.NodeStatus.RUNNING,
                "children": {
                    "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                    "app": {"status": status_utils.AppStatus.RUNNING},
                    "race": {"status": status_utils.RaceStatus.NOT_REPORTING},
                },
            },
        ]
    )
    with pytest.raises(error_utils.RIB342):
        status.get_nodes_that_match_status(
            action="test",
            personas=["race-client-00001", "race-server-00003"],
            app_status=[status_utils.AppStatus.RUNNING],
            require=Require.ALL,
        )


def test_get_nodes_that_match_status_all_match(status):
    status._get_node_status_report = MagicMock(
        return_value={
            "status": status_utils.NodeStatus.RUNNING,
            "children": {
                "daemon": {"status": status_utils.DaemonStatus.RUNNING},
                "app": {"status": status_utils.AppStatus.NOT_RUNNING},
            },
        }
    )
    assert status.get_nodes_that_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
        app_status=[status_utils.AppStatus.NOT_RUNNING],
    ) == {"race-client-00001", "race-server-00003"}
    assert status.get_nodes_that_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
        daemon_status=[status_utils.DaemonStatus.RUNNING],
    ) == {"race-client-00001", "race-server-00003"}
    assert status.get_nodes_that_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
    ) == {"race-client-00001", "race-server-00003"}
    assert status.get_nodes_that_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
        app_status=[status_utils.AppStatus.NOT_RUNNING],
        quiet=True,
        require=Require.ALL,
    ) == {"race-client-00001", "race-server-00003"}


def test_get_nodes_that_match_status_defaults_to_all_deployment_personas(
    status,
):
    status.deployment.all_personas = ["race-client-00002", "race-server-00002"]
    assert status.get_nodes_that_match_status(
        action="test",
        app_status=[status_utils.AppStatus.RUNNING],
        force=True,
    ) == {"race-client-00002", "race-server-00002"}


################################################################################
# wait_for_nodes_to_match_status
################################################################################


@patch("rib.deployment.status.rib_deployment_status.datetime")
@patch("time.sleep")
@patch("click.echo", MagicMock())
def test_wait_for_nodes_to_match_status_waits_until_all_match_criteria(
    mock_sleep, mock_datetime, status
):
    status.get_nodes_that_match_status = MagicMock(
        side_effect=[
            set(),
            {"race-client-00001"},
            {"race-client-00001", "race-server-00003"},
        ]
    )
    mock_datetime.now.side_effect = [
        datetime(2022, 2, 2, 10, 0, 0),  # Start time
        datetime(2022, 2, 2, 10, 0, 0),  # Time after first check
        datetime(2022, 2, 2, 10, 0, 1),  # Time after second check
    ]

    status.wait_for_nodes_to_match_status(
        action="test",
        personas=["race-client-00001", "race-server-00003"],
        app_status=[status_utils.AppStatus.RUNNING],
    )

    assert status.get_nodes_that_match_status.call_count == 3
    assert mock_sleep.call_count == 2


@patch("rib.deployment.status.rib_deployment_status.datetime")
@patch("time.sleep")
@patch("click.echo", MagicMock())
def test_wait_for_nodes_to_match_status_raises_when_timeout_occurs(
    mock_sleep, mock_datetime, status
):
    status.get_nodes_that_match_status = MagicMock(return_value={"race-client-00001"})
    mock_datetime.now.side_effect = [
        datetime(2022, 2, 2, 10, 0, 0),  # Start time
        datetime(2022, 2, 2, 10, 0, 0),  # Time after first check
        datetime(2022, 2, 2, 10, 0, 1),  # Time after second check
        datetime(2022, 2, 2, 10, 0, 29),  # Time after "30th" check
        datetime(2022, 2, 2, 10, 0, 30),  # Time after "31st" check
        datetime(2022, 2, 2, 10, 0, 59),  # Time after "60th" check
        datetime(2022, 2, 2, 10, 1, 0),  # Time after "61st" check
        datetime(2022, 2, 2, 10, 1, 1),  # Time after "62nd" check (timeout occurs)
        datetime(2022, 2, 2, 10, 1, 2),  # Time after "63rd" check
    ]

    with pytest.raises(error_utils.RIB332):
        status.wait_for_nodes_to_match_status(
            action="test",
            personas=["race-client-00001", "race-server-00003"],
            app_status=[status_utils.AppStatus.RUNNING],
            timeout=60,
        )

    assert status.get_nodes_that_match_status.call_count == 7
    assert mock_sleep.call_count == 6


################################################################################
# wait_for_services_to_match_status
################################################################################


@patch("rib.deployment.status.rib_deployment_status.datetime")
@patch("time.sleep")
@patch("click.echo", MagicMock())
def test_wait_for_services_to_match_waits_until_criteria_matches(
    mock_sleep, mock_datetime, status
):
    status.get_services_status_report = MagicMock(
        side_effect=[
            {"status": status_utils.ParentStatus.ALL_DOWN},
            {"status": status_utils.ParentStatus.SOME_RUNNING},
            {"status": status_utils.ParentStatus.ALL_RUNNING},
        ]
    )
    mock_datetime.now.side_effect = [
        datetime(2022, 2, 2, 10, 0, 0),  # Start time
        datetime(2022, 2, 2, 10, 0, 0),  # Time after first check
        datetime(2022, 2, 2, 10, 0, 1),  # Time after second check
    ]

    status.wait_for_services_to_match_status(
        action="test",
        parent_status=[status_utils.ParentStatus.ALL_RUNNING],
    )

    assert status.get_services_status_report.call_count == 3
    assert mock_sleep.call_count == 2


@patch("rib.deployment.status.rib_deployment_status.datetime")
@patch("time.sleep")
@patch("click.echo", MagicMock())
def test_wait_for_services_to_match_status_raises_when_timeout_occurs(
    mock_sleep, mock_datetime, status
):
    status.get_services_status_report = MagicMock(
        return_value={"status": status_utils.ParentStatus.SOME_RUNNING}
    )
    mock_datetime.now.side_effect = [
        datetime(2022, 2, 2, 10, 0, 0),  # Start time
        datetime(2022, 2, 2, 10, 0, 0),  # Time after first check
        datetime(2022, 2, 2, 10, 0, 1),  # Time after second check
        datetime(2022, 2, 2, 10, 0, 29),  # Time after "30th" check
        datetime(2022, 2, 2, 10, 0, 30),  # Time after "31st" check
        datetime(2022, 2, 2, 10, 0, 59),  # Time after "60th" check
        datetime(2022, 2, 2, 10, 1, 0),  # Time after "61st" check
        datetime(2022, 2, 2, 10, 1, 1),  # Time after "62nd" check (timeout occurs)
        datetime(2022, 2, 2, 10, 1, 2),  # Time after "63rd" check
    ]

    with pytest.raises(error_utils.RIB332):
        status.wait_for_services_to_match_status(
            action="test",
            parent_status=[status_utils.ParentStatus.ALL_RUNNING],
            timeout=60,
        )

    assert status.get_services_status_report.call_count == 7
    assert mock_sleep.call_count == 6


################################################################################
# get_services_status_report
################################################################################


def test_get_services_status_report(status):
    status._get_external_services_status_report = MagicMock(
        return_value={"status": status_utils.ParentStatus.SOME_RUNNING}
    )
    status._get_rib_services_status_report = MagicMock(
        return_value={"status": status_utils.ParentStatus.ALL_RUNNING}
    )

    assert status.get_services_status_report() == {
        "status": status_utils.ParentStatus.SOME_RUNNING,
        "children": {
            "External Services": {"status": status_utils.ParentStatus.SOME_RUNNING},
            "RiB": {"status": status_utils.ParentStatus.ALL_RUNNING},
        },
    }


###
# get_app_status_report
###


def test_get_app_status_report(status):
    status._get_node_status_report = MagicMock(
        side_effect=lambda persona: StatusReport(
            status=status_utils.NodeStatus.RUNNING
            if persona == "race-client-00001"
            else status_utils.NodeStatus.READY_TO_START
        )
    )
    status.deployment.all_personas = ["race-client-00001", "race-server-00001"]

    assert status.get_app_status_report() == StatusReport(
        status=status_utils.ParentStatus.MIXED,
        children={
            "race-client-00001": StatusReport(status=status_utils.NodeStatus.RUNNING),
            "race-server-00001": StatusReport(
                status=status_utils.NodeStatus.READY_TO_START
            ),
        },
    )


###
# _get_node_status_report
###


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_daemon_not_reporting(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={"is_alive": False}
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(return_value={})
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.UNKNOWN,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.NOT_REPORTING, reason=None
            ),
            "app": StatusReport(
                status=status_utils.AppStatus.NOT_REPORTING, reason=None
            ),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED, reason=None
            ),
            "etc": StatusReport(
                status=status_utils.EtcStatus.ETC_TAR_PUSHED, reason=None
            ),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_app_not_installed(status):
    # First call is to check etc files pushed, then config files.
    # Bootstrap nodes should not have configs pushed
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        side_effect=[True, False]
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": False,
            "configsPresent": False,
            "configsExtracted": False,
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(return_value={})
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.READY_TO_BOOTSTRAP,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(
                status=status_utils.AppStatus.NOT_INSTALLED, reason=None
            ),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.CONFIG_GEN_SUCCESS, reason=None
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_daemon_exception(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        side_effect=Exception("connection failed")
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={"is_alive": False}
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.ERROR,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.ERROR,
                reason="Unexpectedly unable to get daemon status",
            ),
            "app": StatusReport(
                status=status_utils.AppStatus.NOT_REPORTING, reason=None
            ),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED, reason=None
            ),
            "etc": StatusReport(
                status=status_utils.EtcStatus.ETC_TAR_PUSHED, reason=None
            ),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_configs_not_installed(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsPresent": False,
            "configsExtracted": False,
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={"is_alive": False}
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.UNKNOWN,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(status=status_utils.AppStatus.NOT_RUNNING, reason=None),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.CONFIGS_TAR_PUSHED, reason=None
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_configs_no_deployment(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsPresent": True,
            "configsExtracted": False,
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={"is_alive": False}
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.ERROR,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(status=status_utils.AppStatus.NOT_RUNNING, reason=None),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.ERROR,
                reason="No deployment associated with RACE configs",
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_configs_wrong_deployment(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsPresent": True,
            "configsExtracted": False,
            "deployment": "other-deployment",
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={"is_alive": False}
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.ERROR,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(
                status=status_utils.AppStatus.NOT_RUNNING,
                reason=None,
            ),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.ERROR,
                reason="Configs from wrong deployment present: other-deployment",
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_dns_unsuccessful(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsExtracted": True,
            "deployment": status.deployment.config["name"],
            "dnsSuccessful": False,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={
            "is_alive": True,
            "RaceStatus": {
                "validConfigs": True,
                "network-manager-status": "PLUGIN_READY",
            },
        }
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.ERROR,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.ERROR,
                reason="DNS lookups are failing on node",
            ),
            "app": StatusReport(status=status_utils.AppStatus.RUNNING, reason=None),
            "race": StatusReport(status=status_utils.RaceStatus.RUNNING, reason=None),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.EXTRACTED_CONFIGS, reason=None
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_app_not_running(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsPresent": True,
            "configsExtracted": False,
            "deployment": status.deployment.config["name"],
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={"is_alive": False}
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.READY_TO_START,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(status=status_utils.AppStatus.NOT_RUNNING, reason=None),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.DOWNLOADED_CONFIGS, reason=None
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
def test__get_node_status_report_app_running(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsPresent": False,
            "configsExtracted": True,
            "deployment": status.deployment.config["name"],
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        return_value={
            "is_alive": True,
            "RaceStatus": {
                "validConfigs": True,
                "network-manager-status": "PLUGIN_READY",
            },
        }
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.RUNNING,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(status=status_utils.AppStatus.RUNNING, reason=None),
            "race": StatusReport(status=status_utils.RaceStatus.RUNNING, reason=None),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.EXTRACTED_CONFIGS, reason=None
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.do_expected_node_artifacts_archives_exist",
    MagicMock(return_value=True),
)
@patch(
    "rib.deployment.status.rib_deployment_status.RibDeploymentStatus.did_config_gen_succeed",
    MagicMock(return_value=True),
)
@patch("rib.deployment.rib_deployment.RibDeployment.get_etc_tar_name", MagicMock())
@patch("rib.deployment.rib_deployment.RibDeployment.get_configs_tar_name", MagicMock())
@patch("os.path.isfile", MagicMock(return_value=True))
def test__get_node_status_report_app_exception(status):
    status.deployment.file_server_client.is_file_on_file_server = MagicMock(
        return_value=True
    )
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={
            "is_alive": True,
            "installed": True,
            "configsPresent": True,
            "deployment": status.deployment.config["name"],
            "dnsSuccessful": True,
            "jaegerConfigExists": True,
        }
    )
    status.deployment.race_node_interface.get_app_status = MagicMock(
        side_effect=Exception("connection failed")
    )
    assert status._get_node_status_report("race-client-00001") == StatusReport(
        status=status_utils.NodeStatus.ERROR,
        children={
            "artifacts": StatusReport(
                status=status_utils.ArtifactsStatus.ARTIFACT_TARS_EXIST, reason=None
            ),
            "daemon": StatusReport(
                status=status_utils.DaemonStatus.RUNNING, reason=None
            ),
            "app": StatusReport(
                status=status_utils.AppStatus.ERROR,
                reason="Unexpectedly unable to get app status",
            ),
            "race": StatusReport(
                status=status_utils.RaceStatus.NOT_REPORTING, reason=None
            ),
            "configs": StatusReport(
                status=status_utils.ConfigsStatus.DOWNLOADED_CONFIGS, reason=None
            ),
            "etc": StatusReport(status=status_utils.EtcStatus.READY, reason=None),
        },
    )


def test__get_node_os_details_returns_values(status):
    status.deployment.race_node_interface.get_daemon_status = MagicMock(
        return_value={"nodePlatform": "linux", "nodeArchitecture": "x86"}
    )
    (nodePlatform, nodeArch) = status.get_node_os_details("race-client-00001")
    assert nodePlatform == "linux"
    assert nodeArch == "x86"

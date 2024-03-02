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
    Tests for status_utils.py
"""

# Python Library Imports
import pytest

# Local Library Imports
from rib.utils import status_utils
from rib.utils.status_utils import (
    AppStatus,
    ArtifactsStatus,
    ContainerStatus,
    ConfigsStatus,
    DaemonStatus,
    EtcStatus,
    NodeStatus,
    ParentStatus,
    RaceStatus,
    ServiceStatus,
)


###
# evaluate_container_status
###


@pytest.mark.parametrize(
    "container_state,container_status,expected_status",
    [
        ("not running", "", ContainerStatus.EXITED),
        ("running", "starting", ContainerStatus.STARTING),
        ("running", "Up 2 minutes (unhealthy)", ContainerStatus.UNHEALTHY),
        ("running", "Up 2 minutes (healthy)", ContainerStatus.RUNNING),
        ("running", "Up 2 minutes", ContainerStatus.RUNNING),
        ("running", "unexpected status", ContainerStatus.UNKNOWN),
    ],
)
def test_evaluate_container_status(container_state, container_status, expected_status):
    assert expected_status == status_utils.evaluate_container_status(
        container_state, container_status
    )


###
# evaluate_node_status
###


@pytest.mark.parametrize(
    "artifacts_status,daemon_status,app_status,race_status,configs_status,etc_status,expected_status",
    [
        # fmt: off
        # READY TO GENERATE CONFIGS
        (ArtifactsStatus.ARTIFACTS_EXIST, DaemonStatus.NOT_REPORTING, AppStatus.NOT_REPORTING, RaceStatus.NOT_REPORTING, ConfigsStatus.ERROR_CONFIG_GEN_FAILED, EtcStatus.ERROR_CONFIG_GEN_FAILED, NodeStatus.READY_TO_GENERATE_CONFIG),
        # READY TO TAR
        (ArtifactsStatus.ARTIFACTS_EXIST, DaemonStatus.NOT_REPORTING, AppStatus.NOT_REPORTING, RaceStatus.NOT_REPORTING, ConfigsStatus.CONFIG_GEN_SUCCESS, EtcStatus.CONFIG_GEN_SUCCESS, NodeStatus.READY_TO_TAR_CONFIGS),
        # DOWN
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.NOT_REPORTING, AppStatus.NOT_REPORTING, RaceStatus.NOT_REPORTING, ConfigsStatus.CONFIGS_TAR_EXISTS, EtcStatus.ETC_TAR_EXISTS, NodeStatus.DOWN),
        # READY TO PUBLISH
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.NOT_REPORTING, RaceStatus.NOT_REPORTING, ConfigsStatus.CONFIGS_TAR_EXISTS, EtcStatus.ETC_TAR_EXISTS, NodeStatus.READY_TO_PUBLISH_CONFIGS),
        # READY TO INSTALL
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.NOT_REPORTING, RaceStatus.NOT_REPORTING, ConfigsStatus.CONFIGS_TAR_PUSHED, EtcStatus.ETC_TAR_PUSHED, NodeStatus.READY_TO_INSTALL_CONFIGS),
        # UP - GENESIS
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.NOT_RUNNING, RaceStatus.NOT_REPORTING, ConfigsStatus.DOWNLOADED_CONFIGS, EtcStatus.READY, NodeStatus.READY_TO_START),
        # UP - BOOTSTRAP
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.NOT_INSTALLED, RaceStatus.NOT_REPORTING, ConfigsStatus.UNKNOWN, EtcStatus.READY, NodeStatus.READY_TO_BOOTSTRAP),
        # INITIALIZING
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.RUNNING, RaceStatus.NETWORK_MANAGER_NOT_READY, ConfigsStatus.EXTRACTED_CONFIGS, EtcStatus.READY, NodeStatus.INITIALIZING),
        # RUNNING
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.RUNNING, RaceStatus.RUNNING, ConfigsStatus.EXTRACTED_CONFIGS, EtcStatus.READY, NodeStatus.RUNNING),
        # STOPPED
        (ArtifactsStatus.ARTIFACT_TARS_EXIST, DaemonStatus.RUNNING, AppStatus.NOT_RUNNING, RaceStatus.NOT_REPORTING, ConfigsStatus.EXTRACTED_CONFIGS, EtcStatus.READY, NodeStatus.STOPPED),
        # fmt: on
    ],
)
def test_evaluate_node_status(
    artifacts_status,
    daemon_status,
    app_status,
    race_status,
    configs_status,
    etc_status,
    expected_status,
):
    assert expected_status == status_utils.evaluate_node_status(
        daemon_status,
        app_status,
        race_status,
        configs_status,
        etc_status,
        artifacts_status,
    )


###
# evaluate_node_parent_status
###


@pytest.mark.parametrize(
    "children,expected_status",
    [
        # fmt: off

        # Statuses where one node determine's parent status
        ([NodeStatus.ERROR, NodeStatus.DOWN], ParentStatus.ERROR),
        ([NodeStatus.UNKNOWN, NodeStatus.RUNNING], ParentStatus.UNKNOWN),
        # Uknown is higher priority than Error
        ([NodeStatus.UNKNOWN, NodeStatus.ERROR], ParentStatus.UNKNOWN),
        # Bootstrap
        ([NodeStatus.READY_TO_BOOTSTRAP, NodeStatus.READY_TO_START], ParentStatus.READY_TO_START),
        ([NodeStatus.READY_TO_START, NodeStatus.READY_TO_BOOTSTRAP], ParentStatus.READY_TO_START),
        ([NodeStatus.READY_TO_BOOTSTRAP, NodeStatus.RUNNING], ParentStatus.READY_TO_BOOTSTRAP),
        ([NodeStatus.RUNNING, NodeStatus.READY_TO_BOOTSTRAP], ParentStatus.READY_TO_BOOTSTRAP),
        # Mixed
        ([NodeStatus.RUNNING, NodeStatus.READY_TO_START], ParentStatus.MIXED),
        # All Others
        ([NodeStatus.READY_TO_GENERATE_CONFIG, NodeStatus.READY_TO_GENERATE_CONFIG], ParentStatus.READY_TO_GENERATE_CONFIG),
        ([NodeStatus.READY_TO_TAR_CONFIGS, NodeStatus.READY_TO_TAR_CONFIGS], ParentStatus.READY_TO_TAR_CONFIGS),
        ([], ParentStatus.ALL_DOWN),
        ([NodeStatus.DOWN, NodeStatus.DOWN], ParentStatus.ALL_DOWN),
        ([NodeStatus.READY_TO_PUBLISH_CONFIGS, NodeStatus.READY_TO_PUBLISH_CONFIGS], ParentStatus.READY_TO_PUBLISH_CONFIGS),
        ([NodeStatus.READY_TO_INSTALL_CONFIGS, NodeStatus.READY_TO_INSTALL_CONFIGS], ParentStatus.READY_TO_INSTALL_CONFIGS),
        ([NodeStatus.READY_TO_START, NodeStatus.READY_TO_START], ParentStatus.READY_TO_START),
        ([NodeStatus.INITIALIZING, NodeStatus.INITIALIZING], ParentStatus.INITIALIZING),
        ([NodeStatus.READY_TO_BOOTSTRAP, NodeStatus.READY_TO_BOOTSTRAP], ParentStatus.READY_TO_BOOTSTRAP),
        ([NodeStatus.RUNNING, NodeStatus.RUNNING], ParentStatus.ALL_RUNNING),
        ([NodeStatus.STOPPED, NodeStatus.STOPPED], ParentStatus.ALL_STOPPED),
        # fmt: on
    ],
)
def test_evaluate_node_parent_status(children, expected_status):
    assert expected_status == status_utils.evaluate_node_parent_status(children)


###
# evaluate_container_parent_status
###


@pytest.mark.parametrize(
    "children,expected_status",
    [
        # fmt: off
        ([], ParentStatus.ALL_DOWN),
        ([ContainerStatus.NOT_PRESENT, ContainerStatus.NOT_PRESENT], ParentStatus.ALL_DOWN),
        ([ContainerStatus.NOT_PRESENT, ContainerStatus.EXITED], ParentStatus.ALL_DOWN),
        ([ContainerStatus.NOT_PRESENT, ContainerStatus.STARTING], ParentStatus.SOME_RUNNING),
        ([ContainerStatus.NOT_PRESENT, ContainerStatus.RUNNING], ParentStatus.SOME_RUNNING),
        ([ContainerStatus.NOT_PRESENT, ContainerStatus.UNHEALTHY], ParentStatus.ERROR),
        ([ContainerStatus.NOT_PRESENT, ContainerStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ContainerStatus.EXITED, ContainerStatus.EXITED], ParentStatus.ALL_DOWN),
        ([ContainerStatus.EXITED, ContainerStatus.STARTING], ParentStatus.SOME_RUNNING),
        ([ContainerStatus.EXITED, ContainerStatus.RUNNING], ParentStatus.SOME_RUNNING),
        ([ContainerStatus.EXITED, ContainerStatus.UNHEALTHY], ParentStatus.ERROR),
        ([ContainerStatus.EXITED, ContainerStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ContainerStatus.STARTING, ContainerStatus.STARTING], ParentStatus.ALL_RUNNING),
        ([ContainerStatus.STARTING, ContainerStatus.RUNNING], ParentStatus.ALL_RUNNING),
        ([ContainerStatus.STARTING, ContainerStatus.UNHEALTHY], ParentStatus.ERROR),
        ([ContainerStatus.STARTING, ContainerStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ContainerStatus.RUNNING, ContainerStatus.RUNNING], ParentStatus.ALL_RUNNING),
        ([ContainerStatus.RUNNING, ContainerStatus.UNHEALTHY], ParentStatus.ERROR),
        ([ContainerStatus.RUNNING, ContainerStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ContainerStatus.UNHEALTHY, ContainerStatus.UNHEALTHY], ParentStatus.ERROR),
        ([ContainerStatus.UNHEALTHY, ContainerStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ContainerStatus.UNKNOWN, ContainerStatus.UNKNOWN], ParentStatus.UNKNOWN),
        # fmt: on
    ],
)
def test_evaluate_container_parent_status(children, expected_status):
    assert expected_status == status_utils.evaluate_container_parent_status(children)


###
# evaluate_service_parent_status
###


@pytest.mark.parametrize(
    "children,expected_status",
    [
        # fmt: off
        ([], ParentStatus.ALL_DOWN),
        ([ServiceStatus.NOT_RUNNING, ServiceStatus.NOT_RUNNING], ParentStatus.ALL_DOWN),
        ([ServiceStatus.NOT_RUNNING, ServiceStatus.RUNNING], ParentStatus.SOME_RUNNING),
        ([ServiceStatus.NOT_RUNNING, ServiceStatus.ERROR], ParentStatus.ERROR),
        ([ServiceStatus.NOT_RUNNING, ServiceStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ServiceStatus.RUNNING, ServiceStatus.RUNNING], ParentStatus.ALL_RUNNING),
        ([ServiceStatus.RUNNING, ServiceStatus.ERROR], ParentStatus.ERROR),
        ([ServiceStatus.RUNNING, ServiceStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ServiceStatus.ERROR, ServiceStatus.ERROR], ParentStatus.ERROR),
        ([ServiceStatus.ERROR, ServiceStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ServiceStatus.UNKNOWN, ServiceStatus.UNKNOWN], ParentStatus.UNKNOWN),
        # fmt: on
    ],
)
def test_evaluate_service_parent_status(children, expected_status):
    assert expected_status == status_utils.evaluate_service_parent_status(children)


###
# evaluate_grandparent_status
###


@pytest.mark.parametrize(
    "children,expected_status",
    [
        # fmt: off
        ([], ParentStatus.ALL_DOWN),
        ([ParentStatus.ALL_DOWN, ParentStatus.ALL_DOWN], ParentStatus.ALL_DOWN),
        ([ParentStatus.ALL_DOWN, ParentStatus.READY_TO_START], ParentStatus.MIXED),
        ([ParentStatus.ALL_DOWN, ParentStatus.ERROR], ParentStatus.ERROR),
        ([ParentStatus.ALL_DOWN, ParentStatus.UNKNOWN], ParentStatus.UNKNOWN),
        ([ParentStatus.READY_TO_GENERATE_CONFIG, ParentStatus.READY_TO_GENERATE_CONFIG], ParentStatus.READY_TO_GENERATE_CONFIG),
        ([ParentStatus.READY_TO_TAR_CONFIGS, ParentStatus.READY_TO_TAR_CONFIGS], ParentStatus.READY_TO_TAR_CONFIGS),
        ([ParentStatus.READY_TO_PUBLISH_CONFIGS, ParentStatus.READY_TO_PUBLISH_CONFIGS], ParentStatus.READY_TO_PUBLISH_CONFIGS),
        ([ParentStatus.READY_TO_INSTALL_CONFIGS, ParentStatus.READY_TO_INSTALL_CONFIGS], ParentStatus.READY_TO_INSTALL_CONFIGS),
        ([ParentStatus.READY_TO_START, ParentStatus.READY_TO_START], ParentStatus.READY_TO_START),
        ([ParentStatus.INITIALIZING, ParentStatus.INITIALIZING], ParentStatus.INITIALIZING),
        ([ParentStatus.READY_TO_BOOTSTRAP, ParentStatus.READY_TO_BOOTSTRAP], ParentStatus.READY_TO_BOOTSTRAP),
        ([ParentStatus.ALL_RUNNING, ParentStatus.ALL_RUNNING], ParentStatus.ALL_RUNNING),
        ([ParentStatus.ALL_STOPPED, ParentStatus.ALL_STOPPED], ParentStatus.ALL_STOPPED),
        # fmt: on
    ],
)
def test_evaluate_grandparent_status(children, expected_status):
    assert expected_status == status_utils.evaluate_grandparent_status(children)

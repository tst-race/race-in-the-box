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
    Tests for rib_deployment_rpc.py
"""

# Python Library Imports
import pytest
from unittest.mock import MagicMock, call, create_autospec

# Local Library Imports
from rib.deployment.rib_deployment_rpc import RibDeploymentRpc
from rib.utils import error_utils
from rib.utils.race_node_utils import RaceNodeInterface


###
# Mocks
###


@pytest.fixture
def deployment():
    deployment.status = MagicMock()
    deployment.status.verify_deployment_is_active = MagicMock()
    deployment.status.get_nodes_that_match_status = MagicMock(
        side_effect=lambda **kwargs: (
            kwargs.get("personas") or ["implicit-node-1", "implicit-node-2"]
        )
    )
    deployment.race_node_interface = create_autospec(RaceNodeInterface)
    return deployment


@pytest.fixture
def rpc(deployment):
    return RibDeploymentRpc(deployment)


###
# Tests
###

################################################################################
# deactivate_channel
################################################################################


def test_deactivate_channel_implicit_nodes(rpc):
    rpc.deactivate_channel(channel_gid="test-channel")
    rpc.deployment.race_node_interface.rpc_deactivate_channel.assert_has_calls(
        [
            call(channel_gid="test-channel", persona="implicit-node-1"),
            call(channel_gid="test-channel", persona="implicit-node-2"),
        ]
    )


def test_deactivate_channel_explicit_nodes(rpc):
    rpc.deactivate_channel(channel_gid="test-channel", nodes=["explicit-node-1"])
    rpc.deployment.race_node_interface.rpc_deactivate_channel.assert_has_calls(
        [
            call(channel_gid="test-channel", persona="explicit-node-1"),
        ]
    )


def test_deactivate_channel_error(rpc):
    rpc.deployment.race_node_interface.rpc_deactivate_channel.side_effect = Exception
    with pytest.raises(error_utils.RIB412):
        rpc.deactivate_channel(channel_gid="test-channel")
    assert rpc.deployment.race_node_interface.rpc_deactivate_channel.call_count == 2


################################################################################
# destroy_link
################################################################################


def test_destroy_link_implicit_nodes(rpc):
    rpc.destroy_link(link_id="test-link")
    rpc.deployment.race_node_interface.rpc_destroy_link.assert_has_calls(
        [
            call(link_id="test-link", persona="implicit-node-1"),
            call(link_id="test-link", persona="implicit-node-2"),
        ]
    )


def test_destroy_link_explicit_nodes(rpc):
    rpc.destroy_link(link_id="test-link", nodes=["explicit-node-1"])
    rpc.deployment.race_node_interface.rpc_destroy_link.assert_has_calls(
        [
            call(link_id="test-link", persona="explicit-node-1"),
        ]
    )


def test_destroy_link_error(rpc):
    rpc.deployment.race_node_interface.rpc_destroy_link.side_effect = Exception
    with pytest.raises(error_utils.RIB412):
        rpc.destroy_link(link_id="test-link")
    assert rpc.deployment.race_node_interface.rpc_destroy_link.call_count == 2


################################################################################
# close_connection
################################################################################


def test_close_connection_implicit_nodes(rpc):
    rpc.close_connection(connection_id="test-connection")
    rpc.deployment.race_node_interface.rpc_close_connection.assert_has_calls(
        [
            call(connection_id="test-connection", persona="implicit-node-1"),
            call(connection_id="test-connection", persona="implicit-node-2"),
        ]
    )


def test_close_connection_explicit_nodes(rpc):
    rpc.close_connection(connection_id="test-connection", nodes=["explicit-node-1"])
    rpc.deployment.race_node_interface.rpc_close_connection.assert_has_calls(
        [
            call(connection_id="test-connection", persona="explicit-node-1"),
        ]
    )


def test_close_connection_error(rpc):
    rpc.deployment.race_node_interface.rpc_close_connection.side_effect = Exception
    with pytest.raises(error_utils.RIB412):
        rpc.close_connection(connection_id="test-connection")
    assert rpc.deployment.race_node_interface.rpc_close_connection.call_count == 2


################################################################################
# notify_epoch
################################################################################


def test_notify_epoch_implicit_nodes(rpc):
    rpc.notify_epoch(data="{}")
    rpc.deployment.race_node_interface.rpc_notify_epoch.assert_has_calls(
        [
            call(data="{}", persona="implicit-node-1"),
            call(data="{}", persona="implicit-node-2"),
        ]
    )


def test_notify_epoch_explicit_nodes(rpc):
    rpc.notify_epoch(data="{}", nodes=["explicit-node-1"])
    rpc.deployment.race_node_interface.rpc_notify_epoch.assert_has_calls(
        [
            call(data="{}", persona="explicit-node-1"),
        ]
    )


def test_notify_epoch_error(rpc):
    rpc.deployment.race_node_interface.rpc_notify_epoch.side_effect = Exception
    with pytest.raises(error_utils.RIB412):
        rpc.notify_epoch(data="{}")
    assert rpc.deployment.race_node_interface.rpc_notify_epoch.call_count == 2

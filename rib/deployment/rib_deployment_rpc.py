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
    Remote procedure call (RPC) commands against a deployment
"""

# Python Library Imports
import functools

# Local Python Library Imports
import rib.deployment.rib_deployment as rib_deployment
from rib.utils import error_utils, status_utils


###
# Decorators
###


def execute_for_running_nodes(action: str):
    """
    Purpose:
        Custom decorator to perform status verification and invoke the wrapped function on all
        applicable nodes in the deployment.

        The wrapped function must accept a `node` keyword argument indicating the RACE node persona.
        The caller of the decorated function must use the `nodes` keyword argument to specify the
        list of RACE node personas for which to invoke the wrapped function. If no nodes are
        specified, all nodes in the deployment will be considered.
    Args:
        action: Action to be performed
    Returns:
        Decorator
    Example:
        ```
        @execute_for_running_nodes("foo")
        def foo(self, node: str, some_arg):
            pass

        obj.foo(nodes=["bar", "baz"], some_arg="qux")
        ```
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # self/args[0] is the RibDeploymentRpc instance
            deployment = args[0].deployment
            deployment.status.verify_deployment_is_active(action)

            nodes = kwargs.pop("nodes", None)

            can_execute = deployment.status.get_nodes_that_match_status(
                action=action,
                personas=nodes,
                app_status=[status_utils.AppStatus.RUNNING],
            )

            failed_to_execute = {}
            for node_name in can_execute:
                try:
                    func(*args, node=node_name, **kwargs)
                except Exception as error:
                    failed_to_execute[node_name] = error

            if failed_to_execute:
                raise error_utils.RIB412(action=action, reasons=failed_to_execute)

        return wrapper

    return decorator


###
# Types
###


class RibDeploymentRpc:
    """
    Purpose:
        Interface to execute RPC commands against a deployment
    """

    def __init__(self, deployment: "rib_deployment.RibDeployment") -> None:
        """
        Purpose:
            Initialize the object
        Args:
            deployment: Associated deployment instance
        Returns:
            N/A
        """

        self.deployment = deployment

    @execute_for_running_nodes("enable comms channel on")
    def enable_channel(self, channel_gid: str, node: str):
        """
        Purpose:
            Executes the enableChannel remote method on specified nodes

            When invoked, this function should be passed a `nodes` keyword argument with the list of
            node names. It will be invoked multiple times by the decorator for each applicable node.
        Args:
            channel_gid: ID of the channel to be enabled
            node: Name of the node on which to execute the remote method
        Returns:
            N/A
        Example:
            ```
            deployment.rpc.enable_channel(
                channel_gid="channel-1",
                nodes=["race-client-00001", "race-client-00002"],
            )
            ```
        """
        self.deployment.race_node_interface.rpc_enable_channel(
            channel_gid=channel_gid, persona=node
        )

    @execute_for_running_nodes("disable comms channel on")
    def disable_channel(self, channel_gid: str, node: str):
        """
        Purpose:
            Executes the disableChannel remote method on specified nodes

            When invoked, this function should be passed a `nodes` keyword argument with the list of
            node names. It will be invoked multiple times by the decorator for each applicable node.
        Args:
            channel_gid: ID of the channel to be disabled
            node: Name of the node on which to execute the remote method
        Returns:
            N/A
        Example:
            ```
            deployment.rpc.disable_channel(
                channel_gid="channel-1",
                nodes=["race-client-00001", "race-client-00002"],
            )
            ```
        """
        self.deployment.race_node_interface.rpc_disable_channel(
            channel_gid=channel_gid, persona=node
        )

    @execute_for_running_nodes("deactivate comms channel on")
    def deactivate_channel(self, channel_gid: str, node: str):
        """
        Purpose:
            Executes the deactivateChannel remote method on specified nodes

            When invoked, this function should be passed a `nodes` keyword argument with the list of
            node names. It will be invoked multiple times by the decorator for each applicable node.
        Args:
            channel_gid: ID of the channel to be deactivated
            node: Name of the node on which to execute the remote method
        Returns:
            N/A
        Example:
            ```
            deployment.rpc.deactivate_channel(
                channel_gid="channel-1",
                nodes=["race-client-00001", "race-client-00002"],
            )
            ```
        """
        self.deployment.race_node_interface.rpc_deactivate_channel(
            channel_gid=channel_gid, persona=node
        )

    @execute_for_running_nodes("destroy comms link on")
    def destroy_link(self, link_id: str, node: str):
        """
        Purpose:
            Executes the destroyLink remote method on specified nodes

            When invoked, this function should be passed a `nodes` keyword argument with the list of
            node names. It will be invoked multiple times by the decorator for each applicable node.
        Args:
            link_id: ID of the link to be destroyed
            node: Name of the node on which to execute the remote method
        Returns:
            N/A
        Example:
            ```
            deployment.rpc.destroy_link(
                link_id="link-1",
                nodes=["race-client-00001", "race-client-00002"],
            )
            ```
        """
        self.deployment.race_node_interface.rpc_destroy_link(
            link_id=link_id, persona=node
        )

    @execute_for_running_nodes("close comms connection on")
    def close_connection(self, connection_id: str, node: str):
        """
        Purpose:
            Executes the closeConnection remote method on specified nodes

            When invoked, this function should be passed a `nodes` keyword argument with the list of
            node names. It will be invoked multiple times by the decorator for each applicable node.
        Args:
            connection_id: ID of the connection to be closed
            node: Name of the node on which to execute the remote method
        Returns:
            N/A
        Example:
            ```
            deployment.rpc.close_connection(
                connection_id="connection-1",
                nodes=["race-client-00001", "race-client-00002"],
            )
            ```
        """
        self.deployment.race_node_interface.rpc_close_connection(
            connection_id=connection_id, persona=node
        )

    @execute_for_running_nodes("notify RACE nodes of epoch")
    def notify_epoch(self, data: str, node: str):
        """
        Purpose:
            Executes the notifyEpoch remote method on specified nodes

            When invoked, this function should be passed a `nodes` keyword argument with the list of
            node names. It will be invoked multiple times by the decorator for each applicable node.
        Args:
            data: data to send to the command
            node: Name of the node on which to execute the remote method
        Returns:
            N/A
        Example:
            ```
            deployment.rpc.notify_epoch(
                data="{}",
                nodes=["race-client-00001", "race-client-00002"],
            )
            ```
        """
        self.deployment.race_node_interface.rpc_notify_epoch(persona=node, data=data)

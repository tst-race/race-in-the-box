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
    Utilities for interacting with RACE nodes
"""

# Python Library Imports
import json
import logging
import redis
from typing import Dict, TypedDict, List, Optional

# Local Python Library Imports
from rib.utils import error_utils, redis_utils, voa_utils


###
# Constants
###


BASE_ACTIONS_CHANNEL = "race.node.actions:"
BASE_NODE_STATUS_KEY = "race.node.status:"
BASE_NODE_IS_ALIVE_KEY = "race.node.is.alive:"
BASE_APP_STATUS_KEY = "race.app.status:"
BASE_APP_IS_ALIVE_KEY = "race.app.is.alive:"


###
# Globals
###


logger = logging.getLogger(__name__)


###
# Types
###


class DaemonStatusDetails(TypedDict):
    """Info/status reported by the RACE node daemon"""

    installed: bool
    is_alive: bool
    timestamp: str


class AppStatusDetails(TypedDict):
    """Info/status reported by the RACE app"""

    is_alive: bool
    timestamp: str


class RaceNodeInterface:
    """Interface for interacting with RACE nodes through a Redis client"""

    redis_client: redis.Redis

    def __init__(self, redis_host: str = "rib-redis") -> None:
        """
        Purpose:
            Initializes the RACE node interface
        Args:
            redis_host: Hostname of the Redis server
        Returns:
            N/A
        """
        self.redis_client = redis_utils.create_redis_client(redis_host)
        if not self.redis_client:
            raise error_utils.RIB407()

    ###
    # Properties
    ###

    @property
    def connected(self) -> bool:
        """RaceNodeInterface is connected"""

        return redis_utils.is_connected(self.redis_client)

    @property
    def active_deployment(self) -> Optional[str]:
        """Get Active Deployment set in Redis"""

        if not self.connected:
            return None

        return self.redis_client.get("active_deployment")

    ###
    # Info/Status functions
    ###

    def get_all_node_personas(self) -> List[str]:
        """
        Purpose:
            Get list of all RACE node personas to have ever reported status
        Args:
            N/A
        Returns:
            Set of RACE node personas
        """

        if not self.connected:
            return []

        (_, keys) = self.redis_client.scan(
            cursor=0, match=f"{BASE_NODE_IS_ALIVE_KEY}*", count=500000
        )
        return [key.replace(BASE_NODE_IS_ALIVE_KEY, "") for key in keys]

    def get_daemon_status(self, persona: str) -> DaemonStatusDetails:
        """
        Purpose:
            Get daemon status for the specified node
        Args:
            persona: RACE node persona
        Returns:
            Daemon status details
        """

        # if redis is not running, we can report the node as down
        if not self.connected:
            return {
                "installed": False,
                "configsPresent": False,
                "deployment": "",
                "timestamp": "",
                "is_alive": False,
                "dnsSuccessful": False,
                "nodePlatform": "",
                "nodeArchitecture": "",
            }

        try:
            status_str = self.redis_client.get(f"{BASE_NODE_STATUS_KEY}{persona}")
            if not status_str:
                status = {
                    "installed": False,
                    "configsPresent": False,
                    "deployment": "",
                    "timestamp": "",
                    "dnsSuccessful": False,
                    "nodePlatform": "",
                    "nodeArchitecture": "",
                }
            else:
                status = json.loads(status_str)

            is_alive_str = self.redis_client.get(f"{BASE_NODE_IS_ALIVE_KEY}{persona}")
            if not is_alive_str:
                is_alive_str = "false"
            status["is_alive"] = is_alive_str.lower() == "true"

            logger.trace(f"Node status for {persona}: {status}")
            return status

        except Exception as err:
            logger.warning(f"Error getting node status for {persona}: {err}")
            raise error_utils.RIB408(persona, str(err))

    def get_app_status(self, persona: str) -> AppStatusDetails:
        """
        Purpose:
            Get RACE app status for the specified node
        Args:
            persona: RACE node persona
        Returns:
            App status details
        """
        try:
            status_str = self.redis_client.get(f"{BASE_APP_STATUS_KEY}{persona}")
            if not status_str:
                status = {
                    "timestamp": "",
                    "sdkStatus": "",
                }
            else:
                status = json.loads(status_str)

            is_alive_str = self.redis_client.get(f"{BASE_APP_IS_ALIVE_KEY}{persona}")
            if not is_alive_str:
                is_alive_str = "false"
            status["is_alive"] = is_alive_str.lower() == "true"

            logger.trace(f"App status for {persona}: {status}")
            return status

        except Exception as err:
            # logger.warning(f"Error getting app status for {persona}: {err}")
            raise error_utils.RIB409(persona, str(err))

    ###
    # Active Deployments
    ###

    def set_active_deployment(self, deployment_name: str) -> None:
        """
        Purpose:
            Set an active deployment in Redis for tracking deployments
        Args:
            deployment_name: Name of deployment to set in redis
        Returns:
            N/A
        Raises:
            Exception: if there is already an active deployment set in redis
        """

        # Check to see if we are setting the right active deployment, if not error
        current_active_deployment = self.redis_client.get("active_deployment")
        if current_active_deployment and current_active_deployment != deployment_name:
            raise error_utils.RIB413(
                deployment_name,
                current_active_deployment,
                "set",
            )

        # Set the key
        self.redis_client.set("active_deployment", deployment_name)

    def unset_active_deployment(self, deployment_name: str) -> None:
        """
        Purpose:
            Unset the active_deployment key in redis
        Args:
            deployment_name: Name of deployment to unset in redis (if it is currently
                the active deployment)
        Returns:
            N/A
        """

        if not self.connected:
            # Don't need to do anything if we can't get to rib
            return

        # Check to see if we are unsetting the right active deployment, if not error
        current_active_deployment = self.redis_client.get("active_deployment")
        if current_active_deployment and current_active_deployment != deployment_name:
            raise error_utils.RIB413(
                deployment_name,
                current_active_deployment,
                "unset",
            )

        # Unset the key
        self.redis_client.delete("active_deployment")

    ###
    # Command functions
    ###

    def publish_daemon_config(
        self,
        deployment_name: str,
        persona: str,
        is_boostrap_node: bool,
        race_app: str,
        status_publishing_rate: int,
    ) -> None:
        """
        Purpose:
            Set configs for the Daemon on the RACE node
        Args:
            deployment_name: Name of the deployment
            persona: RACE node persona
            is_boostrap_node: Whether or not the node is a bootstrap node
            race_app: Which race app to run (Android App, racetestapp-linux, registry-exemplar, Peraton registry)
            status_publishing_rate: rate to publish daemon status
        """
        self._send_action_command(
            persona=persona,
            action={
                "type": "publish-daemon-config",
                "payload": {
                    "deployment-name": deployment_name,
                    "is-bootstrap-node": is_boostrap_node,
                    "race-app": race_app,
                    "status-publishing-rate": status_publishing_rate,
                },
            },
        )

    def pull_configs(self, deployment_name: str, persona: str, etc_only: bool) -> None:
        """
        Purpose:
            Signal the RACE node to pull configs from the file server.
        Args:
            deployment_name: Name of the deployment
            persona: RACE node persona
            etc_only: flag to only pull etc.tar, not configs.tar
        """
        self._send_action_command(
            persona,
            {
                "type": "pull-configs",
                "payload": {"deployment-name": deployment_name, "etc_only": etc_only},
            },
        )

    def set_daemon_config(
        self,
        deployment_name: Optional[str] = None,
        persona: Optional[str] = None,
        genesis: Optional[bool] = None,
        app: Optional[str] = None,
        period: Optional[int] = None,
        ttl_factor: Optional[int] = None,
    ) -> None:
        """
        Purpose:
            Set the config for the daemon on the specified node
        Args:
            deployment_name: Name of the deployment
            persona: RACE node persona
            genesis: Whether the node is a genesis node
            app: Name of the app/executable to run (testapp vs registry)
            period: Statusing period to set
            ttl_factor: Mulitplier of period to get the time to live
        Returns:
            N/A
        """

        payload = {}
        if deployment_name is not None:
            payload["deployment-name"] = deployment_name
        if genesis is not None:
            payload["genesis"] = genesis
        if app is not None:
            payload["app"] = app
        if period is not None:
            payload["period"] = period
        if ttl_factor is not None:
            payload["ttl-factor"] = ttl_factor

        self._send_action_command(
            persona,
            {
                "type": "set-daemon-config",
                "payload": payload,
            },
        )

    def clear_configs_and_etc(
        self,
        persona: str,
    ) -> None:
        """
        Purpose:
            Clear configs and etc from the specified node
        Args:
            persona: RACE node persona
        Returns:
            N/A
        """
        self._send_action_command(
            persona,
            {
                "type": "clear-configs-and-etc",
                "payload": {},
            },
        )

    def clear_artifacts(
        self,
        persona: str,
    ) -> None:
        """
        Purpose:
            Clear artifacts from the specified node
        Args:
            persona: RACE node persona
        Returns:
            N/A
        """
        self._send_action_command(
            persona,
            {
                "type": "clear-artifacts",
                "payload": {},
            },
        )

    def start_app(self, persona: str) -> None:
        """
        Purpose:
            Start the RACE app on the specified node
        Args:
            persona: RACE node persona
        Returns:
            N/A
        """
        self._send_action_command(persona, {"type": "start", "payload": {}})

    def stop_app(self, persona: str) -> None:
        """
        Purpose:
            Stop the RACE app on the specified node
        Args:
            persona: RACE node persona
        Returns:
            N/A
        """
        self._send_action_command(persona, {"type": "stop", "payload": {}})

    def kill_app(self, persona: str) -> None:
        """
        Purpose:
            Kill the RACE app on the specified node
        Args:
            persona: RACE node persona
        Returns:
            N/A
        """
        self._send_action_command(persona, {"type": "kill", "payload": {}})

    def rotate_logs(
        self, persona: str, delete: bool = True, backup_id: str = ""
    ) -> None:
        """
        Purpose:
            Rotate RACE app logs on the specified node. Logs may be deleted, and may
            be backed up by uploading to the rib-file-server under the given backup identifier.
        Args:
            persona: RACE node persona
            delete: Whether to delete logs
            backup_id: Unique identifier (e.g., a timestamp) for the backed up logs,
                if empty no backup will occur
        Returns:
            N/A
        """
        self._send_action_command(
            persona,
            {
                "type": "rotate-logs",
                "payload": {"delete": delete, "backup-id": backup_id},
            },
        )

    def push_runtime_configs(self, persona: str, config_name: str) -> None:
        """"""
        self._send_action_command(
            persona,
            {
                "type": "push-runtime-configs",
                "payload": {"name": config_name},
            },
        )

    def set_timezone(self, persona: str, specified_zone: str) -> None:
        """
        Purpose:
            Set the system timezone, to affect local clock time
        Args:
            persona: RACE node persona
            specified_zone: the new timezone to be written
        Return:
            N/A
        """
        self._send_action_command(
            persona,
            {
                "type": "set-timezone",
                "payload": {
                    "timezone": specified_zone,
                },
            },
        )

    def send_manual_message(
        self,
        sender: str,
        recipient: str,
        message: str,
        test_id: str = "",
        network_manager_bypass_route: str = "",
    ) -> None:
        """
        Purpose:
            Send a manual message from the sender node to the recipient node
        Args:
            sender: Persona of the sender RACE node
            recipient: Persona of the recipient RACE node
            message: Contents of the message to be sent
            test_id: Test identifier to be inserted into the message (if left blank,
                test ID will be "")
            network_manager_bypass_route: Channel ID, link ID, or connection ID over which to
                send the network-manager-bypass message (leave blank for normal message routing)
        Return:
            N/A
        """
        self._send_action_command(
            sender,
            {
                "type": "send-message",
                "payload": {
                    "send-type": "manual",
                    "recipient": recipient,
                    "message": message,
                    "test-id": test_id,
                    "network-manager-bypass-route": network_manager_bypass_route or "",
                },
            },
        )

    def send_auto_message(
        self,
        sender: str,
        recipient: str,
        period: int,
        quantity: int,
        size: int,
        test_id: str = "",
        network_manager_bypass_route: str = "",
    ) -> None:
        """
        Purpose:
            Send an auto message from the sender node to the recipient node
        Args:
            sender: Persona of the sender RACE node
            recipient: Persona of the recipient RACE node
            period: Time in milliseconds to wait between each message send
            quantity: Number of messages to be sent
            size: Size in bytes of the auto-generated message
            test_id: Test identifier to be inserted into the message (if left blank,
                test ID will be "")
            network_manager_bypass_route: Channel ID, link ID, or connection ID over which to
                send the network-manager-bypass message (leave blank for normal message routing)
        Return:
            N/A
        """
        self._send_action_command(
            sender,
            {
                "type": "send-message",
                "payload": {
                    "send-type": "auto",
                    "recipient": recipient,
                    "period": int(period),
                    "quantity": int(quantity),
                    "size": int(size),
                    "test-id": test_id,
                    "network-manager-bypass-route": network_manager_bypass_route or "",
                },
            },
        )

    def send_message_plan(
        self,
        sender: str,
        plan: Dict,
    ) -> None:
        """
        Purpose:
            Send a message plan to be executed on the sender node
        Args:
            sender: Persona of the sender RACE node
            plan: JSON message plan to be executed
        Return:
            N/A
        """
        self._send_action_command(
            sender,
            {
                "type": "send-message",
                "payload": {
                    "send-type": "plan",
                    "plan": plan,
                },
            },
        )

    def open_network_manager_bypass_recv(
        self,
        sender: str,
        recipient: str,
        network_manager_bypass_route: str,
    ) -> None:
        """
        Purpose:
            Open a network-manager-bypass receive connection on the recipient node
        Args:
            sender: Persona of the sender RACE node
            recipient: Persona of the recipient RACE node
            network_manager_bypass_route: Channel ID or link ID on which to open a receive
                connection from the sender node
        Return:
            N/A
        """
        self._send_action_command(
            recipient,
            {
                "type": "open-network-manager-bypass-receive-connection",
                "payload": {
                    "persona": sender,
                    "route": network_manager_bypass_route,
                },
            },
        )

    def add_voa_rule(
        self,
        node: str,
        rule_action: str,
        **rule: voa_utils.VoaRule,
    ) -> None:
        """
        Purpose:
            Add a VoA rule to the given node
        Args:
            node: Persona of the RACE node
            rule_action: The specific VoA action to perform (delay, drop, tamper, replay)
            rule: Rule parameters

        Return:
            N/A
        """

        voa_config = voa_utils.construct_voa_rule(node, rule_action, **rule)
        self.apply_voa_config(node, voa_config)

    def apply_voa_config(
        self,
        node: str,
        voa_config: Dict,
    ) -> None:
        """
        Purpose:
            Apply the VoA config on the given node
        Args:
            node: Persona of the RACE node
            voa_config: JSON VoA config to be installed
        Return:
            N/A
        """
        cmd_payload = {
            "type": "voa-action",
            "payload": {
                "action": "add-rules",
                "config": voa_config,
            },
        }

        self._send_action_command(node, cmd_payload)

    def delete_voa_rules(
        self,
        node: str,
        rule_id_list: List[str],
    ) -> None:
        """
        Purpose:
            Delete VoA rules with the given Ids
        Args:
            node: Persona of the RACE node
            rule_id_list: List of rule identifiers, or empty list if all rules
        Return:
            N/A
        """
        cmd_payload = {
            "type": "voa-action",
            "payload": {
                "action": "delete-rules",
                "config": {
                    "rule_ids": rule_id_list,
                },
            },
        }

        self._send_action_command(node, cmd_payload)

    def voa_set_active_state(
        self,
        node: str,
        state: bool,
    ) -> None:
        """
        Purpose:
            Set the VoA state (active or not)
        Args:
            node: Persona of the RACE node
            state: The desired state
        Return:
            N/A
        """
        cmd_payload = {
            "type": "voa-action",
            "payload": {
                "action": "set-active-state",
                "config": {
                    "state": state,
                },
            },
        }

        self._send_action_command(node, cmd_payload)

    def prepare_to_bootstrap(
        self,
        introducer: str,
        target: str,
        platform: str,
        architecture: str,
        node_type: str,
        passphrase: str,
        bootstrapChannelId: str,
    ) -> None:
        """
        Purpose:
            Prepare to bootstrap a new RACE node on the introducer node
        Args:
            introducer: Persona of the introducer node
            target: Persona of the target node
            platform: Platform of the new device to be bootstrapped
            architecture: Architecture of the new device to be bootstrapped
            node_type: Node type of the new device to be bootstrapped
            passphrase: Passphrase to use while bootstrapping
            bootstrapChannelId: Preferred bootstrap channel
        Return:
            N/A
        """
        self._send_action_command(
            introducer,
            {
                "type": "prepare-to-bootstrap",
                "payload": {
                    "target": target,
                    "platform": platform,
                    "architecture": architecture,
                    "nodeType": node_type,
                    "passphrase": passphrase,
                    "bootstrapChannelId": bootstrapChannelId,
                },
            },
        )

    def rpc_notify_epoch(
        self,
        persona: str,
        data: str,
    ) -> None:
        """
        Purpose:
            Notify a node to trigger an epoch
        Args:
            persona: RACE node persona
            data: data to pass through to the command
        Return:
            N/A
        """
        self._send_action_command(
            persona,
            {
                "type": "rpc",
                "payload": {
                    "action": "notify-epoch",
                    "data": data,
                },
            },
        )

    def rpc_deactivate_channel(self, persona: str, channel_gid: str) -> None:
        """
        Purpose:
            Execute the deactivateChannel RPC on the specified node
        Args:
            persona: RACE node persona
            channel_gid: ID of channel to be deactivated
        """
        self._send_action_command(
            persona,
            {
                "type": "rpc",
                "payload": {
                    "action": "deactivate-channel",
                    "channelGid": channel_gid,
                },
            },
        )

    def rpc_destroy_link(self, persona: str, link_id: str) -> None:
        """
        Purpose:
            Execute the destroyLink RPC on the specified node
        Args:
            persona: RACE node persona
            link_id: ID of link to be destroyed
        """
        self._send_action_command(
            persona,
            {
                "type": "rpc",
                "payload": {
                    "action": "destroy-link",
                    "linkId": link_id,
                },
            },
        )

    def rpc_close_connection(self, persona: str, connection_id: str) -> None:
        """
        Purpose:
            Execute the closeConnection RPC on the specified node
        Args:
            persona: RACE node persona
            connection_id: ID of connection to be closed
        """
        self._send_action_command(
            persona,
            {
                "type": "rpc",
                "payload": {
                    "action": "close-connection",
                    "connectionId": connection_id,
                },
            },
        )

    def rpc_enable_channel(self, persona: str, channel_gid: str) -> None:
        """
        Purpose:
            Execute the enableChannel RPC on the specified node
        Args:
            persona: RACE node persona
            channel_gid: Name of the channel to be enabled
        """
        self._send_action_command(
            persona,
            {
                "type": "rpc",
                "payload": {
                    "action": "enable-channel",
                    "channelGid": channel_gid,
                },
            },
        )

    def rpc_disable_channel(self, persona: str, channel_gid: str) -> None:
        """
        Purpose:
            Execute the disableChannel RPC on the specified node
        Args:
            persona: RACE node persona
            channel_gid: Name of the channel to be disabled
        """
        self._send_action_command(
            persona,
            {
                "type": "rpc",
                "payload": {
                    "action": "disable-channel",
                    "channelGid": channel_gid,
                },
            },
        )

    ###
    # Internal helper functions
    ###

    def _send_action_command(self, persona: str, action: Dict) -> None:
        """
        Purpose:
            Sends an action command to the specified RACE node
        Args:
            client: Redis client
            persona: RACE node persona
            action: Action command
        Return:
            N/A
        """
        try:
            channel = f"{BASE_ACTIONS_CHANNEL}{persona}"
            action_str = json.dumps(action)
            logger.trace(f"Publishing {action_str} to {channel}")
            self.redis_client.publish(channel, action_str)
        except Exception as err:
            logger.warning(f"Error publishing action to {persona}: {action}: {err}")
            raise error_utils.RIB410(persona, action.get("type", ""), str(err))

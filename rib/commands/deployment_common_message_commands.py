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
        Deployment Message Command Group is responsible for using RACE in the Box
        deployments for sending and receiving messages
"""

# Python Library Imports
import sys
import logging
from rib.utils import testing_utils
from rib.utils import error_utils
from rib.utils import messaging_utils
import click
import time
from typing import Optional

# Local Python Library Imports
from rib.commands.deployment_options import (
    deployment_name_option,
    network_manager_bypass_route_option,
    pass_rib_mode,
)
from rib.commands.env_local_commands import status
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import elasticsearch_utils
from rib.commands.common_options import timeout_option

# Set up logger
logger = logging.getLogger(__name__)


###
# Send Message Commands
###


@click.group("message")
def message_command_group() -> None:
    """Commands for sending and receiving messages"""


@message_command_group.command("send-auto")
@deployment_name_option("send auto messages on")
@click.option(
    "--period",
    "message_period",
    help="Time (in milliseconds) to wait between sending messages",
    required=True,
    type=str,
)
@click.option(
    "--quantity",
    "message_quantity",
    help="Quantity of Messages to Send",
    required=True,
    type=int,
)
@click.option(
    "--size",
    "message_size",
    help="Size (in bytes) of Messages to Send",
    required=True,
    type=int,
)
@click.option(
    "--recipient", "recipient", help="Recipient of Message", required=False, type=str
)
@click.option("--sender", "sender", help="Sender of Message", required=False, type=str)
@click.option(
    "--test-id",
    "test_id",
    help="A string added to the message sent to aid in identification",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--verify",
    "verify",
    flag_value=True,
    help="Verify Receipt of Messages",
)
@timeout_option(default=30)
@network_manager_bypass_route_option()
@pass_rib_mode
def send_auto(
    rib_mode: str,
    message_period: int,
    message_quantity: int,
    message_size: int,
    recipient: Optional[str],
    sender: Optional[str],
    test_id: str,
    deployment_name: str,
    network_manager_bypass_route: Optional[str],
    timeout: int,
    verify: bool = False,
):
    """
    Send a auto messages from/to a (or all) node(s)
    """

    click.echo("Sending Messages")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Give a non-named verify test a unique name
    if test_id == "" and verify:
        test_id = "V-" + str(time.time())

    # Initialize testing object to track verification testing
    test_result = testing_utils.TestResult(test_case="send_auto_messages")

    start_time = int(time.time() * 1000)

    # Updated send_message to return the recipient_sender_mapping
    returned_recipient_sender_mapping = deployment.send_message(
        message_type="auto",
        message_period=message_period,
        message_quantity=message_quantity,
        message_size=message_size,
        recipient=recipient,
        sender=sender,
        test_id=test_id,
        network_manager_bypass_route=network_manager_bypass_route,
    )

    click.echo("Sent Messages To Deployment Nodes")

    if verify:
        result = testing_utils.evaluate_messages_test(
            elasticsearch_host_name=deployment.get_elasticsearch_hostname(),
            test_id=test_id,
            start_time=start_time,
            run_time=timeout,
            test_result=test_result,
            expected_message_count=message_quantity,
            recipient_sender_mapping=returned_recipient_sender_mapping,
            expected_message_size=message_size,
            range_name=deployment.get_range_name(),
        )

        # print the report and return the report status
        all_passed = testing_utils.print_single_test_case_report(result)

        if not all_passed:
            raise error_utils.RIB604(rib_mode, deployment_name, "auto")

    click.echo("Auto Message Sends Complete")


@message_command_group.command("send-manual")
@deployment_name_option("send manual messages on")
@click.option(
    "--message", "message_content", help="Message to Send", required=True, type=str
)
@click.option(
    "--recipient", "recipient", help="Recipient of Message", required=False, type=str
)
@click.option("--sender", "sender", help="Sender of Message", required=False, type=str)
@click.option(
    "--test-id",
    "test_id",
    help="A string added to the message sent to aid in identification",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--verify",
    "verify",
    flag_value=True,
    help="Verify Receipt of Messages",
)
@timeout_option(default=30)
@network_manager_bypass_route_option()
@pass_rib_mode
def send_manual(
    rib_mode: str,
    deployment_name: str,
    message_content: str,
    recipient: Optional[str],
    sender: Optional[str],
    test_id: str,
    network_manager_bypass_route: Optional[str],
    timeout: int,
    verify: bool = False,
):
    """
    Send a manual message from/to a (or all) node(s)
    """

    click.echo("Sending Messages")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Give a non-named verify test a unique name
    if test_id == "" and verify:
        test_id = "V-" + str(time.time())

    # Initialize testing object to track verification testing
    test_result = testing_utils.TestResult(test_case="send_manual_messages")

    start_time = int(time.time() * 1000)

    # Updated send message to return the recipient sender mapping
    returned_recipient_sender_mapping = deployment.send_message(
        message_type="manual",
        message_content=message_content,
        recipient=recipient,
        sender=sender,
        test_id=test_id,
        network_manager_bypass_route=network_manager_bypass_route,
    )

    click.echo("Sent Messages To Deployment Nodes")

    if verify:
        # expected message count/quantity should be 1 in manual send mode
        # this is because message quantity refers to the number of messages along each paired edge,
        # not the total number of messages in the network
        message_quantity = 1

        result = testing_utils.evaluate_messages_test(
            elasticsearch_host_name=deployment.get_elasticsearch_hostname(),
            test_id=test_id,
            start_time=start_time,
            run_time=timeout,
            test_result=test_result,
            expected_message_count=message_quantity,
            recipient_sender_mapping=returned_recipient_sender_mapping,
            range_name=deployment.get_range_name(),
        )

        # print the report and return the report status
        all_passed = testing_utils.print_single_test_case_report(result)

        if not all_passed:
            raise error_utils.RIB604(rib_mode, deployment_name, "manual")

    click.echo("Manual Message Send Complete")


@message_command_group.command("send-plan")
@deployment_name_option("send message plan on")
@click.option(
    "--plan-file", "plan_file", help="Path to plan file", required=True, type=str
)
@click.option(
    "--start-time",
    "start_time",
    help="The time the messages will start to send, in milliseconds since epoch",
    required=False,
    type=int,
    default=None,
)
@click.option(
    "--test-id",
    "test_id",
    help="A string added to the message sent to aid in identification",
    required=False,
    type=str,
    default="",
)
@network_manager_bypass_route_option()
@pass_rib_mode
def send_plan(
    rib_mode: str,
    deployment_name: str,
    plan_file: str,
    start_time: Optional[int],
    network_manager_bypass_route: Optional[str],
    test_id: str,
):
    """
    Send a test plan to node(s)
    """

    if start_time is None:
        # if start time is not supplied, start in 10 seconds (in milliseconds) to
        # give time for nodes to receive the plan and create messages
        start_time = int((time.time() + 10) * 1000)

    click.echo("Sending Test Plan")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Call send message for the class
    deployment.send_plan(
        message_plan_file=plan_file,
        start_time=start_time,
        network_manager_bypass_route=network_manager_bypass_route,
        test_id=test_id,
    )

    click.echo("Sent Messages To Deployment Nodes")


###
# Get Message Commands
###


@message_command_group.command("list")
@deployment_name_option("list messages")
@click.option(
    "--recipient",
    "recipient",
    help="Filter on recipient of message",
    required=False,
    type=str,
)
@click.option(
    "--sender", "sender", help="Filter on sender of message", required=False, type=str
)
@click.option(
    "--test-id",
    "test_id",
    help="Filter on Test ID",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--trace-id",
    "trace_id",
    help="Filter on Trace ID",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--since",
    "date_from",
    help="Return records after date ('YYYY-MM-DD HH:MM:SS')",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--until",
    "date_to",
    help="Return records until date ('YYYY-MM-DD HH:MM:SS')",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--sort-by",
    "sort_by",
    help="Sort the list on a column",
    required=False,
    type=str,
    default="Status",
)
@click.option(
    "--reverse-sort", "reverse_sort", flag_value=True, help="Reverse the sort"
)
@pass_rib_mode
def list_messages(
    rib_mode: str,
    deployment_name: str,
    recipient: Optional[str],
    sender: Optional[str],
    test_id: str,
    trace_id: str = None,
    date_from: str = None,
    date_to: str = None,
    sort_by: str = "Status",
    reverse_sort: bool = False,
):
    """
    Get messages from/to a (or all) node(s)
    """
    try:
        # Verbose controls whether this function prints
        messaging_utils.get_matching_messages(
            rib_mode=rib_mode,
            deployment_name=deployment_name,
            recipient=recipient,
            sender=sender,
            test_id=test_id,
            trace_id=trace_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            reverse_sort=reverse_sort,
            verbose=True,
        )
    except:
        raise error_utils.RIB605(rib_mode, deployment_name, "message list")


###
# Verify Message Commands
###


@message_command_group.command("verify")
@deployment_name_option("verify test-id state on")
@click.option(
    "--recipient",
    "recipient",
    help="Filter on recipient of message",
    required=False,
    type=str,
)
@click.option(
    "--sender",
    "sender",
    help="Filter on sender of message",
    required=False,
    type=str,
)
@click.option(
    "--test-id",
    "test_id",
    help="Filter on Test ID",
    required=True,
    type=str,
)
@click.option(
    "--verbose",
    "verbose",
    help="print matching messages",
    flag_value=True,
    required=False,
)
@click.option(
    "--trace-id",
    "trace_id",
    help="Filter on Trace ID",
    required=False,
    type=str,
    default="",
)
@click.option(
    "--sort-by",
    "sort_by",
    help="Sort the list on a column",
    required=False,
    type=str,
    default="Status",
)
@pass_rib_mode
def verify(
    rib_mode: str,
    deployment_name: str,
    recipient: Optional[str],
    sender: Optional[str],
    test_id: str,
    verbose: bool = False,
    trace_id: str = None,
    sort_by: str = "Status",
):
    """
    Verify messages have been received on test-id and secondary filters (sender, recipient, trace-id)
    """
    try:
        unreceived_count, messages = messaging_utils.get_matching_messages(
            rib_mode=rib_mode,
            deployment_name=deployment_name,
            recipient=recipient,
            sender=sender,
            test_id=test_id,
            trace_id=trace_id,
            sort_by=sort_by,
            verbose=verbose,
        )
    except:
        raise error_utils.RIB605(rib_mode, deployment_name, "message verify")

    if unreceived_count == 0 and len(messages) > 0:
        click.echo(f"All Messages In {rib_mode}:{test_id} Have Been Received")
    else:
        if len(messages) > 0:
            click.echo(
                f"{unreceived_count}/{len(messages)} Messages In {rib_mode}:{test_id} Have Not Been Received"
            )
        else:
            click.echo("No Matching Messages Found")
        sys.exit(1)


###
# Open Connection Commands
###


@message_command_group.command("open-network-manager-bypass-recv")
@deployment_name_option("open network-manager-bypass receive connections")
@click.option(
    "--recipient",
    "recipient",
    help="Node on which to open network-manager-bypass receive connection",
    required=True,
    type=str,
)
@click.option(
    "--sender",
    "sender",
    help="Node from which to receive",
    required=True,
    type=str,
)
@network_manager_bypass_route_option()
@pass_rib_mode
def open_network_manager_bypass_recv(
    rib_mode: str,
    deployment_name: str,
    recipient: str,
    sender: str,
    network_manager_bypass_route: Optional[str],
):
    """
    Open a temporary network-manager-bypass receive connection on a recipient node
    """

    click.echo("Opening network-manager-bypass Receive Connection")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.open_network_manager_bypass_recv(
        recipient, sender, network_manager_bypass_route
    )

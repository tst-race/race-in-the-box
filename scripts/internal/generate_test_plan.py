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

# -----------------------------------------------------------------------------
# Script to generate a test plan JSON to be used with
# `rib deployment message send-plan`.
#
# The only required argument is the client count (which may be 0). The plan will
# include client-to-client messages sent from every client to every other client.
#
# If a server node count is specified, it is assumed that network-manager-bypass will be used
# with the plan, and the generated plan will include client-to-server and
# server-toserver messages. It will not include any client-to-client messages.
#
# By default, the count, size, and send times for messages are randomly
# generated between default minimum and maximum values. These bounds can be
# modified, or exact values can be specified.
#
# Examples:
#   # client-to-client messages in a 3-client deployment
#   python3 generate_test_plan.py --client-count=3 --out=./test-plan-1.json
#
#   # network-manager-bypass messages in a 3x4 deployment
#   python3 generate_test_plan.py --client-count=3 --server-count=4 \
#       --out=./test-plan-2.json
#
#   # Fixed message count for all sender-recipient pairs (5 messages each)
#   python3 generate_test_plan.py --client-count=3 --message-count=5
#
#   # Fixed message size for all messages (140 bytes)
#   python3 generate_test_plan.py --client-count=3 --message-size=140
#
#   # Tweaked min/max for randomized message parameters
#   python3 generate_test_plan.py --client-count=3 \
#       --min-message-count=10 --max-message-count=20 \
#       --min-message-size=100 --max-message-size=300 \
#       --min-send-time=2000 --max-send-time=10000
# -----------------------------------------------------------------------------

import argparse
import json
import random
import sys
from typing import Dict, List, Optional


def get_cli_arguments() -> argparse.Namespace:
    """
    Purpose:
        Parses command-line arguments
    Args:
        N/A
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate test plan",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--out",
        default=sys.stdout,
        help="Output for test plan JSON",
        type=argparse.FileType("w"),
    )

    # Nodes
    parser.add_argument(
        "--client-count",
        help="Number of clients in the deployment",
        required=True,
        type=int,
    )
    parser.add_argument(
        "--server-count",
        default=0,
        help="Number of servers in the deployment (assumes network-manager-bypass)",
        type=int,
    )

    # Message count
    parser.add_argument(
        "--message-count",
        default=None,
        help="Number of messages to be sent by each sender node (if not using min/max)",
        type=int,
    )
    parser.add_argument(
        "--min-message-count",
        default=2,
        help="Minimum number of messages to be sent by each sender node (if not using an exact count)",
        type=int,
    )
    parser.add_argument(
        "--max-message-count",
        default=5,
        help="Maximum number of messages to be sent by each sender node (if not using an exact count)",
        type=int,
    )

    # Message size
    parser.add_argument(
        "--message-size",
        default=None,
        help="Message size in bytes for each message (if not using min/max)",
        type=int,
    )
    parser.add_argument(
        "--min-message-size",
        default=100,
        help="Minimum message size in bytes for each message (if not using an exact size)",
    )
    parser.add_argument(
        "--max-message-size",
        default=300,
        help="Maximum message size in bytes for each message (if not using an exact size)",
    )

    # Send time
    parser.add_argument(
        "--min-send-time",
        default=500,
        help="Minimum send time in milliseconds since plan execution start time",
        type=int,
    )
    parser.add_argument(
        "--max-send-time",
        default=5000,
        help="Maximum send time in milliseconds since plan execution start time",
        type=int,
    )

    parser.add_argument(
        "--seed",
        default=None,
        help="Random number generator seed",
    )

    return parser.parse_args()


def generate_node_names(
    node_type: str, count: int, prefix: str = "race", id_width: int = 5
) -> List[str]:
    """
    Purpose:
        Generates a list of node names/RACE node personas
    Args:
        node_type: "client" or "server"
        count: Number of nodes
        prefix: Node name prefix
        id_width: Number of digits to pad the node ID/number
    Returns:
        List of node names
    """
    return [
        "-".join([prefix, node_type, str(idx + 1).zfill(id_width)])
        for idx in range(count)
    ]


def generate_sender_recipient_pairs_from_node_names(
    senders: List[str], recipients: List[str]
) -> Dict[str, List[str]]:
    """
    Purpose:
        Generates a mapping of sender node names to a list of recipient node names,
        where each given sender is mapped against each given recipient
    Args:
        senders: List of sender node names
        recipients: List of recipient node names
    Returns:
        Map of sender node names to list of recipient node names
    """
    pairs = {}
    for sender in senders:
        pairs.setdefault(sender, [])
        for recipient in recipients:
            if sender == recipient:
                continue
            pairs.get(sender).append(recipient)
    return pairs


def generate_sender_recipient_pairs_from_node_counts(
    client_count: int, server_count: int
) -> Dict[str, List[str]]:
    """
    Purpose:
        Generates a mapping of sender node names to a list of recipient node names
    """
    """
    Purpose:
        Generates a mapping of sender node names to a list of recipient node names,
        given a count of clients and servers. If servers are given, it is assumed that
        network-manager-bypass is enabled and only client-to-server and server-to-server mappings
        will be generated. Otherwise only client-to-client mappings are generated.
    Args:
        client_count: Number of client nodes
        sender_count: Number of sender nodes
    Returns:
        Map of sender node names to list of recipient node names
    """
    pairs = {}
    client_node_names = generate_node_names("client", client_count)
    if server_count:  # network-manager-bypass pairs
        server_node_names = generate_node_names("server", server_count)
        # server-to-server
        pairs.update(
            generate_sender_recipient_pairs_from_node_names(
                server_node_names, server_node_names
            )
        )
        # client-to-server
        pairs.update(
            generate_sender_recipient_pairs_from_node_names(
                client_node_names, server_node_names
            )
        )
    else:
        # client-to-client
        pairs.update(
            generate_sender_recipient_pairs_from_node_names(
                client_node_names, client_node_names
            )
        )
    return pairs


def generate_value(min_val: int, max_val: int, exact: Optional[int] = None) -> int:
    """
    Purpose:
        Generates an int value between the given min and max, or just returns the
        exact value if one was given. If min_val is greater than max_val, they are
        swapped and max_val will be considered the lower bound.
    Args:
        min_val: Minimum integer value, if no exact value is specified
        max_val: Maximum integer value, if no exact value is specified
        exact: Exact integer value to be returned
    Returns:
        Integer value between min and max, or the exact value
    """
    if exact is not None:
        return exact
    return random.randint(min(min_val, max_val), max(min_val, max_val))


def generate_messages(
    message_count: Optional[int],
    min_message_count: int,
    max_message_count: int,
    message_size: Optional[int],
    min_message_size: int,
    max_message_size: int,
    min_send_time: int,
    max_send_time: int,
) -> List[Dict[str, int]]:
    """
    Purpose:
        Generate a series of messages with potentially random message count, sizes, and send times.
    Args:
        message_count: Exact message count, if specified
        min_message_count: Minimum number of messages, if not an exact count
        max_message_count: Maximum number of messages, if not an exact count
        message_size: Exact message size (in bytes), if specified
        min_message_size: Minimum message size (in byte), if not an exact size
        max_message_size: Maximum message size (in byte), if not an exact size
        min_send_time: Minimum send time (in milliseconds after test plan start time)
        max_send_time: Maximum send time (in milliseconds after test plan start time)
    Returns:
        List of messages
    """
    return [
        {
            "size": generate_value(
                min_val=min_message_size, max_val=max_message_size, exact=message_size
            ),
            "time": generate_value(min_val=min_send_time, max_val=max_send_time),
        }
        for _ in range(
            generate_value(
                min_val=min_message_count,
                max_val=max_message_count,
                exact=message_count,
            )
        )
    ]


if __name__ == "__main__":
    args = get_cli_arguments()

    random.seed(args.seed)

    sender_recipient_pairs = generate_sender_recipient_pairs_from_node_counts(
        client_count=args.client_count,
        server_count=args.server_count,
    )

    test_plan = {"messages": {}}
    for sender, recipients in sender_recipient_pairs.items():
        test_plan["messages"][sender] = {}
        for recipient in recipients:
            test_plan["messages"][sender][recipient] = generate_messages(
                message_count=args.message_count,
                min_message_count=args.min_message_count,
                max_message_count=args.max_message_count,
                message_size=args.message_size,
                min_message_size=args.min_message_size,
                max_message_size=args.max_message_size,
                min_send_time=args.min_send_time,
                max_send_time=args.max_send_time,
            )

    args.out.write(json.dumps(test_plan, indent=2, sort_keys=True))

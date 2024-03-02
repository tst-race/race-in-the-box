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

# Python Library Imports
import logging
import datetime
import warnings
from opensearchpy import OpenSearch as Elasticsearch
from opensearchpy.exceptions import OpenSearchWarning as ElasticsearchWarning
from prettytable import PrettyTable
from typing import Optional, List, Tuple

# Local Python Library Imports
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import elasticsearch_utils

# Set up logger
logger = logging.getLogger(__name__)


###
# Types
###


###
# Get Messages
###


def get_matching_messages(
    rib_mode: str,
    deployment_name: str,
    recipient: Optional[str],
    sender: Optional[str],
    test_id: str = None,
    trace_id: str = None,
    date_from: str = None,
    date_to: str = None,
    sort_by: str = "Status",
    reverse_sort: bool = False,
    verbose: bool = False,
) -> Tuple[int, List[elasticsearch_utils.MessageTrace]]:
    """
    Purpose:
        Get matching messages from Elastic Search Instance, print if indicated. May return all messages in deployment.
    Args:
        rib_mode: mode that rib is in
        deployment_name: name of deployment (needs to be active)
        recipient: filter on given receiving node
        sender: filter on given sender node
        test_id: filter on given test_id
        trace_id: filter on given trace_id
        date_from: starting date for filter
        date_to: ending date for filter
        sort_by: how to sort printed table
        reverse_sort: flag to turn on reverse sorting table
        verbose: flag to turn on printing out table
    Return:
        messages_to_be_received: int -> count of number of messages in a non-received status
        output: List[message_traces] -> a returned list of all of the matching messages
    """
    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Elasticsearch service (for this deployment) needs to be up to get messages
    deployment.status.verify_deployment_is_active("get matching messages")

    date_range = []
    if date_from:
        date_exp = datetime.datetime.fromisoformat(date_from).timestamp() * 1000
        date_range.append(["gte", f"{date_exp}"])
    if date_to:
        date_exp = datetime.datetime.fromisoformat(date_to).timestamp() * 1000
        date_range.append(["lte", f"{date_exp}"])

    # Query Elasticsearch for send message spans
    warnings.filterwarnings("ignore", category=ElasticsearchWarning)
    es = Elasticsearch(
        deployment.get_elasticsearch_hostname(),
        timeout=120,
        max_retries=5,
        retry_on_timeout=True,
    )

    query = elasticsearch_utils.create_query(
        actions=["sendMessage", "receiveMessage"],
        trace_id=trace_id,
        time_range=date_range,
        range_name=deployment.get_range_name(),
    )
    results = elasticsearch_utils.do_query(es=es, query=query)
    spans = elasticsearch_utils.get_spans(es, results)
    (_, trace_id_to_span) = elasticsearch_utils.get_message_spans(spans)
    message_traces = elasticsearch_utils.getMessageTraces(trace_id_to_span)

    if verbose:
        PTables = PrettyTable()
        PTables.field_names = [
            "Trace ID",
            "Test ID",
            "Size",
            "Sender",
            "Recipient",
            "Status",
            "Start Time",
            "End Time",
            "Total Time (s)",
        ]

    output = []
    messages_to_be_received = 0

    for message in message_traces:
        span = message.get("send_span", message.get("receive_span"))
        if sender and span["messageFrom"] != sender:
            continue
        if recipient and span["messageTo"] != recipient:
            continue
        if test_id and span["messageTestId"] != test_id:
            continue
        # Current message is a part of our wanted matching subset
        output.append(message)
        if message["status"] != elasticsearch_utils.MessageStatus.RECEIVED:
            messages_to_be_received += 1
        # If user wants matched subset printed
        if verbose:
            # Prepare data
            starttime = "N/A"
            endtime = "N/A"
            if message.get("send_span"):
                starttime = datetime.datetime.fromtimestamp(
                    message["send_span"]["start_time"] / 1000000
                ).strftime("%Y-%m-%d %H:%M:%S")
            if message.get("receive_span"):
                endtime = datetime.datetime.fromtimestamp(
                    message["receive_span"]["start_time"] / 1000000
                ).strftime("%Y-%m-%d %H:%M:%S")
            # Add new row to the table
            PTables.add_row(
                [
                    span["trace_id"],
                    span["messageTestId"],
                    span["messageSize"],
                    span["messageFrom"],
                    span["messageTo"],
                    f"{message['status']}",
                    starttime,
                    endtime,
                    message.get("total_time"),
                ]
            )

    # Once all messages have been searched, print matched subset
    if verbose:
        if sort_by in PTables.field_names:
            PTables.sortby = sort_by
        else:
            logger.warn(f"Invalid column to sort by: {sort_by}")
            PTables.sortby = "Start Time"

        PTables.reversesort = reverse_sort
        print(PTables)

    return messages_to_be_received, output


def ui_get_matching_messages(
    rib_mode: str,
    deployment_name: str,
    size: int,
    recipient: Optional[str],
    sender: Optional[str],
    test_id: str = None,
    trace_id: str = None,
    date_from: str = None,
    date_to: str = None,
    reverse_sort: bool = False,
    search_after_vals: list = [],
) -> Tuple[List, List[elasticsearch_utils.MessageTraceUi], bool]:
    """
    Purpose:
        Get matching messages from Elastic Search Instance, print if indicated. May return all messages in deployment.
    Args:
        rib_mode: mode that rib is in
        deployment_name: name of deployment (needs to be active)
        size: total number of results expected per page
        recipient: filter on given receiving node
        sender: filter on given sender node
        test_id: filter on given test_id
        trace_id: filter on given trace_id
        date_from: starting date for filter
        date_to: ending date for filter
        reverse_sort: flag to turn on reverse sorting table
        search_after_vals: values used to run a search after query, for retrieving non first page results
    Return:
        search_after_return: List -> the elasticsearch sort value that is needed as "search_after_vals" input, to handle pagination of results
        output: List[message_traces] -> a returned list of all of the matching messages
        has_more_pages: bool -> the backend determined the current page of results is full and it is worth trying a next page
    """
    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Elasticsearch service (for this deployment) needs to be up to get messages
    deployment.status.verify_deployment_is_active("ui get matching messages")

    date_range = []
    if date_from:
        date_exp = datetime.datetime.fromisoformat(date_from).timestamp() * 1000
        date_range.append(["gte", f"{date_exp}"])
    if date_to:
        date_exp = datetime.datetime.fromisoformat(date_to).timestamp() * 1000
        date_range.append(["lte", f"{date_exp}"])

    # Query Elasticsearch for wanted message spans
    warnings.filterwarnings("ignore", category=ElasticsearchWarning)

    es = Elasticsearch(
        deployment.get_elasticsearch_hostname(),
        timeout=120,
        max_retries=5,
        retry_on_timeout=True,
    )

    query = elasticsearch_utils.create_message_list_query(
        actions=["sendMessage", "receiveMessage"],
        trace_id=trace_id,
        time_range=date_range,
        range_name=deployment.get_range_name(),
        search_after_vals=search_after_vals,
        sender=sender,
        recipient=recipient,
        test_id=test_id,
    )

    results = elasticsearch_utils.do_message_list_query(
        es=es, query=query, page_size=size, reverse_sort=reverse_sort
    )

    (
        spans,
        new_search_after_vals,
        has_more_pages,
    ) = elasticsearch_utils.get_message_list_spans(results, page_size=size)

    (_, trace_id_to_span) = elasticsearch_utils.get_message_spans_ui(spans)
    message_traces = elasticsearch_utils.get_message_traces_ui(trace_id_to_span)

    output = message_traces

    return new_search_after_vals, output, has_more_pages

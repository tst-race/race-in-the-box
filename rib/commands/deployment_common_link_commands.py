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
import click
import datetime
import logging
import warnings
from opensearchpy.exceptions import OpenSearchWarning as ElasticsearchWarning
from prettytable import PrettyTable
from typing import Optional

# Local Python Library Imports
from rib.commands.deployment_options import (
    deployment_name_option,
    pass_rib_mode,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import elasticsearch_utils

# Set up logger
logger = logging.getLogger(__name__)


###
# Get Link Command Group
###


@click.group("link")
def link_command_group() -> None:
    """Commands for getting link information"""


###
# Get Link Commands
###


@link_command_group.command("list")
@deployment_name_option("list links")
@click.option(
    "--node",
    "node",
    help="Filter on node",
    required=False,
    type=str,
)
@click.option(
    "--persona",
    help="Filter on link persona",
    required=False,
    type=str,
)
@click.option(
    "--sort-by",
    "sort_by",
    help="Sort the list on a column",
    required=False,
    type=str,
    default="Event Time",
)
@click.option(
    "--reverse-sort", "reverse_sort", flag_value=True, help="Reverse the sort"
)
@pass_rib_mode
def list_links(
    rib_mode: str,
    deployment_name: str,
    node: Optional[str],
    persona: Optional[str],
    sort_by: str = "Event Time",
    reverse_sort: bool = False,
):
    """
    Get Links of node
    """
    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Elasticsearch service (for this deployment) needs to be up to get messages
    deployment.status.verify_deployment_is_active("list messages for")

    # Getting Links
    warnings.filterwarnings("ignore", category=ElasticsearchWarning)
    qObj = elasticsearch_utils.ESLinkExtractor(
        deployment.get_elasticsearch_hostname()[0]
    )
    results = qObj.do_query(range_name=deployment.get_range_name())
    link_traces = qObj.extract_link_records(results)

    # Set up Output Table
    PTables = PrettyTable()
    PTables.field_names = [
        # "Trace ID",
        # "Span ID",
        # "Start Time Millis",
        "Channel ID",
        "Link ID",
        "Event Time",
        "Operation Name",
        "Node Name",
        "Personas",
        "Transmission Type",
        "Connection Type",
        "Send Type",
        "Reliable",
        "Link Direction",
        "Link Type",
        "Link Address",
    ]
    for link_trace in link_traces:
        if link_trace["operationName"] not in ["LINK_LOADED", "LINK_CREATED"]:
            continue

        if node and link_trace["serviceName"] != node:
            continue

        if persona and persona not in link_trace["personas"]:
            continue

        PTables.add_row(
            [
                # link_trace["traceID"],
                # link_trace["spanID"],
                # link_trace["startTimeMillis"],
                link_trace["channelGid"],
                link_trace["linkId"],
                datetime.datetime.fromtimestamp(
                    link_trace["startTimeMillis"] / 1000.0
                ).strftime("%Y-%m-%d %H:%M:%S"),
                link_trace["operationName"],
                link_trace["serviceName"],
                link_trace["personas"],
                link_trace["transmissionType"],
                link_trace["connectionType"],
                link_trace["sendType"],
                link_trace["reliable"],
                link_trace["linkDirection"],
                link_trace["linkType"],
                link_trace["linkAddress"],
            ]
        )
    if sort_by in PTables.field_names:
        PTables.sortby = sort_by
    else:
        logger.warn(f"Invalid column to sort by: {sort_by}")
        PTables.sortby = "Event Time"

    PTables.reversesort = reverse_sort
    print(PTables)

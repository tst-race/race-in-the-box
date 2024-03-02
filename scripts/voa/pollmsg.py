#!/usr/bin/python
#
# Run as watch -n 5 ....
#
# INTERVAL="1"
#
# tsstr=$(date -d "${INTERVAL} hour ago" "+%Y-%m-%d %H:%M:%S")
# tspad=" $tsstr "
#
# rib deployment message list --sort-by "End Time" --reverse-sort | head -23 | awk -v ts="$tspad" -F '[\|+]' \
#    '(NR<4) || ($9 > ts) {printf "|%s|%s|%s|%s|%s|%s|\n", $2, $3, $5, $6, $9, $10; print ""}' | sed -e '/^$/d'

import argparse
import pandas as pd
import datetime
from prettytable import PrettyTable
from opensearchpy import OpenSearchWarning

import warnings

warnings.filterwarnings(action="ignore", category=OpenSearchWarning)

from rib.utils import elasticsearch_utils
from rib.utils.link_graph_utils import (
    LinkGraph,
    LinkQueryMethod,
    LinkGraphRenderer,
    LinkGraphSerializer,
)


last_link_cache = {}

def pretty_print_table(spandict, show_na=False):
    PTables = PrettyTable()
    PTables.field_names = [
        "Trace ID",
        #"Test ID",
        #"Size",
        "Sender",
        "Recipient",
        #"Status",
        #"Start Time",
        "End Time",
        "Total Time (s)",
        "Force URL",
        "Jaeger URL",
    ]

    for trace_id in spandict:
        # if not show_na and spandict[trace_id]['endtime'] == "N/A":
        #     continue

        PTables.add_row(
            [
                trace_id,
                #spandict[trace_id]["messageTestId"],
                #spandict[trace_id]["messageSize"],
                spandict[trace_id]["messageFrom"],
                spandict[trace_id]["messageTo"],
                #spandict[trace_id]['status']",
                #spandict[trace_id]['starttime'],
                spandict[trace_id]['endtime'],
                spandict[trace_id]["total_time"],
                f"http://localhost:6080/?collapse=true&trace={trace_id}",
                f"http://localhost:16686/trace/{trace_id}",
            ]
        )
    PTables.sortby = "End Time"
    PTables.reversesort = True

    # Pretty-print the message list
    print(PTables.get_string(start=0, end=args.row_count))

def get_message_traces(es_host, date_range, range_name):
    qObj = elasticsearch_utils.ESLinkExtractor(es_host)
    query = qObj.create_query(
        actions=["sendMessage", "receiveMessage"],
        trace_ids=None,
        time_range=date_range,
        range_name=range_name,
    )
    results = qObj.do_query(query=query)
    spans = qObj.get_spans(results)
    (_, trace_id_to_span) = elasticsearch_utils.get_message_spans(spans)
    message_traces = elasticsearch_utils.getMessageTraces(trace_id_to_span)
    spandict = {}
    print(len(message_traces))
    idx = 1
    for message in message_traces:
        idx+=1
        # Prepare data
        starttime = "N/A"
        endtime = "N/A"
        span = message.get("send_span", message.get("receive_span"))
        if message.get("send_span"):
            starttime = datetime.datetime.fromtimestamp(
                message["send_span"]["start_time"] / 1000000
            ).strftime("%Y-%m-%d %H:%M:%S")
        if message.get("receive_span"):
            endtime = datetime.datetime.fromtimestamp(
                message["receive_span"]["start_time"] / 1000000
            ).strftime("%Y-%m-%d %H:%M:%S")
        currspan = {}
        currspan["messageTestId"] = span["messageTestId"]
        currspan["messageSize"] = span["messageSize"]
        currspan["messageFrom"] = span["messageFrom"]
        currspan["messageTo"] = span["messageTo"]
        currspan["status"] = f"{message['status']}"
        currspan["starttime"] = starttime
        currspan["endtime"] = endtime
        currspan["total_time"] = message.get("total_time")
        trace_id = span["trace_id"]

        # if span["messageFrom"] == "race-client-00001" and span["messageTo"] == "race-client-00002":
        #     # print("IGNORED")
        #     continue
        
        spandict[trace_id] = currspan
    return spandict


def fetch_path_graph(spandict, es_host, date_range, range_name):
    qObj = elasticsearch_utils.ESLinkExtractor(es_host)
    results = qObj.do_query(
        timeout=600,
        date_range=date_range,
        services=[],
        method=LinkQueryMethod.LINK_CURRENT,
        range_name=range_name,
    )
    if results:
        links = qObj.extract_link_records(results)
    else:
        links = []
    linkdf = pd.DataFrame(links)
    if not linkdf.empty:
        linkdf.sort_values(by=["startTimeMillis"], inplace=True)
    if len(linkdf) == 0:
        exit(0)

    # Convert returned records to a bipartite graph
    bip, _ = LinkGraph.linksToGraph(linkdf, method=LinkQueryMethod.LINK_CURRENT)

    # Convert to a projected representation
    fullG = LinkGraph.projectGraph(bip)

    # Fetch span information
    traceids = list(spandict.keys())
    path_graph = qObj.get_path_graph(traceids, range_name)

    # fullG.remove_edges_from(list(fullG.edges()))
    for traceId in path_graph:
        for (n1, n2, plugin, connection) in path_graph[traceId]:
            fullG.add_edge(n1, n2, traceId=traceId, traceConn=connection)

    return fullG


def main(args):
    if args.deployment_name:
        deployment = RibDeployment.get_existing_deployment_or_fail(
            args.deployment_name, args.rib_mode
        )
        es_host = deployment.get_elasticsearch_hostname()[0]
    else:
        es_host = args.es_endpoint

    date_range = [["gte", "now-30m/m"]]

    # Get all messages
    spandict = get_message_traces(es_host, date_range, args.range_name)

    pretty_print_table(spandict, args.show_na)

    # Render the graph
    render_endpoint = f"http://{args.renderer_endpoint}:6080/update"
    fullG = fetch_path_graph(spandict, es_host, date_range, args.range_name)
    LinkGraphSerializer.serialize_graph(fullG, None, render_endpoint)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Poll for messages",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--es-ip",
        dest="es_endpoint",
        default="elasticsearch",
        help="IP address for elasticsearch",
    )
    parser.add_argument(
        "--renderer-ip",
        dest="renderer_endpoint",
        default="graph_renderer",
        help="IP address for graph renderer",
    )
    parser.add_argument(
        "--show-na",
        dest="show_na",
        default=False,
        help="Show unarrived messages",
    )
    parser.add_argument(
        "--deployment",
        dest="deployment_name",
        type=str,
        default=None,
        help="Deployment name",
    )
    parser.add_argument(
        "--mode",
        dest="rib_mode",
        type=str,
        default="local",
        help="Deployment mode",
    )
    parser.add_argument(
        "--traceid",
        dest="traceid",
        type=str,
        default=None,
        help="Trace ID to query",
    )
    parser.add_argument(
        "--range",
        dest="range_name",
        choices=["sri-demo", "stealth-demo"],
        default=None,
        help="Range name for which to filter",
    )
    parser.add_argument(
        "--row-count",
        dest="row_count",
        type=int,
        default=21,
        help="Number of rows to display",
    )
    args = parser.parse_args()
    main(args)

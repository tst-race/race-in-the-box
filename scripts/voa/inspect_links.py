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
        Query Elasticsearch for link and connection artifacts,
        construct graphs over the returned data and assess/render
        such graphs.

    Example usage:

        # Return records within the given date range
        python inspect_links.py --host elasticsearch:9200 \\
                                --date-range "gte:now-8d/d" \\
                                --date-range "lte:now-5d/d" \\
                                --size 10

        # Return records associated with a particular race node
        python inspect_links.py --host elasticsearch:9200 \\
                                --service race-server-00001

        # Return all records and display some statistics over links
        python inspect_links.py --host elasticsearch:9200 \\
                                --stats

        # Save retrieved records to CSV file
        python inspect_links.py --host elasticsearch:9200 \\
                                --to-csv /path/to/data.csv

        # construct a graph representation of the links read from a csv file
        python inspect_links.py --from-csv /path/to/data.csv --to-csv /dev/null \\
            --layout "spring" --saveplotdir ./graphs
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms.distance_measures import eccentricity
import argparse

from rib.utils.link_graph_utils import (
    LinkGraph,
    LinkQueryMethod,
    LinkGraphRenderer,
    LinkGraphSerializer,
)
from rib.utils.elasticsearch_utils import ESLinkExtractor
from utils import ArgHelper


class InspectLinksArgHelper(ArgHelper):
    """
    Purpose:
        Helper class for inspect-links specific CLI argument parsing
    """

    def __init__(self):
        super(InspectLinksArgHelper, self).__init__()

        self.parser.add_argument(
            "--rollup",
            dest="roll_up",
            type=str,
            help="Rollup graph",
        )

        self.parser.add_argument(
            "--to-csv",
            dest="to_csv",
            type=argparse.FileType("w"),
            default="-",
            help="Output file",
        )


if __name__ == "__main__":
    argHelper = InspectLinksArgHelper()
    args = argHelper.get_cli_arguments()

    if args.from_csv:
        linkdf = pd.read_csv(args.from_csv, sep="|")
    else:
        qObj = ESLinkExtractor(args.es_host)
        results = qObj.do_query(
            timeout=args.timeout,
            date_range=args.date_range,
            services=args.services,
            method=args.method,
            range_name=args.range,
        )
        if results:
            links = qObj.extract_link_records(results)
        else:
            links = []
        linkdf = pd.DataFrame(links)
        print("Number of records returned:{}\n".format(len(linkdf)))
        if not linkdf.empty:
            linkdf.sort_values(by=["startTimeMillis"], inplace=True)

            # Write to file
            linkdf.to_csv(args.to_csv, sep="|", header=True, index=False)

    if len(linkdf) == 0:
        print("No results returned")
        exit(0)

    # Convert returned records to a bipartite graph
    bip, _ = LinkGraph.linksToGraph(linkdf, method=args.method)

    # Convert to a projected representation
    fullG = LinkGraph.projectGraph(bip)

    # Extract relevant sub-graphs
    dirG = LinkGraph.getDirectNetwork(fullG)
    indirG = LinkGraph.getIndirectNetwork(fullG)

    if args.show_stats:
        # Add stats corresponding to main graph
        LinkGraph.updateDirectStats(fullG, dirG)
        LinkGraph.updateIndirectStats(fullG, indirG)

        stats_df = LinkGraph.getStatsDataframe(fullG)
        print(stats_df.to_csv(sep="|"))

    if args.json_file or args.render_endpoint:
        LinkGraphSerializer.serialize_graph(fullG, args.json_file, args.render_endpoint)

    if args.save_plot_dir or args.show_plot:

        # If roll-up options are given generate that plot

        addedLinks = removedLinks = None
        colormap = {n: v for (n, v) in args.colormap}

        if args.roll_up:
            R = LinkGraph.rollUp(dirG, args.roll_up)
            gPlot = LinkGraphRenderer(R, colormap)
            gPlot.drawGraph(
                layout=args.layout,
                edge_attr=args.ref_edge_attr,
                showEdgeLabels=args.show_labels,
                showNodeLabels=args.show_labels,
                figsize=(10, 10),
            )
        else:
            gPlot = LinkGraphRenderer(fullG, colormap)
            gPlot.drawGraph(
                layout=args.layout,
                edge_attr=args.ref_edge_attr,
                showEdgeLabels=args.show_labels,
                showNodeLabels=args.show_labels,
                figsize=(10, 10),
                added=addedLinks,
                removed=removedLinks,
            )

        if args.save_plot_dir:
            plt.savefig(f"{args.save_plot_dir}/graph.png")

        if args.show_plot:
            plt.show()

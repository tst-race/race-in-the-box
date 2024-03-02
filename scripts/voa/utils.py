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
Supporting methods for link extraction and adversary agent behavior.

"""
import argparse
from typing import List, Any, Tuple, Optional
import subprocess
from opensearchpy import OpenSearch as Elasticsearch
from opensearchpy import OpenSearchException as ElasticsearchException
import pandas as pd
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import re
from time import sleep
from random import random
from pathlib import Path
import threading
from datetime import datetime

from rib.utils.link_graph_utils import (
    LinkGraph,
    LinkQueryMethod,
    LinkGraphRenderer,
    LinkGraphSerializer,
)
from rib.utils.elasticsearch_utils import ESLinkExtractor


class GraphPoller:
    """
    Purpose:
        Helper class that constructs a network graph elasticsearch or locally
        provided data, updates it based on adverary information, and serializes
        the resulting graph object for subsequent rendering.
    """

    def __init__(self, agentArgs: argparse.Namespace) -> None:
        """
        Purpose:
            Initialize the poller object

        Args:
            agentArgs: command line arguments
        """
        self.thread = threading.Thread(target=self._worker_loop, args=())
        self.args = agentArgs
        self.qObj = ESLinkExtractor(self.args.es_host)

        # A common lock to protect several members
        self.worker_lock = threading.Lock()
        self.full_graph = None
        self.serialized_graph = None
        self.attacked = set()
        self.thread_terminate = False
        (self.full_graph, _, self.initial_ts) = self._refresh_graph()

    def get_base_graph(self):
        """
        Purpose:
            Return the base graph representation

        """
        with self.worker_lock:
            if not self.full_graph or nx.is_empty(self.full_graph):
                return None
            P = LinkGraph.projectGraph(self.full_graph)
        return P

    def start_worker(self) -> None:
        """
        Purpose:
            Start the worker thread

        """
        self.thread.start()

    def stop_worker(self) -> None:
        """
        Purpose:
            Stop the worker thread
        """
        with self.worker_lock:
            self.thread_terminate = True
        self.thread.join()

    def _refresh_links(self, ts: int = None) -> None:
        """
        Purpose:
            Refresh links from elasticsearch

        Args:
            ts: the timestamp beyond which to fetch results
        """
        if not ts:
            date_range = self.args.date_range
        else:
            ts_str = datetime.fromtimestamp(ts / 1000.0)
            date_range = [["gt", f"{ts_str}"]]

        results = self.qObj.do_query(
            timeout=self.args.timeout,
            date_range=date_range,
            method=self.args.method,
            range_name=self.args.range,
        )
        if results:
            links = self.qObj.extract_link_records(results)
        else:
            links = []
        linkdf = pd.DataFrame(links)
        if not linkdf.empty:
            linkdf.sort_values(by=["startTimeMillis"], inplace=True)
        return linkdf

    def _extract_graph(self, linkdf: pd.DataFrame) -> Tuple[nx.MultiDiGraph, list, int]:
        """
        Purpose:
            Extract a graph representation from the provided dataframe

        Args:
            linkdf: a dataframe containing link information

        Returns:
            A tuple containing the graph, a list of links that were removed,
            and the timestamp for the last record in the dataframe used to
            generate the graph.
        """
        # Convert returned records to a graph using link information
        if linkdf.empty:
            return (None, None, None)
        G, removed_links = LinkGraph.linksToGraph(linkdf, method=self.args.method)
        last_ts = linkdf["startTimeMillis"].iloc[-1]
        return (G, removed_links, last_ts)

    def _refresh_graph(self, ts: int = None) -> Tuple[nx.MultiDiGraph, list, int]:
        """
        Purpose:
            Construct a graph based after refreshing link information

        Args:
            ts: the timestamp beyond which to fetch results

        Returns:
            A tuple containing the graph, a list of links that were removed,
            and the timestamp for the last record in the dataframe used to
            generate the graph.
        """
        if self.args.from_csv:
            with open(self.args.from_csv) as fp:
                linkdf = pd.read_csv(fp, sep="|")
                if ts:
                    linkdf = linkdf[linkdf["startTimeMillis"] > ts]
        else:
            linkdf = self._refresh_links(ts)
        if linkdf.empty:
            # return the current timestamp since we want to preserve what is
            # latest
            return (None, None, ts)
        return self._extract_graph(linkdf)

    def _get_filtered_graph(self, G: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """
        Purpose:
            Filter attacked nodes from the provided graph and return a new
            graph
        """
        with self.worker_lock:
            for n in self.attacked:
                if n in G:
                    G.remove_node(n)
        return G

    def update_attacked(
        self, node: str, new_suspects: List[str], plot_name: str
    ) -> nx.MultiDiGraph:
        """
        Purpose:
            Update list of attacked nodes and depict adversarial progression

        Args:
            node: the node that was attacked
            new_suspects: suspects inferred through association with node
            plot_name: if supplied, save attack progression to given file name

        Returns:
            The updated graph.
        """

        with self.worker_lock:
            newG = self.full_graph.copy()
        newG = self._get_filtered_graph(newG)

        # First display the attack progression if needed
        P = LinkGraph.projectGraph(newG)
        if self.args.save_plot_dir or self.args.show_plot:
            AgentHelper.draw_agent_graph(self.args, P, node, new_suspects, plot_name)

        # Next update the current graph representation
        with self.worker_lock:
            self.attacked.add(node)
        newG.remove_node(node)
        P = LinkGraph.projectGraph(newG)

        json_data = nx.json_graph.node_link_data(newG)
        curr_serialized = LinkGraphSerializer.get_serialized(json_data)
        with self.worker_lock:
            self.serialized_graph = curr_serialized

        return P

    def _worker_loop(self):
        """
        Purpose:
            Main worker loop for the poller
        """
        prev_cmp = None
        last_ts = self.initial_ts
        while True:
            with self.worker_lock:
                full_graph = self.full_graph.copy()

            # Get a serialized representation of the current graph
            curr_graph = self._get_filtered_graph(full_graph)
            json_data = nx.json_graph.node_link_data(curr_graph)
            curr_cmp = LinkGraphSerializer.get_serialized(json_data)

            # If serialized representation has changed, persist or send it along
            if not prev_cmp or curr_cmp != prev_cmp:
                prev_cmp = curr_cmp
                # Serialize the projected graph
                P = LinkGraph.projectGraph(curr_graph)
                LinkGraphSerializer.serialize_graph(
                    P, self.args.json_file, self.args.render_endpoint
                )

            # Look for termination condition
            with self.worker_lock:
                if self.thread_terminate:
                    break

            # wait for specified interval
            refresh_time = max(self.args.refresh, 0.0001)
            sleep(refresh_time)

            # refresh the graph if needed
            if self.args.refresh > 0:
                (
                    new_graph,
                    removed_links,
                    last_ts,
                ) = self._refresh_graph(ts=last_ts)

                with self.worker_lock:
                    if new_graph:
                        for (u, v, d) in LinkGraph.get_all_edges(new_graph):
                            if (u, v) in self.full_graph.edges():
                                self.full_graph[u][v]["conn"] += d["conn"]
                            else:
                                self.full_graph.add_edge(u, v, **d)
                            # Remove the link if there are no active connections
                            if self.full_graph[u][v]["conn"] <= 0:
                                removed_links.append((u, v))

                    if removed_links:
                        for (u, v) in removed_links:
                            if (u, v) in self.full_graph.edges():
                                self.full_graph.remove_edge(u, v)


class AgentHelper:
    """
    Purpose:
        Helper class for common adversary functions
    """

    FALSE_POSITIVE = "False-Suspect"

    @staticmethod
    def tryFollowEdge(
        graph: nx.MultiDiGraph, edge: Tuple[str, str], indirect_prob: float
    ) -> Optional[Tuple[str, str]]:
        """
        Purpose:
            Attempt to follow edge

        Args:
            graph: the network representation of nodes and edges
            edge: the edge under consideration
            indirect_prob: the probability of successfully following an indirect link

        Returns:
            The link that was followed if successful, or None otherwise
        """
        (u, v) = edge
        links = graph.get_edge_data(u, v).values()
        connTypes = list(set([l["connType"].pop() for l in links]))

        if LinkGraph.CONN_TYPE_DIRECT in connTypes:
            return edge

        elif LinkGraph.CONN_TYPE_INDIRECT in connTypes:
            if indirect_prob == 0.0:
                return None  # Fundamentally not following indirect

            # Probabilistically succeed at finding the other endpoint
            print("Trying an indirect link")
            if random() < indirect_prob:
                print(f"...succeeded - {edge}")
                return edge
            else:
                print(f"...false positive - {edge}")
                return (AgentHelper.FALSE_POSITIVE,)

    @staticmethod
    def followEdges(
        graph: nx.MultiDiGraph, node: str, indirect_prob: float = 0.0
    ) -> List[str]:
        """
        Purpose:
            Iteratively follow edges

        Args:
            graph: the network representation of nodes and edges
            node: the attack target
            indirect_prob: the probability of successfully following an indirect link

        Returns:
            The nodes that were reachable from the given node after adversarial
            action
        """
        suspects = set()
        processed = set()
        for edge in list(graph.in_edges(node)) + list(graph.out_edges(node)):
            # Don't attempt to reach the same node through multiple links
            (u, v) = edge
            other_node = u if u != node else v
            if other_node in processed:
                continue
            processed.add(other_node)
            # Check if the link can be followed
            followed = AgentHelper.tryFollowEdge(graph, edge, indirect_prob)
            if followed:
                suspects.update(
                    [other_node for other_node in followed if other_node != node]
                )

        return suspects

    @staticmethod
    def shutdownNode(deployment_name: str, node: str) -> None:
        """
        Purpose:
            Perform a shutdown operation on a node

        Args:
            deployment_name: the name of the deployment
            node: the attack target
        """
        cmd = f"/usr/local/bin/rib deployment local stop --name={deployment_name} --node={node}".split()
        print(cmd)
        subprocess.call(cmd)

    @staticmethod
    def draw_agent_graph(
        args,
        graph: nx.MultiDiGraph,
        node: str = None,
        new_nodes: List[str] = None,
        plot_name: str = "graph",
    ):
        """
        Purpose:
            Render the current graph of nodes and edges

        Args:
            graph: the current graph representation
            node: the attack target
            new_nodes: the additional targets reachable from node
            plot_name: the file name for the generated plot
        """
        colormap = {n: v for (n, v) in args.colormap}

        removed_edges = []
        attack_graph = graph.copy()
        # Remove all edges except the ones relating to the attacked nodes
        # and any new suspects
        if node:
            all_edges = LinkGraph.get_all_edges(graph)
            removed_edges = [
                (e[0], e[1])
                for e in all_edges
                if (node not in e) or (e[0] not in new_nodes and e[1] not in new_nodes)
            ]
            attack_graph.remove_edges_from(removed_edges)

            # If all edges are removed don't generate a plot
            if nx.is_empty(attack_graph):
                return

        gPlot = LinkGraphRenderer(attack_graph, colormap)
        gPlot.drawGraph(
            layout=args.layout,
            edge_attr=args.ref_edge_attr,
            showEdgeLabels=args.show_labels,
            showNodeLabels=args.show_labels,
            figsize=(10, 10),
            added=None,
            removed=removed_edges,
        )

        if args.save_plot_dir:
            Path(args.save_plot_dir).mkdir(parents=True, exist_ok=True)
            plt.savefig(f"{args.save_plot_dir}/{plot_name}.png")

        if args.show_plot:
            # plt.show()
            # plt.draw()
            plt.pause(0.001)
            input("Press [enter] to continue.")


class ArgHelper:
    """
    Purpose:
        Helper class for CLI argument parsing
    """

    ARG_CONNECTION_EVER = "conn-ever"
    ARG_CONNECTION_CURRENT = "conn-current"
    ARG_LINK_EVER = "link-ever"
    ARG_LINK_CURRENT = "link-current"

    @staticmethod
    def methodToType(arg_method: str) -> LinkQueryMethod:
        if arg_method == ArgHelper.ARG_CONNECTION_EVER:
            return LinkQueryMethod.CONNECTION_EVER
        elif arg_method == ArgHelper.ARG_CONNECTION_CURRENT:
            return LinkQueryMethod.CONNECTION_CURRENT
        elif arg_method == ArgHelper.ARG_LINK_CURRENT:
            return LinkQueryMethod.LINK_CURRENT
        elif arg_method == ArgHelper.ARG_LINK_EVER:
            return LinkQueryMethod.LINK_EVER
        raise argparse.ArgumentTypeError("Unknown LinkQueryMethod type")

    @staticmethod
    def colon_sep_tuple(value: str) -> list:
        """Convert a string representation of the date range a list

        Parameters
        ----------
        value:string
            A string of the form "name:value"

        Returns
        -------
        list
            A list consisting of the [name,value] pair

        Raises
        ------
        argparse.ArgumentTypeError
            If the given string is not of the expected form
        """
        dateparam = value.split(":")
        if len(dateparam) != 2:
            raise argparse.ArgumentTypeError(
                f"{value} should be of the form name: value"
            )
        return dateparam

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Query elasticsearch for link artifacts",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        self.parser.add_argument(
            "--host",
            dest="es_host",
            default="elasticsearch",
            help="Elasticsearch IP address[:port]",
        )

        self.parser.add_argument(
            "--timeout", dest="timeout", default=60, help="Search timeout"
        )

        self.parser.add_argument(
            "--size", dest="res_size", type=int, default=-1, help="Result size"
        )

        self.parser.add_argument(
            "--date-range",
            action="append",
            dest="date_range",
            type=ArgHelper.colon_sep_tuple,
            default=[],
            help="""
            Date range parameter formatted as "<date-parm>:<date-math>".
            For details on the possible values for date-param and date-math see
            https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-range-query.html
            """,
        )

        self.parser.add_argument(
            "--service",
            action="append",
            dest="services",
            default=[],
            help="Service (node) name to match",
        )

        self.parser.add_argument(
            "--method",
            dest="method",
            choices=[
                ArgHelper.ARG_CONNECTION_EVER,
                ArgHelper.ARG_CONNECTION_CURRENT,
                ArgHelper.ARG_LINK_EVER,
                ArgHelper.ARG_LINK_CURRENT,
            ],
            default=ArgHelper.ARG_LINK_CURRENT,
            help="Type of edges to process",
        )

        self.parser.add_argument(
            "--range",
            default=None,
            help="Range name for which to filter",
        )

        self.parser.add_argument(
            "--from-csv",
            dest="from_csv",
            # type=argparse.FileType("r"),
            type=str,
            default=None,
            help="Input file",
        )

        self.parser.add_argument(
            "--stats",
            dest="show_stats",
            action="store_true",
            help="Display node statistics",
        )

        self.parser.add_argument(
            "--json",
            dest="json_file",
            type=str,
            default=None,
            help="Graph JSON output file name",
        )

        self.parser.add_argument(
            "--render",
            dest="render_endpoint",
            type=str,
            default="http://graph_renderer:6080/update",
            help="Graph rendering endpoint",
        )

        self.parser.add_argument(
            "--saveplotdir",
            dest="save_plot_dir",
            type=str,
            default=None,
            help="Graph output file name directory",
        )

        self.parser.add_argument(
            "--showlabels",
            dest="show_labels",
            action="store_true",
            help="Display node and edge labels",
        )

        self.parser.add_argument(
            "--showplot",
            dest="show_plot",
            action="store_true",
            help="Show graph",
        )

        self.parser.add_argument(
            "--layout",
            dest="layout",
            type=str,
            help="""
            Specify layout of the graph as one of "spiral", "spring", "dot",
            "fdp", "sfdp", "neato", "bipartite", or "circular".
            """,
        )

        self.parser.add_argument(
            "--edgeattr",
            dest="ref_edge_attr",
            type=str,
            default="channelGid",
            help="Edge attribute to display",
        )

        self.parser.add_argument(
            "--colormap",
            action="append",
            dest="colormap",
            type=ArgHelper.colon_sep_tuple,
            default=[],
            help="Specify a color for a particular edge attribute value",
        )

    def get_cli_arguments(self) -> argparse.Namespace:
        """Parse command line arguments

        Returns
        -------
        argparse.Namespace
            a namespace comprising of parsed arguments

        """
        args = self.parser.parse_args()

        # Fix the method type
        args.method = ArgHelper.methodToType(args.method)

        return args

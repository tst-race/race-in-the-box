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
    Handle Graphing the Links of a RACE Run

Example Usage:

from rib.utils.elasticsearch_utils import ESLinkExtractor
from rib.utils.link_graph_utils import LinkGraph, LinkGraphRenderer
import pandas as pd

qObj = ESLinkExtractor("elasticsearch")
results = qObj.do_query(timeout=200, date_range=[["gte", "now-1h/h"]])
links = qObj.extract_link_records(results)
df = pd.DataFrame(links)

bip, _ = LinkGraph.linksToGraph(df)
G = LinkGraph.projectGraph(bip)
I = LinkGraph.getIndirectNetwork(G)
D = LinkGraph.getDirectNetwork(G)

LinkGraph.updateIndirectStats(G, I)
LinkGraph.updateDirectStats(G, D)
stats = LinkGraph.getStatsDataframe(G)

rollup1_max = stats.iloc[stats['D_maxdepth'].idxmax()]['Node']

R = LinkGraph.rollUp(D, rollup1_max)

attrcolormap = {"twoSixDirectCpp": "red", "twoSixIndirectCpp": "green"}
gPlot = LinkGraphRenderer(R, attrcolormap)
gPlot.drawGraph(layout="spring", showNodeLabels=False, figsize=(25, 25))
"""


# Imports
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms import bipartite
import pandas as pd
import re
import json
import requests
from collections import defaultdict
from itertools import cycle
from networkx.algorithms.distance_measures import eccentricity
from typing import List, Any, Tuple, Optional
from rib.utils.elasticsearch_utils import LinkQueryMethod


class LinkGraph:
    """
    A class that provides convenience routines for link graph manipulation
    """

    # Some definitions
    CONN_TYPE_DIRECT = "CT_DIRECT"
    CONN_TYPE_INDIRECT = "CT_INDIRECT"
    CONN_TYPE_ATTR = "connType"

    @staticmethod
    def linksToGraph(
        df: pd.DataFrame, method: LinkQueryMethod = LinkQueryMethod.LINK_CURRENT
    ) -> Tuple[nx.MultiDiGraph, List[Tuple[str, str]]]:
        """Convert links within a dataframe to a graph representation

        Parameters
        ----------

        df:pd.DataFrame
            A dataframe of records returned from a previous do_query() operation
        method:LinkQueryMethod
            The type of links to use in the creation of the graph

        Returns
        -------
        nx.MultiDiGraph: a tuple consisting of a directed graph and any
            removed links.  The directed graph of links
            contains the following link attributes:
            "connType": The connection type
            "channelGid": The channel identifier
            "linkAddress": The link address
        removed_links: list of edges that were removed from the graph
        """

        createOps = []
        destroyOps = []
        if method == LinkQueryMethod.CONNECTION_EVER:
            createOps = ["CONNECTION_OPEN"]
        elif method == LinkQueryMethod.CONNECTION_CURRENT:
            createOps = ["CONNECTION_OPEN"]
            destroyOps = ["CONNECTION_CLOSED", "LINK_DESTROYED"]
        elif method == LinkQueryMethod.LINK_EVER:
            createOps = ["LINK_CREATED", "LINK_LOADED"]
        elif method == LinkQueryMethod.LINK_CURRENT:
            createOps = ["LINK_CREATED", "LINK_LOADED"]
            destroyOps = ["LINK_DESTROYED"]
        else:
            raise Exception("Unknown link method")

        G = nx.DiGraph()
        edgeattrs = defaultdict(lambda: defaultdict(set))

        extant_links = {}
        connection_counts = defaultdict(lambda: defaultdict(int))
        removed_links = []
        bip_attrs = {}
        for idx, row in df.fillna("").iterrows():
            reqd_fields = [
                "operationName",
                "serviceName",
                "connectionType",
                "linkType",
                "channelGid",
                "linkId",
                "linkAddress",
            ]

            # Skipping CONNECTION_SEND and CONNECTION_RECV because we do not
            # use them and they are missing some fields, causing lots of
            # spurious error messages
            if row["operationName"] in {"CONNECTION_SEND", "CONNECTION_RECV"}:
                continue

            # Ensure that we have all required fields
            if not (all(key in row and row[key] != "" for key in reqd_fields)):
                if row["operationName"] != "LINK_DESTROYED":
                    print(f"Ignoring malformed record at index {idx}")
                    continue

            src = row["serviceName"]
            connType = row["connectionType"]
            linkType = row["linkType"]
            linkId = row["linkId"]
            linkAddress = row["linkAddress"]
            channelGid = row["channelGid"]

            # Add optional fields
            if "personas" in row:
                personas = row["personas"]
            else:
                personas = ""

            pNode = f"{channelGid}|{linkAddress}"

            addLink = False

            if row["operationName"] in createOps:
                addLink = True
                # Increment connection counts
                if row["operationName"] == "CONNECTION_OPEN":
                    connection_counts[linkAddress][src] += 1

            elif destroyOps and row["operationName"] in destroyOps:
                if row["operationName"] == "CONNECTION_CLOSED":
                    addLink = True
                    # Decrement connection counts
                    connection_counts[linkAddress][src] -= 1
                elif row["operationName"] == "LINK_DESTROYED":
                    removed_links.append(linkId)

            if linkType in ["LT_SEND", "LT_BIDI"]:
                if addLink:
                    G.add_edge(
                        src,
                        pNode,
                        pKey=pNode,
                        connType=connType,
                        linkType=linkType,
                        linkId=linkId,
                        linkAddress=linkAddress,
                        channelGid=channelGid,
                        personas=personas,
                        conn=connection_counts[linkAddress][src],
                    )

            if linkType in ["LT_RECV", "LT_BIDI"]:
                if addLink:
                    G.add_edge(
                        pNode,
                        src,
                        pKey=pNode,
                        connType=connType,
                        linkType=linkType,
                        linkId=linkId,
                        linkAddress=linkAddress,
                        channelGid=channelGid,
                        personas=personas,
                        conn=connection_counts[linkAddress][src],
                    )

            if addLink:
                G.nodes[src]["bipartite"] = 0
                G.nodes[pNode]["bipartite"] = 1

        nx.set_node_attributes(G, bip_attrs, "bipartite")
        del_edges = [
            (u, v) for u, v, d in G.edges(data=True) if d["linkId"] in removed_links
        ]
        G.remove_edges_from(del_edges)
        return G, []

    @staticmethod
    def projectGraph(G):
        # Create a map of bipartite keys to edge tuples
        bEdges = defaultdict(list)
        for u, v, d in G.edges(data=True):
            bEdges[d["pKey"]].append((u, v, d))

        P = nx.MultiDiGraph()
        bNodes = {n for n, d in G.nodes(data=True) if d["bipartite"] == 0}
        B = bipartite.projected_graph(G, bNodes, multigraph=True)
        for u, v, k in B.edges(keys=True):
            attrs = defaultdict(set)
            # Re-insert the bipartite edge attributes using the key as the index
            for b_u, b_v, d in bEdges[k]:
                attrs["connType"].add(d["connType"])
                attrs["linkType"].add(d["linkType"])
                attrs["linkId"].add(d["linkId"])
                attrs["linkAddress"].add(d["linkAddress"])
                attrs["channelGid"].add(d["channelGid"])
                attrs["personas"].add(d["personas"])

                base_node = b_u if b_u != k else b_v
                if base_node == u:
                    attrs["conn_out"] = d["conn"]
                elif base_node == v:
                    attrs["conn_in"] = d["conn"]
            P.add_edge(u, v, **attrs)
        return P

    @staticmethod
    def get_all_edges(G: nx.MultiDiGraph) -> list:
        """Return a list of all (in and out) edges for a directed graph

        Parameters
        ----------
        G: nx.MultiDiGraph
            A directed graph

        """
        # in_edges = [(u, v, e) for u, v, e in G.in_edges(data=True)]
        out_edges = [(u, v, e) for u, v, e in G.out_edges(data=True)]
        # return in_edges + out_edges
        return out_edges

    @staticmethod
    def extractGraphWithType(
        G: nx.MultiDiGraph, attrname: str, attrvalue: str
    ) -> nx.MultiDiGraph:
        """Extract graph with links matching a given attribute name/value

        Parameters
        ----------

        attrname:str
            attribute name

        attrvalue: str
            Attribute value to match

        """
        edges = LinkGraph.get_all_edges(G)
        sel_edges = [(u, v, e) for u, v, e in edges if attrvalue == e[attrname]]
        H = nx.MultiDiGraph(sel_edges)
        return H

    @staticmethod
    def getIndirectNetwork(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Extract the sub-graph consisting of only indirect links

        Parameters
        ----------
        G: nx.MultiDiGraph
           A directed graph containing indirect links

        """
        H = LinkGraph.extractGraphWithType(
            G, LinkGraph.CONN_TYPE_ATTR, LinkGraph.CONN_TYPE_INDIRECT
        )
        return H

    @staticmethod
    def getDirectNetwork(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Extract the sub-graph consisting of only directed links

        Parameters
        ----------
        G: nx.MultiDiGraph
            A directed graph containing direct links

        """

        H = LinkGraph.extractGraphWithType(
            G, LinkGraph.CONN_TYPE_ATTR, LinkGraph.CONN_TYPE_DIRECT
        )
        return H

    @staticmethod
    def updateIndirectStats(G: nx.MultiDiGraph, H: nx.MultiDiGraph, pfx=""):
        """Get statistics associated with indirect links

        Update the node properties in graph G with statistics computed over graph H.
        The following statistics are gathered:

        - node indegree

        Parameters
        ----------
        G: nx.MultiDiGraph
            The graph where node properties are to be updated

        H: nx.MultiDiGraph
            The graph over which statistics are computed

        pfx: str
            A prefix string to be appended to the property name
        """

        if nx.is_empty(H):
            return

        # Flatten the edges of the multi-digraph
        H_flat = nx.DiGraph(H)

        stats = dict(H_flat.in_degree)
        nx.set_node_attributes(G, stats, f"I_{pfx}indegree")

    @staticmethod
    def updateDirectStats(
        G: nx.MultiDiGraph, H: nx.MultiDiGraph, pfx: str = ""
    ) -> pd.DataFrame:
        """Get statistics associated with direct links

        Update the node properties in graph G with stats computed over graph H.

        The following statistics are gathered:

        - maxdepth - for each node, the number of hops needed to reach the
           farthest node when traversing a sequence of direct links.
        - descendents - for each node, the number of nodes reachable via
          traversing a sequence of direct links.

        Parameters
        ----------
        G: nx.MultiDiGraph
            The graph where node properties are to be updated

        H: nx.MultiDiGraph
            The graph over which statistics are computed

        pfx: str
            A prefix string to be appended to the property name
        """

        if nx.is_empty(H):
            return

        # Flatten the edges of the multi-digraph
        H_flat = nx.DiGraph(H)

        # descendants
        stats = defaultdict(dict)
        for n in H_flat.nodes:
            g = nx.bfs_tree(H_flat, n)
            stats[n][f"D_{pfx}maxdepth"] = eccentricity(g, n)
            # Do not include head in the list of descendants
            stats[n][f"D_{pfx}descendants"] = g.number_of_nodes() - 1
        nx.set_node_attributes(G, stats)

    @staticmethod
    def getStatsDataframe(G: nx.MultiDiGraph):
        """Convert node statistics to a dataframe

        Parameters
        ----------
        G: nx.MultiDiGraph
            The graph containing node properties
        """

        nodes = dict(G.nodes(data=True))
        statsdf = (
            pd.DataFrame.from_dict(nodes, orient="index")
            .rename_axis("Node")
            .reset_index()
        )
        return statsdf

    @staticmethod
    def rollUp(H: nx.MultiDiGraph, startNode: str) -> nx.MultiDiGraph:
        """Roll-up the network from a given start node

        Parameters
        ----------
        H: nx.MultiDiGraph
            A directed (sub-)graph originating from the given
            startNode obtained by traversing direct links.

        startNode:str
            The name of the starting node

        """

        if nx.is_empty(H) or startNode not in H:
            # return an empty di-graph
            return nx.MultiDiGraph()

        D = nx.bfs_tree(H, startNode)

        # preserve any node and edge properties
        remove = [e for e in H.edges() if e not in D.edges()]
        H_copy = H.copy()
        H_copy.remove_edges_from(remove)
        return H_copy

    @staticmethod
    def getDelta(G: nx.MultiDiGraph, G_ref: nx.MultiDiGraph) -> Tuple[list, list, list]:
        """Compute difference between two graphs

        Parameters
        ----------

        G: nx.MultiDiGraph
            A directed graph

        G_ref: nx.MultiDiGraph
            The directed graph against which to compare

        Returns
        -------
        Two lists, the first containing added edges and the second
        containing removed edges
        """

        edges = LinkGraph.get_all_edges(G)
        ref_edges = LinkGraph.get_all_edges(G_ref)
        added = [item for item in edges if item not in ref_edges]
        removed = [item for item in ref_edges if item not in edges]
        return added, removed


class LinkGraphRenderer:
    """
    A class that provides supporting functions for graph rendering
    """

    # defaults
    FIGSIZE = (8, 8)
    CLIENT_NAME_PFX = "race-client-"
    CLIENT_NODE_COLOR = "blue"
    SERVER_NODE_COLOR = "lightgreen"

    def __init__(self, G: Any, attrcolormap: dict):
        """
        Parameters
        ----------

        G: a DiGraph or a MultiDiGraph
            The graph structure

        attrcolormap: dict
            A dictionary of edge attribute name to color mappings
        """

        self.G = G
        self.attrcolormap = attrcolormap
        self.coloriter = cycle(["r", "g", "c"])

    def toMultiDiGraph(self, attrname: str) -> nx.MultiDiGraph:
        """Construct a multi-digraph based on a given edge attribute

        Parameters
        ----------

        attrname: str
            The edge attribute name

        Returns
        -------
        A MultiDiGraph consisting of edges associated with the given edge attribute type

        """

        # Create a dict from attribute value to links
        edges = LinkGraph.get_all_edges(self.G)
        etypes = defaultdict(list)
        for u, v, e in edges:
            attrval = e[attrname]
            for attr in attrval:
                etypes[attr].append((u, v, e))

        M = nx.MultiDiGraph()
        for attrval in etypes:
            # Sort the list to preserve some consistency in the colors used
            M.add_edges_from(
                # sort the dict portion if the item by the connType
                sorted(list(etypes[attrval]), key=lambda x: x[2]["connType"]),
                color=self._getEdgeColor(attrval),
                label=attrval,
            )
        return M

    def _getEdgeColor(self, attrval: str):
        """
        Convenience routine to get color from the colormap
        or a default color if no mapping exists
        """

        if attrval in self.attrcolormap:
            return self.attrcolormap[attrval]

        # Cycle through some default colors by default
        return next(self.coloriter)

    def _getLayoutPos(self, layout: str, clientGrpPrefix: str):
        """
        Convenience routine to the node positions for a given layout.
        If the layout is "bipartite" then clientGrpPrefix specifies
        the regex that identifies the nodes belonging to the first group.
        """

        if layout == "spiral":
            pos = nx.spiral_layout(self.G)
        elif layout == "spring":
            pos = nx.spring_layout(self.G)
        # Following are graphviz layouts
        elif layout == "dot":
            pos = nx.nx_pydot.graphviz_layout(self.G, prog="dot", root=None)
        elif layout == "fdp":
            pos = nx.nx_pydot.graphviz_layout(self.G, prog="fdp", root=None)
        elif layout == "sfdp":
            pos = nx.nx_pydot.graphviz_layout(self.G, prog="sfdp", root=None)
        elif layout == "neato":
            pos = nx.nx_pydot.graphviz_layout(self.G, prog="neato", root=None)
        elif layout == "bipartite":
            pattern = re.compile(clientGrpPrefix)
            client_nodes = [n for n in self.G.nodes if pattern.match(n)]
            pos = nx.drawing.layout.bipartite_layout(self.G, client_nodes)
        else:
            # Default is circular
            pos = nx.circular_layout(self.G)
        return pos

    def drawGraph(
        self,
        layout: str = "spring",
        edge_attr: str = "channelGid",
        showNodeLabels: bool = True,
        showEdgeLabels: bool = False,
        figsize: tuple = FIGSIZE,
        grpPfx: str = "race-client-",
        added: list = None,
        removed: list = None,
    ):
        """Plot a graph

        Parameters
        ----------

        layout: str
            The layout to use (can be one of "spiral", "spring", "dot",
            "fdp", "sfdp", "neato", "bipartite", or "circular"

        edge_attr: str
            The edge attribute that defines the relationships between nodes.

        showNodeLabels: bool
            A flag to enable the display of node labels

        showEdgeLabels: bool
            A flag to enable the display of edge labels

        figsize: tuple
            A tuple that specifies the width and height of the plotted canvas

        grpPfx: str
            A regex string that identifies the nodes belonging to the first
            category in a bipartite layout (only useful for bipartite layouts)

        added: list
            A set of links that are to be highlighted as added links

        removed: list
            A set of links that are to be highlighted as removed links
        """

        plt.figure(figsize=figsize)
        pos = self._getLayoutPos(layout, grpPfx)
        M = self.toMultiDiGraph(edge_attr)

        edge_labels = defaultdict(set)

        for (u, v, _), attr in nx.get_edge_attributes(M, "label").items():
            edge_labels[(u, v)].add(attr)
        edge_colors = nx.get_edge_attributes(M, "color").values()

        node_colors = [
            LinkGraphRenderer.CLIENT_NODE_COLOR
            if n.startswith(LinkGraphRenderer.CLIENT_NAME_PFX)
            else LinkGraphRenderer.SERVER_NODE_COLOR
            for n in M
        ]

        nx.draw(
            M,
            pos,
            with_labels=showNodeLabels,
            edge_color=edge_colors,
            node_color=node_colors,
        )
        if showEdgeLabels and edge_labels:
            _ = nx.draw_networkx_edge_labels(M, pos, edge_labels=edge_labels)
        if added:
            _ = nx.draw_networkx_edges(M, pos, edgelist=added, width=3)

        if removed:
            _ = nx.draw_networkx_edges(
                M,
                pos,
                edgelist=removed,
                width=0.1,
            )


class LinkGraphSerializer:
    @staticmethod
    def _set_default(obj):
        """Helper for serializing set type"""
        if isinstance(obj, set):
            return list(obj)
        raise TypeError

    @staticmethod
    def serialize_graph(G, json_file=None, render_endpoint=None):
        json_data = nx.json_graph.node_link_data(G)
        serialized = LinkGraphSerializer.get_serialized(json_data)
        LinkGraphSerializer.do_serialize(serialized, json_file, render_endpoint)

    @staticmethod
    def get_serialized(json_data):
        serialized = json.dumps(json_data, default=LinkGraphSerializer._set_default)
        return serialized

    @staticmethod
    def do_serialize(serialized, json_file=None, render_endpoint=None):
        if json_file:
            with open(json_file, "w") as fp:
                fp.write(serialized)
        if render_endpoint:
            response = requests.post(render_endpoint, data=serialized)
            if not response.ok:
                print(f"Posting to {render_endpoint} failed")

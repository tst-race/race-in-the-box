# VoA scripts

This directory contains scripts and modules that support Voice of the Adversary (VoA) analysis operations.

This file provides a brief overview of the capabilities. Additional details can be found on the [Wiki page](https://wiki.race.twosixlabs.com/display/RACE2/VoA+Agent+Tool)

## The graph renderer

The graph_renderer component located in /race-in-the-box/scripts/voa/graph_renderer enables the RACE network that is the subject of adversarial action to be rendered on a web browser. The graph_renderer module is a simple containerized Flask/D3 web-application that provides a REST end-point where the VoA agent can submit serialized graph representations for display. The graph_renderer  persists graph objects that are sent to it. A web-browser can can pointed to the root web-page being served by the graph_renderer  in order view the latest graph that was submitted by the VoA agent. The web-page polls for changes to the graph periodically and updates the graph if it has changed.

### Building and running

```
rib:2.1.2@code# cd /race-in-the-box/scripts/voa/graph_renderer
rib:2.1.2@code# ./docker-build.sh
rib:2.1.2@code# ./docker-run.sh
```

Within RiB, the graph_renderer can be accessed at http://renderer:6080/. The following parameters can be specified in the url:

* linkattr : The information to display on edges. The following values are supported
* connType: Whether CT_DIRECT, CT_INDIRECT, etc
* linkType: Whether LT_SEND, LT_RECEIVE, etc
* linkId: The link ID
* linkAddress: The link address used to establish linkage between the nodes
* channelGid: The channel identifier
* personas: The personas that this link refers to
* conn_out: The number of outward connection requests
* conn_in: The number of inward connection requests (note, that this value is common across all inbound links. That is, if a node has two inbound links the count value is the same for all inbound links)
* refreshtime : The number of milliseconds to wait before each page refresh
* collapse : If true collapse multiple links between two nodes into a single link; if false (default) display the directed multi-graph
* labels : If true (default) display labels on edges; if false  no not display edge labels.


The REST endpoint where graph updates can be posted is located at  http://renderer:6080/update/. A JSON representation for the payload that can be processed by the graph renderer is provided below:

```
{
   "directed" : true,
   "graph" : {},
   "links" : [
      {
         "channelGid" : "twoSixDirectCpp",
         "connType" : "CT_DIRECT",
         "conn_in" : 0,
         "conn_out" : 0,
         "key" : 0,
         "linkAddress" : "{\"hostname\":\"race-server-00002\",\"port\":20000}",
         "linkId" : "PluginCommsTwoSixStub/twoSixDirectCpp/LinkID_3",
         "linkType" : "LT_RECV",
         "personas" : "race-server-00003, race-server-00001",
         "source" : "race-server-00003",
         "target" : "race-server-00002"
      },
      {
         "channelGid" : "twoSixDirectCpp",
         "connType" : "CT_DIRECT",
         "conn_in" : 0,
         "conn_out" : 0,
         "key" : 0,
         "linkAddress" : "{\"hostname\":\"race-server-00003\",\"port\":20001}",
         "linkId" : "PluginCommsTwoSixStub/twoSixDirectCpp/LinkID_3",
         "linkType" : "LT_RECV",
         "personas" : "race-server-00002, race-server-00004",
         "source" : "race-server-00002",
         "target" : "race-server-00003"
      }
   ],
   "multigraph" : true,
   "nodes" : [
      {
         "id" : "race-server-00003"
      },
      {
         "id" : "race-server-00002"
      }
   ]
}
```


## The `inspect_links.py` script

### Example script usage


Gather links and save to file

```
rib:2.1.2@code# python /race_in_the_box/scripts/voa/inspect_links.py --host elasticsearch --date-range "gte:now-1d/d" --method conn-ever --to-csv links.csv

rib:2.1.2@code# head -2 links.csv
traceID|spanID|operationName|startTimeMillis|linkId|channelGid|linkAddress|personas|linkType|transmissionType|connectionType|sendType|reliable|linkDirection|serviceName|connectionId|size
4075e17cca12a97e|4075e17cca12a97e|LINK_LOADED|1654267662508|PluginCommsTwoSixStub/twoSixIndirectCpp/LinkID_0|twoSixIndirectCpp|"{""checkFrequency"":1000,""hashtag"":""cpp_clients_30"",""hostname"":""twosix-whiteboard"",""port"":5000,""timestamp"":-1.0}"|race-server-00003|LT_BIDI|TT_MULTICAST|CT_INDIRECT|ST_STORED_ASYNC|false|LD_BIDI|race-client-00003||
```

Read links from file and generate a PNG of the graph representation

```
rib:2.1.2@code# python /race_in_the_box/scripts/voa/inspect_links.py --layout "spring" --saveplotdir ./ --showlabels --edgeattr channelGid --method conn-ever --from-csv ./links.csv
```

Read links from file, attempt to roll-up the network from a given starting node and create a PNG of the resulting graph
```
rib:2.1.2@code# python /race_in_the_box/scripts/voa/inspect_links.py --from-csv ./links.csv --layout "spring" --saveplotdir ./ --showlabels --edgeattr channelGid --rollup race-server-00001
```

Read links from file and render the graph representation on a browser (note: we assume that the graph render has already been started up)
```
rib:2.1.2@code# python /race_in_the_box/scripts/voa/inspect_links.py --method conn-ever --from-csv links.csv --render http://renderer:6080/update
```

## The `agent_walker.py` script


### Overview

The VoA agent tool enables one to automate adversarial actions within a RACE network. The basic idea is that an agent traverses a RACE network and performs some adversarial action on each node traversed. This enables one to evaluate the ability of the RACE network to remain resilient against adversarial action, and the efficacy of specific countermeasures that are invoked  as part of network manager behavior.

The input to the VoA agent tool is a set of link and/or connection records corresponding to a given RACE deployment. These records can be either obtained in real-time by querying the Elasticsearch instance that is provisioned as part of a RACE deployment, or can be be provided through a CSV file that was created using the inspect_links.py script. The type of information that will be retrieved can be controlled using the --method  option. Using method type of link-ever or link-current results in the retrieval of fewer records; it also means that doing so results in some of the connection-level details getting excluded from analysis results.

Once the list of records have been acquired, the VoA agent converts this information into a graph overlay representation, where linkages between nodes are created based on the shared use of a link addresses within a given RACE channel. This overlay representation forms the starting point for adversarial actions. The list of records used to construct the graph can be refreshed periodically using the --refresh option. The fetch operation is performed asynchronously as part of another thread.

The VoA agent starts at a random node and attempts to build a list of suspected RACE nodes reachable through it. It is assumed that direct links can trivially enumerated; consequently the list of suspected RACE nodes will always include nodes reachable through direct links. For indirect links, it is assumed that enumeration of peer nodes can only occur with some probability of success ( --indirect-prob ) and in other cases would only result in bad suspects or false positives, in which case no other traversal through that indirect link is possible.

The current state of the RACE network under adversarial actions can be serialized in one of two ways:

A json representation of the graph can be written to a file (See the --json option)
A json representation of the graph can be sent to a graph renderer listening at a given location via an HTTP POST operation (See the –render option)
In addition, a visual representation of the attack progression as a sequence of images can also be generated using the --saveplotdir  option or displayed to screen using the --showplot  option. Other options control the type of information and the level of detail that included in these images (see the --showlabels , --layout , --edgeattr  options)

The only adversarial action implemented currently is the node shutdown operation, although the tool can be extended to support other adversarial commands using relevant  rib deployment voa subcommands. The adversarial actions can also be invoked in a dry-run fashion using the --dry-run option, where the effect of adversarial actions on the link associations can be explored without actually invoking the rib deployment actions. If the --dry-run option is not supplied, the deployment where adversarial action is to be invoked must be specified using the --deployment option.

By default the agent traverses nodes within a given RACE deployment in an automated manner. The interval between each action can be controlled through the --action-time  parameter. It is also possible to invoke the agent actions interactively, using the --interrupt option.

### Sample invocation

Perform an VoA agent traversal starting from a random server node and only following direct links. Generate PNG images illustrating the traversal options at each step.

```
rib:2.1.2@code# python /race_in_the_box/scripts/voa/agent_walker.py --from-csv links.csv --interrupt --refresh=0 --indirect-prob=0.0 --dry-run --saveplotdir ./agent-graphs --showlabels

Attacking race-server-00004
Press Enter to continue
Suspects reachable from race-server-00004: {'race-server-00003', 'race-server-00001'}

Attacking race-server-00003
Press Enter to continue
Suspects reachable from race-server-00003: {'race-server-00005', 'race-server-00001', 'race-server-00002'}

Attacking race-server-00001
Press Enter to continue
Suspects reachable from race-server-00001: {'race-server-00005', 'race-server-00002'}

Attacking race-server-00002
Press Enter to continue
Suspects reachable from race-server-00002: {'race-server-00005'}

Attacking race-server-00005
Press Enter to continue
Suspects reachable from race-server-00005: set()
Ran out of suspects. Done.
The following graphs are generated in the agent-graphs  directory
```

Perform an VoA agent traversal starting from a random server node following direct links where ever encountered, and indirect links with a probability of 0.25. Also render the residual RACE network on a web browser as different nodes are targeted.

```
rib:2.1.2@code# python /race_in_the_box/scripts/voa/agent_walker.py --from-csv links.csv --interrupt --refresh=0 --indirect-prob=0.25 --render http://renderer:6080/update --dry-run

Attacking race-client-00003
Press Enter to continue
Trying an indirect link
...false positive - ('race-server-00004', 'race-client-00003')
Trying an indirect link
...false positive - ('race-server-00004', 'race-client-00003')
Trying an indirect link
...false positive - ('race-server-00003', 'race-client-00003')
Trying an indirect link
...false positive - ('race-server-00003', 'race-client-00003')
Trying an indirect link
...succeeded - ('race-client-00003', 'race-server-00003')
Trying an indirect link
...false positive - ('race-client-00003', 'race-server-00003')
Trying an indirect link
...false positive - ('race-client-00003', 'race-server-00004')
Trying an indirect link
...false positive - ('race-client-00003', 'race-server-00004')
Suspects reachable from race-client-00003: {'False-Suspect', 'race-server-00003'}

Attacking False-Suspect
Press Enter to continue
Attacked a bad suspect

Attacking race-server-00003
Press Enter to continue
Suspects reachable from race-server-00003: {'race-server-00001', 'race-server-00005', 'race-server-00002', 'race-server-00004'}

Attacking race-server-00001
Press Enter to continue
Trying an indirect link
...false positive - ('race-client-00002', 'race-server-00001')
Trying an indirect link
...false positive - ('race-client-00002', 'race-server-00001')
Trying an indirect link
...false positive - ('race-client-00001', 'race-server-00001')
Trying an indirect link
...false positive - ('race-client-00001', 'race-server-00001')
Trying an indirect link
...false positive - ('race-server-00001', 'race-client-00002')
Trying an indirect link
...false positive - ('race-server-00001', 'race-client-00002')
Trying an indirect link
...false positive - ('race-server-00001', 'race-client-00001')
Trying an indirect link
...succeeded - ('race-server-00001', 'race-client-00001')
Suspects reachable from race-server-00001: {'race-server-00005', 'race-server-00002', 'race-server-00004', 'False-Suspect', 'race-client-00001'}

Attacking race-server-00005
Press Enter to continue
Trying an indirect link
...false positive - ('race-client-00002', 'race-server-00005')
Trying an indirect link
...succeeded - ('race-client-00002', 'race-server-00005')
Trying an indirect link
...false positive - ('race-client-00001', 'race-server-00005')
Trying an indirect link
...false positive - ('race-client-00001', 'race-server-00005')
Trying an indirect link
...false positive - ('race-server-00005', 'race-client-00002')
Trying an indirect link
...false positive - ('race-server-00005', 'race-client-00002')
Trying an indirect link
...false positive - ('race-server-00005', 'race-client-00001')
Trying an indirect link
...false positive - ('race-server-00005', 'race-client-00001')
Suspects reachable from race-server-00005: {'False-Suspect', 'race-client-00002', 'race-server-00002'}

Attacking race-server-00002
Press Enter to continue
Trying an indirect link
...false positive - ('race-client-00002', 'race-server-00002')
Trying an indirect link
...false positive - ('race-client-00002', 'race-server-00002')
Trying an indirect link
...succeeded - ('race-client-00001', 'race-server-00002')
Trying an indirect link
...false positive - ('race-client-00001', 'race-server-00002')
Trying an indirect link
...false positive - ('race-server-00002', 'race-client-00002')
Trying an indirect link
...false positive - ('race-server-00002', 'race-client-00002')
Trying an indirect link
...false positive - ('race-server-00002', 'race-client-00001')
Trying an indirect link
...succeeded - ('race-server-00002', 'race-client-00001')
Suspects reachable from race-server-00002: {'False-Suspect', 'race-client-00001'}

Attacking race-server-00004
Press Enter to continue
Suspects reachable from race-server-00004: set()

Attacking False-Suspect
Press Enter to continue
Attacked a bad suspect

Attacking race-client-00002
Press Enter to continue
Suspects reachable from race-client-00002: set()

Attacking race-client-00001
Press Enter to continue
Suspects reachable from race-client-00001: set()
Ran out of suspects. Done.
```

### Extensibility

The VoA Agent Tool serves as a template against which other adversarial actions can be modeled. The main VoA agent driver code extracted from /race-in-the-box/scripts/voa/agent_walker.py is shown below.

```
 1      cur_suspects = {start_node}
 2      attacked = set()
 3      step = 1
 4      while True:
 5          pending_suspects = set()
 6          for node in cur_suspects:
 7              if node in attacked:
 8                  continue
 9
10              print(f"\nAttacking {node}")
11              if args.interrupt:
12                  input("Press Enter to continue")
13
14              if node == AgentHelper.FALSE_POSITIVE:
15                  print("Attacked a bad suspect")
16                  continue
17
18              # Current node is a viable target
19              attacked.add(node)
20
21              # attempt to enumerate nodes based on links
22              new_suspects = AgentHelper.followEdges(
23                  refG, node, indirect_prob=args.indirect_prob
24              ).difference(attacked)
25              pending_suspects.update(new_suspects)
26              print(f"Suspects reachable from {node}: {new_suspects}")
27
28              # Perform next action
29              if not args.dry_run:
30                  AgentHelper.shutdownNode(args.deployment_name, node)
31
32              # Wait to model adversarial analysis window
33              sleep(args.action_time)
34
35              # Update attack graph
36              plot_name = f"attack_{step}_{node}"
37              refG = poller.update_attacked(node, new_suspects, plot_name)
38
39              step += 1
40
41          cur_suspects = pending_suspects
42          if all([s == AgentHelper.FALSE_POSITIVE for s in cur_suspects]):
43              print("Ran out of suspects. Done.")
44              break
```

The algorithm is fairly simple in that the agent selects from a current list of suspects, given some starting state, and progressively attempts to identify new nodes that are reachable from that node (lines 21-26). For every node that is targeted, the agent shuts down that node (line 30) and continues on after some delay (line 33) that models the degree of adversarial "work" required to analyze the current list of suspects for subsequent adversarial action.

Network managers are encouraged to modify the basic agent flow above and create new agent driver modules that explore other types of adversarial behavior, including the use of different stopping or propagation criteria. Additionally, the edge attributes in the graph representation of the RACE network ( refG  in line 37) also include relevant channel and link attributes. These may be used as additional selectors to build agent models that follow specific types of edges based on their perceived difficulty to exploit.

## Module usage

Utilities for querying Elasticsearch and rendering graphs can be found under `/race-in-the-box/rib/utils`. The following code illustrates use of some of the relevant functions.

```
#!/usr/bin/env python3

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
```
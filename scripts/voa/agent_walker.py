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

	A simple adversarial agent that traverses a RACE network through known
	links and performs basic adversarial actions on nodes that are visited.

    Starting the renderer

	This script can be used alongside the renderer component that depicts
        the network as it changes the sequence of adversarial actions.

        The renderer container can be build and run as follows

        $ graph_renderer/docker-build.sh
        $ graph_renderer/docker-run.sh


    Example usage:

	# Build a network representation from elasticsearch for a given date
	# range, traverse only direct links (--indirect-prob=0.0), prompt the
	# user before taking any adversarial action (--interrupt), pause for
	# some time before taking the next adversarial action (--action-time=5)
	# and send graph information to the renderer.

	python ./agent_walker.py \
                    --deployment=voa-demo \
                    --host 127.0.0.1:9200 \
                    --date-range "gte:now-1d/d" \
                    --indirect-prob=0.0 \
                    --action-time=5 \
                    --interrupt \
                    --render http://renderer:5000/update

	# Build a network representation from a CSV file, previously generated
	# through the inspect_links.py script, traverse direct and indirect
	# links (with some probability), do not actually
	# invoke adversarial action (--dry-run) on traversed node
	# and send graph information to the renderer.

	python ./agent_walker.py \
                    --from-csv links.csv \
                    --indirect-prob=0.1 \
                    --interrupt \
                    --dry-run \
                    --render http://renderer:5000/update

"""

from rib.utils.link_graph_utils import LinkGraph
from time import sleep
from random import random
import pandas as pd
import argparse

from utils import ArgHelper, AgentHelper, GraphPoller

import warnings

warnings.filterwarnings("ignore")


class AgentWalkerArgHelper(ArgHelper):
    """
    Purpose:
        Helper class for agent-walker specific CLI argument parsing
    """

    def __init__(self):
        super(AgentWalkerArgHelper, self).__init__()

        self.parser.add_argument(
            "--refresh",
            dest="refresh",
            type=int,
            default=5,
            help="Set the periodicity of link gathering operations",
        )

        self.parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Do not actually invoke adversarial action",
        )

        self.parser.add_argument(
            "--action-time",
            dest="action_time",
            type=float,
            default=1.0,
            help="Time between adversary actions",
        )

        self.parser.add_argument(
            "--interrupt",
            dest="interrupt",
            action="store_true",
            help="Wait for user input before continuing",
        )

        self.parser.add_argument(
            "--deployment",
            dest="deployment_name",
            type=str,
            default=None,
            help="",
        )

        self.parser.add_argument(
            "--indirect-prob",
            dest="indirect_prob",
            type=float,
            default=0.0,
            help="Probability of successfully following an indirect link, 0.0 triggers special behavior to always start from a server and not try to follow indirect links",
        )


if __name__ == "__main__":
    argHelper = AgentWalkerArgHelper()
    args = argHelper.get_cli_arguments()
    poller = GraphPoller(args)

    # Fetch the initial graph
    refG = poller.get_base_graph()
    if not refG:
        print("No results returned")
        exit(0)

    # Start the polling loop
    poller.start_worker()

    if args.save_plot_dir or args.show_plot:
        AgentHelper.draw_agent_graph(args, refG, plot_name="complete-graph")

    # Determine potential starting nodes
    if args.indirect_prob == 0.0:
        potential_starts = [node for node in refG.nodes() if "server" in node]
    else:
        potential_starts = list(refG.nodes())

    if len(potential_starts) == 0:
        print("No starting node available")
        exit(0)

    start_node = potential_starts[int(random() * len(potential_starts))]
    cur_suspects = {start_node}
    attacked = set()
    step = 1
    while True:
        pending_suspects = set()
        for node in cur_suspects:
            if node in attacked:
                continue

            print(f"\nAttacking {node}")
            if args.interrupt:
                input("Press Enter to continue")

            if node == AgentHelper.FALSE_POSITIVE:
                print("Attacked a bad suspect")
                continue

            # Current node is a viable target
            attacked.add(node)

            # attempt to enumerate nodes based on links
            new_suspects = AgentHelper.followEdges(
                refG, node, indirect_prob=args.indirect_prob
            ).difference(attacked)
            pending_suspects.update(new_suspects)
            print(f"Suspects reachable from {node}: {new_suspects}")

            # Perform next action
            if not args.dry_run:
                AgentHelper.shutdownNode(args.deployment_name, node)

            # Wait to model adversarial analysis window
            sleep(args.action_time)

            # Update attack graph
            plot_name = f"attack_{step}_{node}"
            refG = poller.update_attacked(node, new_suspects, plot_name)

            step += 1

        cur_suspects = pending_suspects
        if all([s == AgentHelper.FALSE_POSITIVE for s in cur_suspects]):
            print("Ran out of suspects. Done.")
            break

    poller.stop_worker()

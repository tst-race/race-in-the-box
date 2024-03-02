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
    The help command group is reponsible for printing help documents for rib commands and topics
"""

# Python Library Imports
import click
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from typing import Iterable

# Local Python Library Imports
import rib.commands as rib_commands
from rib.utils import error_utils


command_groups = {
    "Common Deployment Commands": {
        "deployment start": {
            "description": rib_commands.deployment_common_commands.start.__doc__,
            "markdown": "reference/deployment/start.md",
        },
        "deployment stop": {
            "description": rib_commands.deployment_common_commands.stop.__doc__,
            "markdown": "reference/deployment/stop.md",
        },
        "deployment status": {
            "description": rib_commands.deployment_common_status_commands.status_all.__doc__,
            "markdown": "reference/deployment/status.md",
        },
        "deployment status app": {
            "description": rib_commands.deployment_common_status_commands.status_app.__doc__,
            "markdown": "reference/deployment/status/app.md",
        },
        "deployment status containers": {
            "description": rib_commands.deployment_common_status_commands.status_containers.__doc__,
            "markdown": "reference/deployment/status/containers.md",
        },
        "deployment status services": {
            "description": rib_commands.deployment_common_status_commands.status_services.__doc__,
            "markdown": "reference/deployment/status/services.md",
        },
        "deployment bootstrap node": {
            "description": rib_commands.deployment_common_bootstrap_commands.bootstrap_node.__doc__,
            "markdown": "reference/deployment/bootstrap/node.md",
        },
        "deployment message send-manual": {
            "description": rib_commands.deployment_common_message_commands.send_manual.__doc__,
            "markdown": "reference/deployment/message/send-manual.md",
        },
        "deployment message send-auto": {
            "description": rib_commands.deployment_common_message_commands.send_auto.__doc__,
            "markdown": "reference/deployment/message/send-auto.md",
        },
        "deployment message send-plan": {
            "description": rib_commands.deployment_common_message_commands.send_plan.__doc__,
            "markdown": "reference/deployment/message/send-plan.md",
        },
        "deployment message list": {
            "description": rib_commands.deployment_common_message_commands.list_messages.__doc__,
            "markdown": "reference/deployment/message/list.md",
        },
        "deployment set-timezone": {
            "description": rib_commands.deployment_common_commands.set_timezone.__doc__,
            "markdown": "reference/deployment/set-timezone.md",
        },
        "deployment bridged android prepare": {
            "description": rib_commands.deployment_common_bridged_commands.prepare_android.__doc__,
            "markdown": "reference/deployment/bridged/android/prepare.md",
        },
        "deployment bridged android connect": {
            "description": rib_commands.deployment_common_bridged_commands.connect_android.__doc__,
            "markdown": "reference/deployment/bridged/android/connect.md",
        },
        "deployment bridged android disconnect": {
            "description": rib_commands.deployment_common_bridged_commands.disconnect_android.__doc__,
            "markdown": "reference/deployment/bridged/android/disconnect.md",
        },
        "deployment bridged android unprepare": {
            "description": rib_commands.deployment_common_bridged_commands.unprepare_android.__doc__,
            "markdown": "reference/deployment/bridged/android/unprepare.md",
        },
        "deployment config generate": {
            "description": rib_commands.deployment_common_config_commands.generate.__doc__,
            "markdown": "reference/deployment/config/generate.md",
        },
        "deployment config tar": {
            "description": rib_commands.deployment_common_config_commands.tar_configs.__doc__,
            "markdown": "reference/deployment/config/tar.md",
        },
        "deployment config publish": {
            "description": rib_commands.deployment_common_config_commands.publish_configs.__doc__,
            "markdown": "reference/deployment/config/publish.md",
        },
        "deployment config install": {
            "description": rib_commands.deployment_common_config_commands.install_configs.__doc__,
            "markdown": "reference/deployment/config/install.md",
        },
        "deployment logs backup": {
            "description": rib_commands.deployment_common_logs_commands.backup_logs.__doc__,
            "markdown": "reference/deployment/logs/backup.md",
        },
        "deployment logs delete": {
            "description": rib_commands.deployment_common_logs_commands.delete_logs.__doc__,
            "markdown": "reference/deployment/logs/delete.md",
        },
        "deployment logs rotate": {
            "description": rib_commands.deployment_common_logs_commands.rotate_logs.__doc__,
            "markdown": "reference/deployment/logs/rotate.md",
        },
        "deployment reset": {
            "description": rib_commands.deployment_common_commands.reset.__doc__,
            "markdown": "reference/deployment/reset.md",
        },
        "deployment clear": {
            "description": rib_commands.deployment_common_commands.clear.__doc__,
            "markdown": "reference/deployment/clear.md",
        },
        "deployment test integrated": {
            "description": rib_commands.deployment_common_test_commands.integrated.__doc__,
            "markdown": "reference/deployment/test/integrated.md",
        },
        "deployment test comms-channel": {
            "description": rib_commands.deployment_common_test_commands.comms_channel.__doc__,
            "markdown": "reference/deployment/test/comms-channel.md",
        },
        "deployment test generate-plan": {
            "description": rib_commands.deployment_common_test_commands.generate_plan.__doc__,
            "markdown": "reference/deployment/test/generate-plan.md",
        },
    },
    "Local Environment & Deployment Commands": {
        "deployment local create": {
            "description": rib_commands.deployment_local_commands.create.__doc__,
            "markdown": "reference/deployment/local/create.md",
        },
        "deployment local up": {
            "description": rib_commands.deployment_local_commands.up.__doc__,
            "markdown": "reference/deployment/local/up.md",
        },
        "deployment local down": {
            "description": rib_commands.deployment_local_commands.down.__doc__,
            "markdown": "reference/deployment/local/down.md",
        },
        "env local capabilities": {
            "description": rib_commands.env_local_commands.capabilities.__doc__,
            "markdown": "reference/env/local/capabilities.md",
        },
        "env local info": {
            "description": rib_commands.env_local_commands.info.__doc__,
            "markdown": "reference/env/local/info.md",
        },
        "env local status": {
            "description": rib_commands.env_local_commands.status.__doc__,
            "markdown": "reference/env/local/status.md",
        },
    },
    "AWS Environment & Deployment Commands": {
        "aws topology by-instance-count": {
            "description": rib_commands.aws_topology_commands.create_by_instance_count.__doc__,
            "markdown": "reference/aws/topology/by-instance-count.md",
        },
        "aws topology by-node-resource-requirements": {
            "description": rib_commands.aws_topology_commands.create_by_node_resource_requirements.__doc__,
            "markdown": "reference/aws/topology/by-node-resource-requirements.md",
        },
        "aws topology by-nodes-per-instance": {
            "description": rib_commands.aws_topology_commands.create_by_nodes_per_instance.__doc__,
            "markdown": "reference/aws/topology/by-nodes-per-instance.md",
        },
        "env aws list": {
            "description": rib_commands.env_aws_commands.list_envs.__doc__,
            "markdown": "reference/env/aws/list.md",
        },
        "env aws active": {
            "description": rib_commands.env_aws_commands.active.__doc__,
            "markdown": "reference/env/aws/active.md",
        },
        "env aws create": {
            "description": rib_commands.env_aws_commands.create.__doc__,
            "markdown": "reference/env/aws/create.md",
        },
        "env aws info": {
            "description": rib_commands.env_aws_commands.info.__doc__,
            "markdown": "reference/env/aws/info.md",
        },
        "env aws provision": {
            "description": rib_commands.env_aws_commands.provision.__doc__,
            "markdown": "reference/env/aws/provision.md",
        },
        "env aws runtime-info": {
            "description": rib_commands.env_aws_commands.runtime_info.__doc__,
            "markdown": "reference/env/aws/runtime-info.md",
        },
        "env aws status": {
            "description": rib_commands.env_aws_commands.status.__doc__,
            "markdown": "reference/env/aws/status.md",
        },
        "env aws unprovision": {
            "description": rib_commands.env_aws_commands.unprovision.__doc__,
            "markdown": "reference/env/aws/unprovision.md",
        },
        "env aws remove": {
            "description": rib_commands.env_aws_commands.remove.__doc__,
            "markdown": "reference/env/aws/remove.md",
        },
        "env aws rename": {
            "description": rib_commands.env_aws_commands.rename.__doc__,
            "markdown": "reference/env/aws/rename.md",
        },
        "env aws copy": {
            "description": rib_commands.env_aws_commands.copy.__doc__,
            "markdown": "reference/env/aws/copy.md",
        },
        "deployment aws create": {
            "description": rib_commands.deployment_aws_commands.create.__doc__,
            "markdown": "reference/deployment/aws/create.md",
        },
        "deployment aws up": {
            "description": rib_commands.deployment_aws_commands.up.__doc__,
            "markdown": "reference/deployment/aws/up.md",
        },
        "deployment aws down": {
            "description": rib_commands.deployment_aws_commands.down.__doc__,
            "markdown": "reference/deployment/aws/down.md",
        },
    },
    "Configuration Commands": {
        "github config": {
            "description": rib_commands.github_commands.config.__doc__,
            "markdown": "reference/github/config.md",
        }
    },
}


all_guides = {
    "kit-source": {
        "description": "Kit source syntax",
        "markdown": "general/kit-source.md",
    },
    "local-deployments": {
        "description": "How to create and setup local deployments",
        "markdown": "how-to/deployment-setup/local-deployments.md",
    },
    "local-deployments": {
        "description": "How to create and setup local deployments",
        "markdown": "how-to/deployment-setup/local-deployments.md",
    },
    "android-bridged": {
        "description": "How to use bridged Android devices in a deployment",
        "markdown": "how-to/deployment-setup/android-bridged.md",
    },
    "android-docker": {
        "description": "How to use Docker-based Android devices in a deployment",
        "markdown": "how-to/deployment-setup/android-in-docker.md",
    },
    "manual-deployment-test": {
        "description": "Manual deployment integration testing",
        "markdown": "how-to/manual-deployment-test.md",
    },
    "auto-deployment-test": {
        "description": "Automated deployment integration testing",
        "markdown": "how-to/automated-deployment-test.md",
    },
    "node-bootstrap-test": {
        "description": "Node bootstrap testing",
        "markdown": "how-to/node-bootstrap-test.md",
    },
    "voa-test": {
        "description": "Voice-of-the-Adversary testing",
        "markdown": "how-to/voa-test.md",
    },
    "artifact-manager-test": {
        "description": "Artifact manager testing",
        "markdown": "how-to/deployment-setup/artifact-manager-deployments.md",
    },
    "bootstrap-verification": {
        "description": "Verifying bootstrap tests",
        "markdown": "how-to/test-verification/bootstrapping.md",
    },
    "message-receipt": {
        "description": "Verifying message receipt manually",
        "markdown": "how-to/test-verification/message-receipt.md",
    },
    "message-verification": {
        "description": "Verifying message receipt automatically",
        "markdown": "how-to/test-verification/message-verification.md",
    },
    "message-receipt-android": {
        "description": "Verifying message receipt on Android",
        "markdown": "how-to/test-verification/message-receipt-android.md",
    },
    "aws-integration": {
        "description": "Highlights of support for AWS within RiB",
        "markdown": "general/RiB-With-AWS.md",
    },
    "aws-prerequisites": {
        "description": "Setup prerequisites in order to use AWS",
        "markdown": "general/aws-prerequisites.md",
    },
    "aws-deployments": {
        "description": "How to create and setup AWS deployments",
        "markdown": "how-to/deployment-setup/aws-deployments.md",
    },
    "aws-audit": {
        "description": "Auditing and managing AWS usage",
        "markdown": "how-to/audit-and-manage-aws.md",
    },
    "aws-resource-calc": {
        "description": "Calculating AWS resource requirements",
        "markdown": "how-to/deployment-setup/calculating-aws-resource-requirements.md",
    },
    "gpu-deployments": {
        "description": "How to create and setup local deployments with GPU support",
        "markdown": "how-to/deployment-setup/gpu-deployments.md",
    },
}


@click.command("help")
@click.argument(
    "target",
    metavar="[COMMAND|GUIDE]",
    nargs=-1,
)
@click.option(
    "-a",
    "--all",
    flag_value=True,
    help=(
        "Prints all the available commands on the standard output. This option "
        "overrides any given command or guide name."
    ),
)
@click.option(
    "-g",
    "--guides",
    flag_value=True,
    help=(
        "Prints a list of useful guides on the standard output. This option "
        "overrides any given command or guide name."
    ),
)
def print_help(all: bool, guides: bool, target: Iterable[str]):
    """
    Display help information about RiB

    With no options and no COMMAND or GUIDE given, the synopsis of the rib
    command and a list of the most commonly used RiB commands are printed on the
    standard output.

    If the option --all or -a is given, all available commands are printed on
    the standard output.

    If the option --guide or -g is given, a list of the useful RiB guides is
    also printed on the standard output.

    If a command, or a guide, is given, documentation for that command or guide
    is printed on the standard output.
    """
    os.environ["MANPAGER"] = "less -r"
    console = Console()
    with console.pager(styles=True):
        if all:
            console.print(
                "See 'rib help <command>' to read about a specific subcommand"
            )

            for group_name, group in command_groups.items():
                console.print(f"\n{group_name}")
                grid = Table.grid(padding=(0, 0, 0, 4), pad_edge=True)
                grid.add_column()
                grid.add_column()
                for command_name, command in group.items():
                    grid.add_row(command_name, command["description"].strip())
                console.print(grid)

        elif guides:
            console.print("See 'rib help <guide>' to read a specific guide\n")

            grid = Table.grid(padding=(0, 0, 0, 4), pad_edge=True)
            for guide_name, guide in all_guides.items():
                grid.add_row(guide_name, guide["description"].strip())
            console.print(grid)

        else:
            target_name = " ".join(target)
            target_doc = None
            if target_name in all_guides:
                target_doc = all_guides[target_name]
            else:
                for group in command_groups.values():
                    if target_name in group:
                        target_doc = group[target_name]
                        break

            if not target_doc:
                raise error_utils.RIB006(f"No command or guide found: {target_name}")

            md_file = os.path.join(
                "/race_in_the_box/documentation", target_doc["markdown"]
            )
            if not os.path.exists(md_file):
                raise error_utils.RIB006(
                    f"Markdown file not found: {target_doc['markdown']}"
                )

            with open(md_file, "r") as md_file_in:
                console.print(Markdown(md_file_in.read()))

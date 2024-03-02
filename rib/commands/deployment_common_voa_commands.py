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
        deployments for invoking VoA commands
"""

# Python Library Imports
import click
from typing import Callable, List, Optional

# Local Python Library Imports
from rib.commands.deployment_options import (
    deployment_name_option,
    pass_rib_mode,
    nodes_option,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.commands.option_group import GroupedOptionCommand
from rib.utils.voa_utils import VoaRule
from rib.utils import error_utils

# Local Python Library Imports
from rib.commands.deployment_voa_options import (
    voa_duration_options,
    voa_rule_options,
    voa_delete_options,
)


###
# VoA Command Groups
###


@click.group("voa")
def deployment_voa_command_group() -> None:
    """
    Commands related to VoA actions. All VoA configuration changes
    that are applied through these commands are ephemeral and are
    not persisted across node restart operations.
    """


@deployment_voa_command_group.group("add")
def voa_add_command_group() -> None:
    """Commands for adding VoA rules"""


###
# VoA Commands
###


@voa_add_command_group.command("drop", cls=GroupedOptionCommand)
@deployment_name_option(action="voa add drop rule")
@pass_rib_mode
@nodes_option("invoke VoA drop action on")
@voa_rule_options
def add_rule_drop(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
    **rule: VoaRule,
):
    """
    Add drop rule
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.add_voa_rule(nodes=nodes, rule_action="drop", **rule)


@voa_add_command_group.command("delay", cls=GroupedOptionCommand)
@deployment_name_option(action="voa add delay rule")
@pass_rib_mode
@nodes_option("invoke VoA delay action on")
@voa_rule_options
@voa_duration_options
def add_rule_delay(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
    **rule: VoaRule,
):
    """
    Add delay rule
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.add_voa_rule(nodes=nodes, rule_action="delay", **rule)


@voa_add_command_group.command("tamper", cls=GroupedOptionCommand)
@deployment_name_option(action="voa add tamper rule")
@pass_rib_mode
@nodes_option("invoke VoA tamper action on")
@voa_rule_options
@click.option(
    "--iterations",
    "iterations",
    required=False,
    default="10",
    show_default=True,
    help="The number of times a random byte is corrupted.",
)
def add_rule_tamper(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
    **rule: VoaRule,
):
    """
    Add tamper rule
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.add_voa_rule(nodes=nodes, rule_action="tamper", **rule)


@voa_add_command_group.command("replay", cls=GroupedOptionCommand)
@deployment_name_option(action="voa add replay rule")
@pass_rib_mode
@nodes_option("invoke VoA replay action on")
@voa_rule_options
@voa_duration_options
@click.option(
    "--replay-times",
    "replay_times",
    required=False,
    default="3",
    show_default=True,
    help="The number of times a package needs to be replayed",
)
def add_rule_replay(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
    **rule: VoaRule,
):
    """
    Add replay rule
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.add_voa_rule(nodes=nodes, rule_action="replay", **rule)


@deployment_voa_command_group.command("apply", cls=GroupedOptionCommand)
@deployment_name_option(action="apply given voa config")
@pass_rib_mode
@nodes_option("apply VoA configuration on")
@click.option("--conf-file", "conf_file", help="Config File", required=True, type=str)
def apply_config(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
    conf_file: str,
):
    """
    Apply the specified VoA configuration on the give node.
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.apply_voa_config(
        nodes=nodes,
        voa_config_file=conf_file,
    )


@deployment_voa_command_group.command("delete")
@deployment_name_option(action="voa delete rules")
@pass_rib_mode
@nodes_option("delete VoA rule(s) on")
@voa_delete_options
def delete_rules(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
    rule_id_list: Optional[List[str]],
    all_rules: Optional[bool],
):
    """
    Delete rules
    """

    if all_rules:
        target_ids = []
    elif rule_id_list:
        target_ids = rule_id_list
    else:
        raise error_utils.RIB006("Unspecified rules to delete")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.delete_voa_rules(
        nodes=nodes,
        rule_id_list=target_ids,
    )


@deployment_voa_command_group.command("activate")
@deployment_name_option(action="voa activate")
@pass_rib_mode
@nodes_option("activate VoA state on")
def activate_voa(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
):
    """
    Activate VoA processing
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.voa_set_active_state(
        nodes=nodes,
        state=True,
    )


@deployment_voa_command_group.command("deactivate")
@deployment_name_option(action="voa deactivate")
@pass_rib_mode
@nodes_option("deactivate VoA state on")
def deactivate_voa(
    deployment_name: str,
    rib_mode: str,
    nodes: List[str],
):
    """
    Deactivate VoA processing (enqueued packages are
    still processed through Voa)
    """

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    deployment.voa_set_active_state(
        nodes=nodes,
        state=False,
    )
